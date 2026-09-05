"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useApiFetch } from "@/lib/api";
import { AnalysisStatus, isWorkflowJobId, pollWorkflow } from "@/lib/workflow-polling";
import { ArrowLeft, BriefcaseBusiness, Circle, FileText, Sparkles } from "lucide-react";

const stages = [
  "Reviewing your CV",
  "Processing your profile",
  "Comparing skills with your target role",
  "Calculating your readiness score",
  "Building your learning plan",
];

export default function AnalysisJobPage() {
  const { jobId } = useParams<{ jobId: string }>();
  return <AnalysisScreen key={jobId} jobId={jobId} />;
}

function AnalysisScreen({ jobId }: { jobId: string }) {
  const isValidJobId = isWorkflowJobId(jobId);
  const { isLoaded, isSignedIn } = useAuth();
  const apiFetch = useApiFetch();
  const router = useRouter();
  const [status, setStatus] = useState<AnalysisStatus>("loading");
  const [pollAttempt, setPollAttempt] = useState(0);
  const completed = useRef(false);

  useEffect(() => {
    if (!isValidJobId || !isLoaded || !isSignedIn || completed.current) return;
    return pollWorkflow(jobId, apiFetch, setStatus, (result) => {
      if (completed.current) return;
      completed.current = true;
      // Preserve the dashboard's existing session-storage data contract.
      try {
        if (result) sessionStorage.setItem("campuspath_workflow", JSON.stringify(result));
        else sessionStorage.removeItem("campuspath_workflow");
        for (const field of ["plan_id", "job_target_id"] as const) {
          if (result && typeof result[field] === "string") {
            sessionStorage.setItem(`campuspath_${field}`, result[field]);
          } else {
            sessionStorage.removeItem(`campuspath_${field}`);
          }
        }
      } catch {
        // The dashboard provides a readable empty/error state if storage is unavailable.
      }
      router.replace("/dashboard");
    });
  }, [jobId, isValidJobId, isLoaded, isSignedIn, apiFetch, router, pollAttempt]);

  const displayStatus = isLoaded && !isSignedIn ? "auth-error" : status;
  const messages: Record<AnalysisStatus, [string, string]> = {
    loading: ["Checking your analysis status", "Please wait while we check your analysis."],
    queued: ["Your analysis is queued", "CampusPath will begin processing shortly."],
    processing: ["Analyzing your career readiness", "CampusPath is reviewing your CV against your target role."],
    completed: ["Your analysis is complete", "Opening your dashboard..."],
    failed: ["Analysis couldn't be completed", "We weren't able to finish your career analysis. Return to onboarding to submit a new analysis."],
    "not-found": ["This analysis could not be found", "Return to onboarding to start an analysis."],
    "connection-error": ["We couldn't check your analysis status", "Your analysis may still be running. Check again to reconnect."],
    "auth-error": ["Please sign in to view your analysis", "Return to onboarding to continue with your account."],
  };
  const [heading, description] = isValidJobId ? messages[displayStatus] :
    ["Invalid analysis link", "This link does not contain a valid analysis ID. Return to onboarding to start an analysis."];
  const active = isValidJobId && (displayStatus === "queued" || displayStatus === "processing");

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-6 py-4 lg:px-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950">
            <BriefcaseBusiness aria-hidden="true" className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="font-semibold text-slate-950">CampusPath</p>
            <p className="text-xs text-slate-400">AI Career Readiness Agent</p>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-2xl px-6 py-10 sm:py-14">
        <section aria-labelledby="analysis-heading" className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50">
            {isValidJobId ? (
              <Sparkles aria-hidden="true" className="h-7 w-7 text-indigo-600" />
            ) : (
              <FileText aria-hidden="true" className="h-7 w-7 text-indigo-600" />
            )}
          </div>

          <div role="status" aria-live="polite" aria-atomic="true">
          <h1 id="analysis-heading" className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
            {heading}
          </h1>
          <p className="mt-4 text-sm leading-6 text-slate-600">{description}</p>
          </div>

          {active && (
            <>
              <p className="mt-4 text-sm leading-6 text-slate-500">
                You can leave this page and return later using this link.
              </p>

              <div className="mt-6 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-5">
                <h2 className="text-sm font-semibold text-slate-900">Analysis stages</h2>
                <p id="stages-help" className="mt-2 text-sm leading-6 text-slate-600">
                  These are the stages of your analysis. Individual stage progress is not available.
                </p>
                <ol aria-describedby="stages-help" className="mt-5 space-y-4">
                  {stages.map((stage) => (
                    <li key={stage} className="flex items-start gap-3 text-sm leading-6 text-slate-700">
                      <Circle aria-hidden="true" className="mt-1 h-4 w-4 shrink-0 text-indigo-500" />
                      <span>{stage}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </>
          )}

          {isValidJobId && displayStatus === "failed" && (
            <Link href="/onboarding" className="mt-8 mr-3 inline-flex min-h-12 items-center rounded-xl bg-slate-950 px-5 py-3 font-medium text-white focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-indigo-600">Try Again</Link>
          )}
          {isValidJobId && displayStatus === "connection-error" && (
            <button type="button" onClick={() => {
              setStatus("loading");
              setPollAttempt((attempt) => attempt + 1);
            }} className="mt-8 mr-3 inline-flex min-h-12 items-center rounded-xl bg-slate-950 px-5 py-3 font-medium text-white focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-indigo-600">Check Again</button>
          )}
          <Link href="/onboarding" className="mt-8 inline-flex min-h-12 items-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-indigo-600">
            <ArrowLeft aria-hidden="true" className="h-4 w-4 shrink-0" />
            Back to onboarding
          </Link>
        </section>
      </div>
    </main>
  );
}
