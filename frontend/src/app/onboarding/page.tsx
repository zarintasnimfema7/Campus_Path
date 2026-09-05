"use client";
import { useApiFetch } from "@/lib/api";
import { useAuth } from "@clerk/nextjs";


import {
  ChangeEvent,
  DragEvent,
  FormEvent,
  useEffect,
  useState,
  useRef,
} from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  FileText,
  Loader2,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useAuth();
  const apiFetch = useApiFetch();

  const [jobDescription, setJobDescription] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const submitting = useRef(false);
  const [cvFile, setCvFile] = useState<File | null>(null);

  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const [error, setError] = useState("");

  const canAnalyze = jobDescription.trim().length > 0 && cvFile !== null;

  // Protect page: user must be logged in
  useEffect(() => {
    function checkAuth() {
      if (!isLoaded) return;

      if (!isSignedIn) {
        router.replace("/login");
        return;
      }

      setCheckingAuth(false);
    }

    checkAuth();
  }, [isLoaded, isSignedIn, router]);

  function validateFile(file: File) {
    const types: Record<string, string> = {
      pdf: "application/pdf",
      doc: "application/msword",
      docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    };
    const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!Object.hasOwn(types, extension) || (file.type && file.type !== "application/octet-stream" && file.type !== types[extension])) {
      setError("Please choose a PDF, DOC, or DOCX file with a matching file type.");
      return false;
    }
    if (file.size === 0) {
      setError("This file is empty. Please choose your CV again.");
      return false;
    }

    const maxSize = 5 * 1024 * 1024;

    if (file.size > maxSize) {
      setError("CV must be 5 MB or smaller.");
      return false;
    }

    return true;
  }

  function selectFile(file: File) {
    if (submitting.current || jobId) return;
    setError("");

    if (validateFile(file)) {
      setCvFile(file);
    }
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];

    if (file) {
      selectFile(file);
    }
    // Allow selecting the same file again after a validation error.
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      selectFile(file);
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();
    if (submitting.current || jobId) return;

    if (!jobDescription.trim()) {
      setError("Please enter the target job description.");
      return;
    }

    if (!cvFile) {
      setError("Please upload your CV.");
      return;
    }

    submitting.current = true;
    setLoading(true);
    setError("");

    try {
      if (!isSignedIn) {
        router.replace("/login");
        return;
      }

      const formData = new FormData();

      /*
       * IMPORTANT:
       * These field names must match your FastAPI
       * /workflow/start endpoint.
       */
      formData.append("job_description", jobDescription.trim());
      if (targetRole.trim()) formData.append("target_role", targetRole.trim());
      formData.append("cv", cvFile);

      const response = await apiFetch("/workflow/start", {
        method: "POST",
        body: formData,
      });

      if (response.status !== 202) {
        setError(response.status === 400 || response.status === 413 || response.status === 422
          ? "Check your job description and choose a valid CV of 5 MB or smaller."
          : "We couldn't start your analysis. Please try again shortly.");
        return;
      }
      const result = await response.json();
      if (!result || result.status !== "queued" || typeof result.job_id !== "string" ||
          !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(result.job_id)) {
        setError("We couldn't confirm your analysis request. Please try again later.");
        return;
      }
      setJobId(result.job_id);
      // Keep the job available when returning to the analysis screen.
      try {
        sessionStorage.setItem("campuspath_workflow_job_id", result.job_id);
      } catch {
        // The accepted job remains in component state if browser storage is unavailable.
      }
      router.push(`/analysis/${result.job_id}`);
    } catch {
      setError("We couldn't connect to start your analysis. Check your connection and sign-in, then try again.");
    } finally {
      submitting.current = false;
      setLoading(false);
    }
  }

  if (checkingAuth) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="flex items-center gap-3 text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          Loading CampusPath...
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* HEADER */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950">
              <BriefcaseBusiness className="h-5 w-5 text-white" />
            </div>

            <div>
              <p className="font-semibold text-slate-950">
                CampusPath
              </p>

              <p className="text-xs text-slate-400">
                AI Career Readiness Agent
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium text-slate-500 sm:flex">
            <Sparkles className="h-4 w-4 text-indigo-500" />
            Powered by autonomous AI agents
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        {/* PROGRESS */}
        <div className="mx-auto mb-10 max-w-4xl">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm font-medium text-indigo-600">
              Career setup
            </span>

            <span className="text-sm text-slate-400">
              Step 1 of 1
            </span>
          </div>

          <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
            <div className="h-full w-full rounded-full bg-indigo-600" />
          </div>
        </div>

        {/* TITLE */}
        <div className="mx-auto mb-10 max-w-3xl text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50">
            <Sparkles className="h-7 w-7 text-indigo-600" />
          </div>

          <h1 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
            Build your personalized career path
          </h1>

          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-500">
            Tell CampusPath where you want to go and
            where you are today. Our agents will analyze
            the job, understand your CV, identify your
            gaps and create an actionable learning plan.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="mx-auto max-w-5xl"
        >
          <fieldset disabled={loading || jobId !== null} className="min-w-0">
          <legend className="sr-only">Analysis requirements</legend>
          <div className="grid gap-6 lg:grid-cols-2">
            {/* JOB DESCRIPTION */}
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <div className="mb-6 flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-50">
                  <BriefcaseBusiness className="h-5 w-5 text-indigo-600" />
                </div>

                <div>
                  <h2 className="text-lg font-semibold text-slate-950">
                    Target role
                  </h2>

                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Paste the job description for the
                    position you want to prepare for.
                  </p>
                </div>
              </div>

              <label htmlFor="target-role" className="mb-2 block text-sm font-medium text-slate-700">
                Target role (optional)
              </label>
              <input id="target-role" value={targetRole} onChange={(event) => setTargetRole(event.target.value)}
                placeholder="Junior Backend Developer" aria-describedby="target-role-help"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10" />
              <p id="target-role-help" className="mb-5 mt-2 text-xs text-slate-500">Leave blank to infer the role from the job description.</p>

              <label
                htmlFor="job-description"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Job description
              </label>

              <textarea
                id="job-description"
                required
                value={jobDescription}
                onChange={(event) =>
                  setJobDescription(event.target.value)
                }
                placeholder="Example: We are looking for a Junior Backend Developer with experience in Python, FastAPI, PostgreSQL, Docker and Git..."
                className="min-h-[270px] w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10"
              />

              <div className="mt-3 flex justify-between text-xs text-slate-400">
                <span>
                  Paste the complete description for
                  better analysis.
                </span>

                <span>
                  {jobDescription.length} characters
                </span>
              </div>
            </section>

            {/* CV */}
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <div className="mb-6 flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50">
                  <FileText className="h-5 w-5 text-emerald-600" />
                </div>

                <div>
                  <h2 className="text-lg font-semibold text-slate-950">
                    Your CV
                  </h2>

                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Upload your latest CV so CampusPath
                    can understand your current skills.
                  </p>
                </div>
              </div>

              {!cvFile ? (
                <div
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}
                  className={`relative focus-within:ring-4 focus-within:ring-indigo-500/20 flex min-h-[270px] flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition ${
                    dragging
                      ? "border-indigo-500 bg-indigo-50"
                      : "border-slate-200 bg-slate-50 hover:border-indigo-300 hover:bg-indigo-50/30"
                  }`}
                >
                  <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-sm">
                    <UploadCloud className="h-7 w-7 text-indigo-600" />
                  </div>

                  <p className="font-semibold text-slate-900">
                    Drop your CV here
                  </p>

                  <p className="mt-2 text-sm text-slate-500">
                    or click to browse your files
                  </p>

                  <p id="cv-help" className="mt-5 text-xs text-slate-500">
                    PDF, DOC, or DOCX • Maximum 5 MB
                  </p>

                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileChange}
                    aria-label="Choose your CV"
                    aria-describedby="cv-help"
                    className="absolute inset-0 cursor-pointer opacity-0"
                  />
                </div>
              ) : (
                <div className="flex min-h-[270px] flex-col items-center justify-center rounded-2xl border border-emerald-200 bg-emerald-50/50 p-8 text-center">
                  <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-sm">
                    <CheckCircle2 className="h-7 w-7 text-emerald-600" />
                  </div>

                  <p className="max-w-full break-all font-semibold text-slate-900">
                    {cvFile.name}
                  </p>
                  <p className="mt-2 text-sm font-medium text-emerald-700" role="status">&#10003; Ready</p>

                  <p className="mt-2 text-sm text-slate-500">
                    {(cvFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>

                  <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                    <label className="relative focus-within:ring-4 focus-within:ring-indigo-500/20 cursor-pointer rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
                      Replace
                      <input
                        type="file"
                        accept=".pdf,.doc,.docx"
                        onChange={handleFileChange}
                        aria-label="Change your CV"
                        className="absolute inset-0 cursor-pointer opacity-0"
                      />
                    </label>

                    <button
                      type="button"
                      onClick={() => {
                        setCvFile(null);
                        setError("");
                      }}
                      className="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium text-red-500 transition hover:bg-red-50"
                    >
                      <X className="h-4 w-4" />
                      Remove
                    </button>
                  </div>
                </div>
              )}
            </section>
          </div>

          {/* WHAT HAPPENS */}
          <div className="mt-6 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-5">
            <p className="mb-3 text-sm font-semibold text-slate-900">
              What happens next?
            </p>

            <div className="grid gap-3 text-sm text-slate-600 sm:grid-cols-2 lg:grid-cols-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-indigo-500" />
                Analyze target job
              </div>

              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-indigo-500" />
                Analyze your CV
              </div>

              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-indigo-500" />
                Calculate skill gaps
              </div>

              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-indigo-500" />
                Generate learning path
              </div>
            </div>
          </div>

          {error && (
            <div role="alert" className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-600">
              {error}
            </div>
          )}

          <ul aria-label="Required inputs" aria-live="polite" className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-600">
            <li>{jobDescription.trim() ? "\u2713 Job description added" : "\u25cb Job description required"}</li>
            <li>{cvFile ? "\u2713 CV uploaded" : "\u25cb CV required"}</li>
          </ul>
          {!canAnalyze && <p id="analysis-help" className="mt-2 text-sm text-slate-500">Add a job description and upload your CV to continue.</p>}
          {jobId && <div role="status" className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-800">Analysis started. Your request has been saved.</div>}
          {/* SUBMIT */}
          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              aria-busy={loading}
              aria-describedby={!canAnalyze ? "analysis-help" : undefined}
              disabled={
                loading || jobId !== null || !canAnalyze
              }
              className="flex h-12 min-w-52 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 font-medium text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Starting analysis...
                </>
              ) : (
                <>
                  {jobId ? "Analysis started" : "Analyze my readiness"}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
          </fieldset>
        </form>
      </div>

    </main>
  );
}
