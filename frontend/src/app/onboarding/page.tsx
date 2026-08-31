"use client";
import {apiFetch} from "@/lib/api";


import {
  ChangeEvent,
  DragEvent,
  FormEvent,
  useEffect,
  useState,
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

import { supabase } from "@/lib/supabase";



export default function OnboardingPage() {
  const router = useRouter();

  const [jobDescription, setJobDescription] = useState("");
  const [cvFile, setCvFile] = useState<File | null>(null);

  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const [error, setError] = useState("");

  // Protect page: user must be logged in
  useEffect(() => {
    async function checkAuth() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.replace("/login");
        return;
      }

      setCheckingAuth(false);
    }

    checkAuth();
  }, [router]);

  function validateFile(file: File) {
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowedTypes.includes(file.type)) {
      setError("Please upload a PDF or DOCX file.");
      return false;
    }

    const maxSize = 5 * 1024 * 1024;

    if (file.size > maxSize) {
      setError("CV must be smaller than 5 MB.");
      return false;
    }

    return true;
  }

  function selectFile(file: File) {
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

    if (!jobDescription.trim()) {
      setError("Please enter the target job description.");
      return;
    }

    if (!cvFile) {
      setError("Please upload your CV.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.user) {
        router.replace("/login");
        return;
      }

      const formData = new FormData();

      /*
       * IMPORTANT:
       * These field names must match your FastAPI
       * /workflow/start endpoint.
       */
      formData.append("job_description", jobDescription);
      formData.append("cv", cvFile);

      /*
       * Use the authenticated Supabase UUID.
       * Your backend workflow should use this as user_id.
       */
      

     const response = await apiFetch(
  "/workflow/start",
  {
    method: "POST",
    body: formData,
  }
);

      if (!response.ok) {
        let message = "Career analysis failed.";

        try {
          const result = await response.json();

          if (result.detail) {
            message =
              typeof result.detail === "string"
                ? result.detail
                : JSON.stringify(result.detail);
          }
        } catch {
          // Keep default error message
        }

        throw new Error(message);
      }

      const result = await response.json();

      /*
       * Temporary frontend state.
       * Later we can load this directly from Supabase.
       */
      sessionStorage.setItem(
        "campuspath_workflow",
        JSON.stringify(result)
      );

      if (result.plan_id) {
        sessionStorage.setItem(
          "campuspath_plan_id",
          result.plan_id
        );
      }

      if (result.job_target_id) {
        sessionStorage.setItem(
          "campuspath_job_target_id",
          result.job_target_id
        );
      }

      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
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
                  className={`relative flex min-h-[270px] flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition ${
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

                  <p className="mt-5 text-xs text-slate-400">
                    PDF or DOCX • Maximum 5 MB
                  </p>

                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFileChange}
                    className="absolute inset-0 cursor-pointer opacity-0"
                  />
                </div>
              ) : (
                <div className="flex min-h-[270px] flex-col items-center justify-center rounded-2xl border border-emerald-200 bg-emerald-50/50 p-8 text-center">
                  <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-sm">
                    <CheckCircle2 className="h-7 w-7 text-emerald-600" />
                  </div>

                  <p className="max-w-full truncate font-semibold text-slate-900">
                    {cvFile.name}
                  </p>

                  <p className="mt-2 text-sm text-slate-500">
                    {(cvFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>

                  <div className="mt-6 flex items-center gap-3">
                    <label className="cursor-pointer rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
                      Replace
                      <input
                        type="file"
                        accept=".pdf,.docx"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                    </label>

                    <button
                      type="button"
                      onClick={() => setCvFile(null)}
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
            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* SUBMIT */}
          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              disabled={
                loading ||
                !cvFile ||
                !jobDescription.trim()
              }
              className="flex h-12 min-w-52 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 font-medium text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Building your path...
                </>
              ) : (
                <>
                  Analyze my readiness
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* FULL SCREEN AI LOADING */}
      {loading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-6 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl bg-white p-8 text-center shadow-2xl">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50">
              <Sparkles className="h-8 w-8 animate-pulse text-indigo-600" />
            </div>

            <h3 className="mt-6 text-xl font-semibold text-slate-950">
              Building your career path
            </h3>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              CampusPath agents are analyzing your job,
              CV, skills and learning priorities.
            </p>

            <div className="mt-7 flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
            </div>

            <p className="mt-4 text-xs text-slate-400">
              This may take a little while.
            </p>
          </div>
        </div>
      )}
    </main>
  );
}