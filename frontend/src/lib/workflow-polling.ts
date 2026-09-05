export const POLL_INTERVAL_MS = 3000;
const MAX_REQUEST_FAILURES = 3;

export type AnalysisStatus = "loading" | "queued" | "processing" | "completed" | "failed" |
  "not-found" | "connection-error" | "auth-error";
type ApiFetch = (path: string, init?: RequestInit) => Promise<Response>;

export function isWorkflowJobId(value: unknown): value is string {
  return typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}

// Schedule only after a request settles, so slow responses cannot pile up.
export function pollWorkflow(
  jobId: string,
  apiFetch: ApiFetch,
  onStatus: (status: AnalysisStatus) => void,
  onCompleted: (result: Record<string, unknown> | null) => void,
) {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let stopped = false;
  let failures = 0;

  async function poll() {
    try {
      const response = await apiFetch(`/workflow/${jobId}`, {
        method: "GET", signal: controller.signal, cache: "no-store",
      });
      if (stopped) return;
      if (response.status === 404 || response.status === 401 || response.status === 403) {
        stopped = true;
        onStatus(response.status === 404 ? "not-found" : "auth-error");
        return;
      }
      if (!response.ok) throw new Error("Status request unsuccessful");
      const data = await response.json();
      if (stopped) return;
      if (!data || typeof data.job_id !== "string" || data.job_id.toLowerCase() !== jobId.toLowerCase() ||
          !["queued", "processing", "completed", "failed"].includes(data.status)) {
        throw new Error("Invalid status response");
      }
      failures = 0;
      if (data.status === "completed" || data.status === "failed") {
        stopped = true;
        onStatus(data.status);
        if (data.status === "completed") {
          onCompleted(data.result && typeof data.result === "object" && !Array.isArray(data.result)
            ? data.result : null);
        }
        return;
      }
      onStatus(data.status);
    } catch {
      if (stopped || controller.signal.aborted) return;
      failures += 1;
      if (failures >= MAX_REQUEST_FAILURES) {
        stopped = true;
        onStatus("connection-error");
        return;
      }
    }
    if (!stopped) timer = setTimeout(poll, POLL_INTERVAL_MS);
  }

  if (isWorkflowJobId(jobId)) void poll();
  return () => {
    stopped = true;
    clearTimeout(timer);
    controller.abort();
  };
}
