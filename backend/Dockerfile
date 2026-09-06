FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

WORKDIR /app

# Cache dependency installation independently of application changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip check

RUN groupadd --gid 10001 campuspath \
    && useradd --uid 10001 --gid campuspath --create-home --shell /usr/sbin/nologin campuspath

# Explicit copies keep local environment files and tooling out of the image.
COPY app/ ./app/
COPY entrypoint.sh /usr/local/bin/campuspath-entrypoint
RUN chmod 0555 /usr/local/bin/campuspath-entrypoint

USER campuspath:campuspath
EXPOSE 8080
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/local/bin/campuspath-entrypoint"]
