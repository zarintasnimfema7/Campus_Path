"""Bounded health-only HTTP measurements. No workflow submission or automatic retries."""
import argparse
import asyncio
import ipaddress
import json
import math
import os
import statistics
import time
from urllib.parse import urlsplit

import httpx


def bounded_int(value, maximum):
    number = int(value)
    if not 1 <= number <= maximum:
        raise ValueError(f'Value must be between 1 and {maximum}.')
    return number


def health_url(base_url, allow_remote=False):
    if not base_url:
        raise ValueError('BASE_URL or --base-url is required; there is no default target.')
    try:
        url = urlsplit(base_url)
        port = url.port
    except ValueError:
        raise ValueError('Invalid BASE_URL.') from None
    if (url.scheme not in {'http', 'https'} or not url.hostname or url.username or
            url.password or url.query or url.fragment or url.path not in {'', '/'} or port == 0):
        raise ValueError('BASE_URL must be an HTTP(S) origin without credentials, path, query or fragment.')
    local = url.hostname == 'localhost'
    try:
        local = local or ipaddress.ip_address(url.hostname).is_loopback
    except ValueError:
        pass
    if not local:
        if not allow_remote:
            raise ValueError('Every non-loopback target requires --allow-remote. Confirm it is an approved staging target.')
        if url.scheme != 'https':
            raise ValueError('Remote targets must use HTTPS.')
    return base_url.rstrip('/') + '/health'


def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else 0.0


async def measure(url, concurrency, request_count, auth_token=None, *, transport=None):
    concurrency = bounded_int(concurrency, 100)
    request_count = bounded_int(request_count, 100000)
    # Tokens are never printed; no redirects or environment proxies can forward them.
    headers = {'Authorization': f'Bearer {auth_token}'} if auth_token else {}
    latencies, statuses = [], {}
    work = iter(range(request_count))
    successes = 0
    async with httpx.AsyncClient(
        headers=headers, timeout=10.0, follow_redirects=False, trust_env=False,
        limits=httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency),
        transport=transport,
    ) as client:
        async def worker():
            nonlocal successes
            for _ in work:
                started = time.perf_counter()
                try:
                    # Avoid retaining an unexpected response body from the target.
                    async with client.stream('GET', url) as response:
                        code = str(response.status_code)
                        successes += int(200 <= response.status_code < 300)
                except httpx.HTTPError:
                    code = 'network_error'
                latencies.append((time.perf_counter() - started) * 1000)
                statuses[code] = statuses.get(code, 0) + 1

        started = time.perf_counter()
        await asyncio.gather(*(worker() for _ in range(min(concurrency, request_count))))
        elapsed = time.perf_counter() - started
    return {
        'total_requests': len(latencies), 'successes': successes,
        'failures': len(latencies) - successes,
        'requests_per_second': round(len(latencies) / elapsed, 2) if elapsed else 0.0,
        'average_latency_ms': round(statistics.mean(latencies), 2),
        'p50_ms': round(percentile(latencies, .50), 2),
        'p95_ms': round(percentile(latencies, .95), 2),
        'p99_ms': round(percentile(latencies, .99), 2),
        'status_counts': statuses,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default=os.getenv('BASE_URL'))
    parser.add_argument('--concurrency', default=os.getenv('CONCURRENCY', '4'))
    parser.add_argument('--request-count', default=os.getenv('REQUEST_COUNT', '20'))
    parser.add_argument('--allow-remote', action='store_true', help='Explicitly confirm an approved remote/staging target.')
    args = parser.parse_args(argv)
    try:
        url = health_url(args.base_url, args.allow_remote)
        concurrency = bounded_int(args.concurrency, 100)
        count = bounded_int(args.request_count, 100000)
    except (ValueError, TypeError) as error:
        parser.error(str(error))
    try:
        result = asyncio.run(measure(url, concurrency, count, os.getenv('AUTH_TOKEN')))
    except KeyboardInterrupt:
        print('Measurement interrupted.')
        return 130
    print(json.dumps(result, indent=2))
    return 1 if result['failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
