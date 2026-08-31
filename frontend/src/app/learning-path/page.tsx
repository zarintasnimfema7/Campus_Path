"use client";

import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Circle,
  Clock3,
  GraduationCap,
  LayoutDashboard,
  Lock,
  LogOut,
  Menu,
  Route,
  Sparkles,
  Target,
  User,
  X,
  Zap,
} from "lucide-react";
import {FaGithub } from "react-icons/fa";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { supabase } from "@/lib/supabase";

type LearningTask = {
  title?: string;
  skill?: string;
  description?: string;
  status?: string;
  estimated_time?: string;
  learning_goal?: string;
  deliverable?: string;
};

type WorkflowData = {
  job?: {
    job_title?: string;
  };

  skill_gap?: {
    readiness_score?: number;
    missing_skills?: string[];
    partial_skills?: string[];
  };

  plan?: {
    plan_title?: string;
    summary?: string;
    tasks?: LearningTask[];
  };
};

export default function LearningPathPage() {
  const router = useRouter();

  const [workflow, setWorkflow] =
    useState<WorkflowData | null>(null);

  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    async function loadPage() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.replace("/register");
        return;
      }

      const saved =
        sessionStorage.getItem("campuspath_workflow");

      if (!saved) {
        router.replace("/onboarding");
        return;
      }

      try {
        setWorkflow(JSON.parse(saved));
      } catch {
        router.replace("/onboarding");
        return;
      }

      setLoading(false);
    }

    loadPage();
  }, [router]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    sessionStorage.clear();
    router.replace("/register");
  };

  if (loading || !workflow) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F6FA]">
        <div className="text-center">
          <div className="mx-auto h-11 w-11 animate-spin rounded-full border-4 border-slate-200 border-t-violet-600" />

          <p className="mt-4 text-sm font-medium text-slate-500">
            Building your learning path...
          </p>
        </div>
      </div>
    );
  }

  const tasks = workflow.plan?.tasks ?? [];

  const readiness = Math.round(
    workflow.skill_gap?.readiness_score ?? 0
  );

  const role =
    workflow.job?.job_title ?? "Target role";

  const completedTasks = tasks.filter(
    (task) =>
      task.status?.toLowerCase() === "completed"
  ).length;

  return (
    <div className="min-h-screen bg-[#F4F6FA] text-[#111827]">
      {/* MOBILE HEADER */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur lg:hidden">
        <Logo />

        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-xl p-2 transition hover:bg-slate-100"
        >
          <Menu className="h-6 w-6" />
        </button>
      </header>

      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-[#07111F]/50 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* SIDEBAR */}
      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-[280px] flex-col border-r border-white/5 bg-[#07111F] text-white transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >
        <div className="flex h-20 items-center justify-between px-6">
          <Logo dark />

          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-2 text-slate-400 hover:bg-white/10 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mx-5 mb-6 rounded-2xl border border-violet-400/10 bg-gradient-to-br from-violet-500/15 to-cyan-400/5 p-4">
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-violet-300">
            Target role
          </p>

          <p className="mt-2 text-sm font-semibold text-white">
            {role}
          </p>

          <div className="mt-4 flex items-center gap-2">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-400"
                style={{
                  width: `${Math.min(readiness, 100)}%`,
                }}
              />
            </div>

            <span className="text-xs font-bold text-cyan-300">
              {readiness}%
            </span>
          </div>
        </div>

    <nav className="flex-1 space-y-1 px-4">
  <NavButton
    icon={<LayoutDashboard />}
    label="Dashboard"
    onClick={() => {
      setSidebarOpen(false);
      router.push("/dashboard");
    }}
  />

  <NavButton
    icon={<Target />}
    label="Skill Gap"
    onClick={() => {
      setSidebarOpen(false);
      router.push("/skill-gap");
    }}
  />

  <NavButton
    icon={<Route />}
    label="Learning Path"
    active
    onClick={() => {
      setSidebarOpen(false);
      router.push("/learning-path");
    }}
  />

  <NavButton
    icon={<FaGithub />}
    label="Evidence"
    onClick={() => {
      setSidebarOpen(false);
      router.push("/evidence");
    }}
  />

  <NavButton
    icon={<User />}
    label="Profile"
    onClick={() => {
      setSidebarOpen(false);
      router.push("/profile");
    }}
  />
</nav>

        <div className="border-t border-white/10 p-4">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-400 transition hover:bg-white/5 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* PAGE */}
      <main className="lg:ml-[280px]">
        <div className="mx-auto max-w-[1400px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
          {/* BACK */}
          <button
            onClick={() => router.push("/dashboard")}
            className="mb-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition hover:text-slate-950"
          >
            <ArrowLeft className="h-4 w-4" />
            Dashboard
          </button>

          {/* HERO */}
          <section className="relative overflow-hidden rounded-[32px] bg-[#0A1426] px-7 py-8 text-white shadow-xl shadow-slate-900/5 sm:px-10 sm:py-10">
            <div className="absolute -right-20 -top-28 h-72 w-72 rounded-full bg-violet-500/20 blur-3xl" />
            <div className="absolute -bottom-28 right-52 h-64 w-64 rounded-full bg-cyan-400/10 blur-3xl" />

            <div className="relative grid gap-10 xl:grid-cols-[1fr_360px] xl:items-end">
              <div className="max-w-3xl">
                <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.16em] text-violet-200">
                  <Sparkles className="h-3.5 w-3.5" />
                  AI generated roadmap
                </div>

                <h1 className="text-3xl font-bold tracking-tight sm:text-5xl">
                  {workflow.plan?.plan_title ||
                    "Your personalized learning path"}
                </h1>

                <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
                  {workflow.plan?.summary ||
                    "Complete these focused tasks to close your most important skill gaps."}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <HeroMetric
                  value={`${tasks.length}`}
                  label="Tasks"
                />

                <HeroMetric
                  value={`${completedTasks}`}
                  label="Done"
                />

                <HeroMetric
                  value={`${readiness}%`}
                  label="Ready"
                  accent
                />
              </div>
            </div>
          </section>

          {/* ROADMAP HEADER */}
          <div className="mb-6 mt-10 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-600">
                Your roadmap
              </p>

              <h2 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
                Build skills. Prove them. Progress.
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Each task creates evidence that CampusPath can
                verify.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-500 shadow-sm">
              {completedTasks} of {tasks.length} completed
            </div>
          </div>

          {/* ROADMAP */}
          {tasks.length === 0 ? (
            <section className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center">
              <BookOpen className="mx-auto h-9 w-9 text-slate-300" />

              <h3 className="mt-4 text-lg font-bold">
                No learning tasks yet
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                Run a new career analysis to generate your
                learning roadmap.
              </p>
            </section>
          ) : (
            <div className="relative">
              {/* timeline */}
              <div className="absolute bottom-12 left-[25px] top-12 hidden w-px bg-gradient-to-b from-violet-300 via-cyan-300 to-slate-200 sm:block" />

              <div className="space-y-5">
                {tasks.map((task, index) => (
                  <RoadmapTask
                    key={index}
                    task={task}
                    index={index}
                    total={tasks.length}
                    onEvidence={() =>
                      router.push("/evidence")
                    }
                  />
                ))}
              </div>
            </div>
          )}

          {/* NEXT ACTION */}
          {tasks.length > 0 && (
            <section className="mt-8 overflow-hidden rounded-[28px] border border-violet-100 bg-gradient-to-r from-[#F1EDFF] via-white to-[#EAFBFA] p-6 sm:p-8">
              <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
                <div className="flex gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#07111F] text-cyan-300 shadow-lg">
                    <Zap className="h-5 w-5" />
                  </div>

                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.17em] text-violet-600">
                      Agent loop
                    </p>

                    <h3 className="mt-1 text-xl font-bold">
                      Finished a task?
                    </h3>

                    <p className="mt-1 max-w-xl text-sm leading-6 text-slate-500">
                      Submit your GitHub repository. CampusPath
                      will inspect the evidence, update your
                      readiness score, and replan what remains.
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => router.push("/evidence")}
                  className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[#07111F] px-5 py-3.5 text-sm font-bold text-white shadow-lg shadow-slate-900/10 transition hover:-translate-y-0.5 hover:bg-[#101E35]"
                >
                  Verify my work
                  <ArrowRight className="h-4 w-4 text-cyan-300" />
                </button>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

function RoadmapTask({
  task,
  index,
  total,
  onEvidence,
}: {
  task: LearningTask;
  index: number;
  total: number;
  onEvidence: () => void;
}) {
  const completed =
    task.status?.toLowerCase() === "completed";

  return (
    <article className="relative sm:pl-[76px]">
      <div
        className={`absolute left-0 top-8 z-10 hidden h-[52px] w-[52px] items-center justify-center rounded-2xl border-4 border-[#F4F6FA] text-sm font-bold shadow-sm sm:flex ${
          completed
            ? "bg-emerald-500 text-white"
            : index === 0
              ? "bg-violet-600 text-white"
              : "bg-white text-slate-400"
        }`}
      >
        {completed ? (
          <CheckCircle2 className="h-5 w-5" />
        ) : (
          index + 1
        )}
      </div>

      <div
        className={`group rounded-[26px] border bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-slate-900/5 sm:p-7 ${
          index === 0 && !completed
            ? "border-violet-200"
            : "border-slate-200"
        }`}
      >
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-start">
          <div className="max-w-3xl">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-[#07111F] px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-cyan-300">
                Step {index + 1}/{total}
              </span>

              {task.skill && (
                <span className="rounded-full bg-violet-50 px-3 py-1 text-[11px] font-bold text-violet-700">
                  {task.skill}
                </span>
              )}

              {completed && (
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-bold text-emerald-700">
                  Completed
                </span>
              )}
            </div>

            <h3 className="text-xl font-bold tracking-tight text-slate-950 sm:text-2xl">
              {task.title ||
                task.skill ||
                `Learning task ${index + 1}`}
            </h3>

            {task.description && (
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-500">
                {task.description}
              </p>
            )}

            <div className="mt-5 flex flex-wrap gap-3">
              {task.estimated_time && (
                <SmallInfo
                  icon={<Clock3 />}
                  text={task.estimated_time}
                />
              )}

              <SmallInfo
                icon={<GraduationCap />}
                text="Hands-on learning"
              />

              <SmallInfo
                icon={
                  completed ? (
                    <CheckCircle2 />
                  ) : (
                    <Circle />
                  )
                }
                text={
                  completed
                    ? "Evidence verified"
                    : "Evidence required"
                }
              />
            </div>

            {(task.learning_goal ||
              task.deliverable) && (
              <div className="mt-5 grid gap-3 md:grid-cols-2">
                {task.learning_goal && (
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Learning goal
                    </p>

                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {task.learning_goal}
                    </p>
                  </div>
                )}

                {task.deliverable && (
                  <div className="rounded-2xl bg-cyan-50/60 p-4">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-cyan-700">
                      Evidence to build
                    </p>

                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {task.deliverable}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          <button
            onClick={onEvidence}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700"
          >
            <FaGithub className="h-4 w-4" />

            {completed
              ? "View evidence"
              : "Submit evidence"}

            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </article>
  );
}

function SmallInfo({
  icon,
  text,
}: {
  icon: React.ReactNode;
  text: string;
}) {
  return (
    <div className="inline-flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500">
      <span className="[&>svg]:h-3.5 [&>svg]:w-3.5">
        {icon}
      </span>

      {text}
    </div>
  );
}

function HeroMetric({
  value,
  label,
  accent = false,
}: {
  value: string;
  label: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-4 ${
        accent
          ? "border-cyan-300/20 bg-cyan-300/10"
          : "border-white/10 bg-white/5"
      }`}
    >
      <p
        className={`text-2xl font-bold ${
          accent ? "text-cyan-300" : "text-white"
        }`}
      >
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-400">
        {label}
      </p>
    </div>
  );
}

function NavButton({
  icon,
  label,
  active = false,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${
        active
          ? "bg-violet-500/15 text-white"
          : "text-slate-400 hover:bg-white/5 hover:text-white"
      }`}
    >
      <span
        className={`[&>svg]:h-[18px] [&>svg]:w-[18px] ${
          active ? "text-cyan-300" : ""
        }`}
      >
        {icon}
      </span>

      {label}

      {active && (
        <span className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-300" />
      )}
    </button>
  );
}

function Logo({
  dark = false,
}: {
  dark?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-900/20">
        <Route className="h-5 w-5" />

        <div className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-tl-lg bg-cyan-300" />
      </div>

      <span
        className={`text-xl font-bold tracking-tight ${
          dark ? "text-white" : "text-[#07111F]"
        }`}
      >
        CampusPath
      </span>
    </div>
  );
}