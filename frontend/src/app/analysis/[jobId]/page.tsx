import Link from "next/link";
import { ArrowLeft, BriefcaseBusiness, Circle, FileText, Sparkles } from "lucide-react";

const stages = [
  "Reviewing your CV",
  "Processing your profile",
  "Comparing skills with your target role",
  "Calculating your readiness score",
  "Building your learning plan",
];

export default async function AnalysisJobPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  const isValidJobId = typeof jobId === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(jobId);

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

          <h1 id="analysis-heading" className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
            {isValidJobId ? "Analyzing your career readiness" : "Invalid analysis link"}
          </h1>

          {isValidJobId ? (
            <>
              <p className="mt-4 text-sm leading-6 text-slate-500">
                CampusPath analyzes your CV against your target role to build a personalized learning plan.
                You can leave this page and return later using this link.
              </p>

              <div className="mt-6 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-5">
                <h2 className="text-sm font-semibold text-slate-900">Analysis stages</h2>
                <p id="stages-help" className="mt-2 text-sm leading-6 text-slate-600">
                  This is an overview of the analysis. Live progress is not shown yet.
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
          ) : (
            <p className="mt-4 text-sm leading-6 text-slate-600">
              This link does not contain a valid analysis ID. Return to onboarding to start an analysis.
            </p>
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
