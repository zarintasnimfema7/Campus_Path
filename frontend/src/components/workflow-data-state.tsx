import Link from "next/link";

export function WorkflowDataState({ title, error = false }: { title: string; error?: boolean }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-950">{title}</h1>
        <p role={error ? "alert" : "status"} className="mt-3 text-sm leading-6 text-slate-600">
          {error ? "We couldn't read your saved analysis. Refresh the page or start a new analysis." : "Complete your first analysis to see your career readiness and learning plan."}
        </p>
        <nav aria-label="Next actions" className="mt-6 flex flex-wrap gap-4 text-sm font-medium text-indigo-700">
          <Link href="/onboarding" className="underline">Back to onboarding</Link>
          <Link href="/profile" className="underline">View profile</Link>
        </nav>
      </section>
    </main>
  );
}
