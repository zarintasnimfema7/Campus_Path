"use client";

import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Circle,
  Clock3,
  LogOut,
  Menu,
  Target,
  TrendingUp,
  User,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth, useClerk } from "@clerk/nextjs";

type LearningTask = {
  title?: string;
  skill?: string;
  description?: string;
  status?: string;
  estimated_time?: string;
};

type WorkflowData = {
  student?: {
    name?: string;
  };

  job?: {
    job_title?: string;
  };

  skill_gap?: {
    readiness_score?: number;
    required_score?: number;
    preferred_score?: number;
    matched_skills?: string[];
    partial_skills?: string[];
    missing_skills?: string[];
  };

  plan?: {
    plan_title?: string;
    summary?: string;
    tasks?: LearningTask[];
  };
};

export default function DashboardPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useAuth();
  const { signOut } = useClerk();

  const [data, setData] = useState<WorkflowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const loadDashboard = () => {
      if (!isLoaded) return;

      if (!isSignedIn) {
        router.replace("/register");
        return;
      }

      const savedWorkflow =
        sessionStorage.getItem("campuspath_workflow");

      if (!savedWorkflow) {
        router.replace("/onboarding");
        return;
      }

      try {
        setData(JSON.parse(savedWorkflow));
      } catch {
        router.replace("/onboarding");
        return;
      }

      setLoading(false);
    };

    loadDashboard();
  }, [isLoaded, isSignedIn, router]);

  const logout = async () => {
    await signOut();

    sessionStorage.clear();

    router.replace("/register");
  };

  if (loading || !data) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-indigo-600" />

          <p className="mt-4 text-sm text-slate-500">
            Loading your career dashboard...
          </p>
        </div>
      </main>
    );
  }

  const readiness = Math.round(
    data.skill_gap?.readiness_score ?? 0
  );

  const matched = data.skill_gap?.matched_skills ?? [];
  const partial = data.skill_gap?.partial_skills ?? [];
  const missing = data.skill_gap?.missing_skills ?? [];
  const tasks = data.plan?.tasks ?? [];

  const name =
    data.student?.name ||
    sessionStorage.getItem("campuspath_name") ||
    "Student";

  const jobTitle =
    data.job?.job_title || "Your target role";

  return (
    <div className="min-h-screen bg-[#F6F8FC] text-slate-900">
      {/* MOBILE HEADER */}
      <header className="flex h-16 items-center justify-between border-b bg-white px-5 lg:hidden">
        <Logo />

        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-xl p-2 hover:bg-slate-100"
        >
          <Menu className="h-6 w-6" />
        </button>
      </header>

      {/* MOBILE OVERLAY */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* SIDEBAR */}
      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r bg-white transition-transform lg:translate-x-0 ${
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >
        <div className="flex h-20 items-center justify-between px-7">
          <Logo />

          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-2 px-4 py-6">
          <NavItem
            icon={<TrendingUp />}
            label="Dashboard"
            active
          />

          <NavItem
            icon={<Target />}
            label="Skill Gap"
              onClick={() => router.push("/skill-gap")}
          />

          <NavItem
            icon={<BookOpen />}
            label="Learning Path"
                onClick={() => router.push("/learning-path")}
          />

          <NavItem
            icon={<CheckCircle2 />}
            label="Evidence"
            onClick={() => router.push("/evidence")}
          />

          <NavItem
            icon={<User />}
            label="Profile"
            onClick={() => router.push("/profile")}
          />
        </nav>

        <div className="border-t p-4">
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
          >
            <LogOut className="h-5 w-5" />
            Sign out
          </button>
        </div>
      </aside>

      {/* CONTENT */}
      <main className="lg:ml-72">
        <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
          {/* TOP */}
          <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
            <div>
              <p className="mb-2 text-sm font-semibold text-indigo-600">
                CAREER READINESS
              </p>

              <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Welcome, {name}
              </h1>

              <p className="mt-2 text-slate-500">
                Target role:{" "}
                <span className="font-semibold text-slate-700">
                  {jobTitle}
                </span>
              </p>
            </div>

            <button
              onClick={() => router.push("/onboarding")}
              className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold shadow-sm transition hover:bg-slate-50"
            >
              Analyze another job
            </button>
          </div>

          {/* TOP CARDS */}
          <div className="grid gap-6 xl:grid-cols-[1.25fr_1fr]">
            {/* READINESS */}
            <section className="overflow-hidden rounded-3xl bg-[#071126] p-7 text-white shadow-sm sm:p-9">
              <div className="flex flex-col justify-between gap-8 sm:flex-row sm:items-center">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wider text-indigo-300">
                    Overall readiness
                  </p>

                  <div className="mt-4 flex items-end gap-2">
                    <span className="text-6xl font-bold">
                      {readiness}
                    </span>

                    <span className="mb-2 text-2xl text-slate-400">
                      %
                    </span>
                  </div>

                  <p className="mt-4 max-w-md leading-7 text-slate-300">
                    Complete your learning tasks and verify
                    your work to increase your readiness.
                  </p>
                </div>

                <div
                  className="relative flex h-40 w-40 shrink-0 items-center justify-center rounded-full"
                  style={{
                    background: `conic-gradient(
                      #6366f1 ${readiness * 3.6}deg,
                      #1e293b 0deg
                    )`,
                  }}
                >
                  <div className="flex h-28 w-28 items-center justify-center rounded-full bg-[#071126]">
                    <TrendingUp className="h-9 w-9 text-indigo-400" />
                  </div>
                </div>
              </div>

              <div className="mt-9 grid grid-cols-2 gap-4">
                <ScoreCard
                  label="Required skills"
                  value={
                    data.skill_gap?.required_score ?? 0
                  }
                />

                <ScoreCard
                  label="Preferred skills"
                  value={
                    data.skill_gap?.preferred_score ?? 0
                  }
                />
              </div>
            </section>

            {/* PLAN */}
            <section className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm sm:p-8">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                <BookOpen className="h-6 w-6" />
              </div>

              <p className="text-sm font-semibold text-indigo-600">
                YOUR LEARNING PLAN
              </p>

              <h2 className="mt-2 text-2xl font-bold">
                {data.plan?.plan_title ||
                  "Personalized learning path"}
              </h2>

              <p className="mt-3 line-clamp-3 leading-7 text-slate-500">
                {data.plan?.summary ||
                  "Complete your personalized tasks to close your skill gaps."}
              </p>

              <div className="mt-7 flex items-center justify-between border-t pt-5">
                <div>
                  <p className="text-2xl font-bold">
                    {tasks.length}
                  </p>

                  <p className="text-sm text-slate-500">
                    learning tasks
                  </p>
                </div>

                <button
                  onClick={() =>
                    router.push("/learning-path")
                  }
                  className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
                >
                  View plan
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </section>
          </div>

          {/* SKILLS */}
          <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="mb-7">
              <h2 className="text-2xl font-bold">
                Skill gap overview
              </h2>

              <p className="mt-1 text-slate-500">
                How your current skills compare with the
                target role.
              </p>
            </div>

            <div className="grid gap-5 md:grid-cols-3">
              <SkillCard
                title="Matched"
                count={matched.length}
                skills={matched}
                type="matched"
              />

              <SkillCard
                title="Partial"
                count={partial.length}
                skills={partial}
                type="partial"
              />

              <SkillCard
                title="Missing"
                count={missing.length}
                skills={missing}
                type="missing"
              />
            </div>
          </section>

          {/* TASKS */}
          <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">
                  Next learning tasks
                </h2>

                <p className="mt-1 text-slate-500">
                  Start closing your highest-priority skill
                  gaps.
                </p>
              </div>
            </div>

            {tasks.length === 0 ? (
              <p className="rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">
                No learning tasks were generated.
              </p>
            ) : (
              <div className="space-y-3">
                {tasks.slice(0, 4).map((task, index) => (
                  <div
                    key={index}
                    className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 p-5 transition hover:border-indigo-200 hover:bg-indigo-50/30 sm:flex-row sm:items-center"
                  >
                    <div className="flex gap-4">
                      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 font-semibold text-slate-600">
                        {index + 1}
                      </div>

                      <div>
                        <h3 className="font-semibold">
                          {task.title ||
                            task.skill ||
                            `Learning task ${index + 1}`}
                        </h3>

                        {task.description && (
                          <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-500">
                            {task.description}
                          </p>
                        )}

                        <div className="mt-2 flex items-center gap-4 text-xs text-slate-400">
                          {task.skill && (
                            <span>{task.skill}</span>
                          )}

                          {task.estimated_time && (
                            <span className="flex items-center gap-1">
                              <Clock3 className="h-3.5 w-3.5" />
                              {task.estimated_time}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() =>
                        router.push("/learning-path")
                      }
                      className="flex shrink-0 items-center gap-2 text-sm font-semibold text-indigo-600"
                    >
                      Open
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

function Logo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
        <Target className="h-5 w-5" />
      </div>

      <span className="text-xl font-bold">
        CampusPath
      </span>
    </div>
  );
}

function NavItem({
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
          ? "bg-indigo-50 text-indigo-700"
          : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
      }`}
    >
      <span className="[&>svg]:h-5 [&>svg]:w-5">
        {icon}
      </span>

      {label}
    </button>
  );
}

function ScoreCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-2xl bg-white/10 p-4">
      <p className="text-sm text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-2xl font-bold">
        {Math.round(value)}%
      </p>
    </div>
  );
}

function SkillCard({
  title,
  count,
  skills,
  type,
}: {
  title: string;
  count: number;
  skills: string[];
  type: "matched" | "partial" | "missing";
}) {
  const styles = {
    matched: {
      container:
        "border-emerald-100 bg-emerald-50/50",
      icon: "bg-emerald-100 text-emerald-600",
      badge: "bg-emerald-100 text-emerald-700",
    },

    partial: {
      container: "border-amber-100 bg-amber-50/50",
      icon: "bg-amber-100 text-amber-600",
      badge: "bg-amber-100 text-amber-700",
    },

    missing: {
      container: "border-red-100 bg-red-50/50",
      icon: "bg-red-100 text-red-600",
      badge: "bg-red-100 text-red-700",
    },
  };

  const style = styles[type];

  return (
    <div
      className={`rounded-2xl border p-5 ${style.container}`}
    >
      <div className="flex items-center justify-between">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl ${style.icon}`}
        >
          {type === "matched" ? (
            <CheckCircle2 className="h-5 w-5" />
          ) : (
            <Circle className="h-5 w-5" />
          )}
        </div>

        <span
          className={`rounded-full px-3 py-1 text-xs font-bold ${style.badge}`}
        >
          {count}
        </span>
      </div>

      <h3 className="mt-4 font-bold">
        {title} skills
      </h3>

      <div className="mt-4 flex flex-wrap gap-2">
        {skills.length === 0 ? (
          <span className="text-sm text-slate-400">
            None
          </span>
        ) : (
          skills.slice(0, 6).map((skill) => (
            <span
              key={skill}
              className="rounded-lg bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 shadow-sm"
            >
              {skill}
            </span>
          ))
        )}

        {skills.length > 6 && (
          <span className="px-2 py-1.5 text-xs text-slate-400">
            +{skills.length - 6}
          </span>
        )}
      </div>
    </div>
  );
}
