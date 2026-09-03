"use client";

import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  CircleDashed,
  LayoutDashboard,
  LogOut,
  Menu,
  Route,
  Sparkles,
  Target,
  TrendingUp,
  User,
  X,
  Zap,
} from "lucide-react";
import { FaGithub } from "react-icons/fa";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth, useClerk } from "@clerk/nextjs";

type WorkflowData = {
  job?: {
    job_title?: string;
    required_skills?: string[];
    preferred_skills?: string[];
  };

  skill_gap?: {
    readiness_score?: number;
    required_score?: number;
    preferred_score?: number;
    matched_skills?: string[];
    partial_skills?: string[];
    missing_skills?: string[];
  };
};

export default function SkillGapPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useAuth();
  const { signOut } = useClerk();

  const [workflow, setWorkflow] =
    useState<WorkflowData | null>(null);

  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    function loadPage() {
      if (!isLoaded) return;

      if (!isSignedIn) {
        router.replace("/login");
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
  }, [isLoaded, isSignedIn, router]);

  async function logout() {
    await signOut();
    sessionStorage.clear();
    router.replace("/login");
  }

  if (loading || !workflow) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#F4F6FA]">
        <div className="text-center">
          <div className="mx-auto h-11 w-11 animate-spin rounded-full border-4 border-slate-200 border-t-violet-600" />

          <p className="mt-4 text-sm font-medium text-slate-500">
            Loading skill intelligence...
          </p>
        </div>
      </main>
    );
  }

  const gap = workflow.skill_gap;

  const matched = gap?.matched_skills ?? [];
  const partial = gap?.partial_skills ?? [];
  const missing = gap?.missing_skills ?? [];

  const readiness = Math.round(
    gap?.readiness_score ?? 0
  );

  const requiredScore = Math.round(
    gap?.required_score ?? 0
  );

  const preferredScore = Math.round(
    gap?.preferred_score ?? 0
  );

  const total =
    matched.length + partial.length + missing.length;

  const role =
    workflow.job?.job_title ?? "Target role";

  return (
    <div className="min-h-screen bg-[#F4F6FA] text-[#111827]">
      {/* MOBILE HEADER */}

      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-5 backdrop-blur lg:hidden">
        <Logo />

        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-xl p-2 hover:bg-slate-100"
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

          <p className="mt-2 text-sm font-semibold">
            {role}
          </p>

          <div className="mt-4 flex items-center gap-2">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-300"
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
            onClick={() =>
            {setSidebarOpen(false);
              router.push("/dashboard")
            }}
          />

          <NavButton
            icon={<Target />}
            label="Skill Gap"
            active
          />

            <NavButton
             icon={<Route />}
              label="Learning Path"
              onClick={() => {
              setSidebarOpen(false);
             router.push("/learning-path");
            }}
          />

          <NavButton
            icon={<FaGithub />}
            label="Evidence"
            onClick={() =>
                {setSidebarOpen(false);
              router.push("/evidence")
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
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-400 transition hover:bg-white/5 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* CONTENT */}

      <main className="lg:ml-[280px]">
        <div className="mx-auto max-w-[1400px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10">

          {/* HEADER */}

          <div className="mb-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-100 bg-violet-50 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.15em] text-violet-700">
              <Sparkles className="h-3.5 w-3.5" />
              Skill Intelligence
            </div>

            <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
              Your skill gap
            </h1>

            <p className="mt-2 max-w-2xl text-slate-500">
              CampusPath compared your current evidence and
              experience against the requirements for{" "}
              <strong className="text-slate-700">
                {role}
              </strong>
              .
            </p>
          </div>

          {/* SCORE AREA */}

          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <section className="relative overflow-hidden rounded-[30px] bg-[#07111F] p-7 text-white shadow-xl shadow-slate-900/5 sm:p-9">
              <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-violet-500/20 blur-3xl" />

              <div className="relative flex flex-col justify-between gap-8 md:flex-row md:items-center">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-300">
                    Overall readiness
                  </p>

                  <div className="mt-3 flex items-end">
                    <span className="text-7xl font-bold tracking-tight">
                      {readiness}
                    </span>

                    <span className="mb-2 ml-1 text-2xl text-slate-400">
                      %
                    </span>
                  </div>

                  <p className="mt-4 max-w-md text-sm leading-7 text-slate-300">
                    Your score changes as CampusPath verifies
                    new evidence and reevaluates your skill
                    profile.
                  </p>
                </div>

                <ReadinessRing value={readiness} />
              </div>
            </section>

            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              <ScoreBox
                title="Required skills"
                score={requiredScore}
                icon={<Target />}
                description="Core skills expected for this role."
                variant="violet"
              />

              <ScoreBox
                title="Preferred skills"
                score={preferredScore}
                icon={<Zap />}
                description="Extra skills that strengthen your profile."
                variant="cyan"
              />
            </section>
          </div>

          {/* COUNTERS */}

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <CounterCard
              title="Matched"
              value={matched.length}
              total={total}
              icon={<CheckCircle2 />}
              variant="green"
            />

            <CounterCard
              title="Partial"
              value={partial.length}
              total={total}
              icon={<CircleDashed />}
              variant="amber"
            />

            <CounterCard
              title="Missing"
              value={missing.length}
              total={total}
              icon={<AlertTriangle />}
              variant="red"
            />
          </div>

          {/* SKILL DETAILS */}

          <section className="mt-6 rounded-[30px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                Detailed analysis
              </p>

              <h2 className="mt-2 text-2xl font-bold">
                Where you stand
              </h2>
            </div>

            <div className="mt-7 grid gap-5 lg:grid-cols-3">
              <SkillSection
                title="Ready to use"
                subtitle="Skills already matching the role."
                skills={matched}
                type="matched"
              />

              <SkillSection
                title="Needs strengthening"
                subtitle="You have some relevant experience."
                skills={partial}
                type="partial"
              />

              <SkillSection
                title="Your priority gaps"
                subtitle="Skills your learning plan should target."
                skills={missing}
                type="missing"
              />
            </div>
          </section>

          {/* NEXT ACTION */}

          <section className="relative mt-6 overflow-hidden rounded-[30px] border border-violet-100 bg-gradient-to-r from-[#F0EBFF] via-white to-[#E7FBF8] p-7 sm:p-8">
            <div className="absolute -right-20 top-0 h-52 w-52 rounded-full bg-cyan-300/20 blur-3xl" />

            <div className="relative flex flex-col justify-between gap-6 md:flex-row md:items-center">
              <div className="flex gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#07111F] text-cyan-300 shadow-lg">
                  <BookOpen className="h-5 w-5" />
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet-600">
                    Recommended next step
                  </p>

                  <h3 className="mt-1 text-xl font-bold">
                    Close your highest-impact gaps
                  </h3>

                  <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
                    Your learning roadmap prioritizes missing
                    and partial skills so your effort has the
                    greatest impact on readiness.
                  </p>
                </div>
              </div>

              <button
                onClick={() =>
                  router.push("/learning-path")
                }
                className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[#07111F] px-5 py-3.5 text-sm font-bold text-white shadow-lg shadow-slate-900/10 transition hover:-translate-y-0.5 hover:bg-[#102039]"
              >
                Open learning path
                <ArrowRight className="h-4 w-4 text-cyan-300" />
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function ReadinessRing({
  value,
}: {
  value: number;
}) {
  return (
    <div
      className="relative flex h-44 w-44 shrink-0 items-center justify-center rounded-full"
      style={{
        background: `conic-gradient(
          #67e8f9 ${value * 3.6}deg,
          rgba(255,255,255,0.08) 0deg
        )`,
      }}
    >
      <div className="flex h-[132px] w-[132px] flex-col items-center justify-center rounded-full bg-[#07111F]">
        <TrendingUp className="h-6 w-6 text-violet-300" />

        <span className="mt-2 text-lg font-bold">
          {value}%
        </span>

        <span className="text-[10px] uppercase tracking-widest text-slate-500">
          readiness
        </span>
      </div>
    </div>
  );
}

function ScoreBox({
  title,
  score,
  description,
  icon,
  variant,
}: {
  title: string;
  score: number;
  description: string;
  icon: React.ReactNode;
  variant: "violet" | "cyan";
}) {
  const violet = variant === "violet";

  return (
    <div className="rounded-[26px] border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl ${
            violet
              ? "bg-violet-50 text-violet-600"
              : "bg-cyan-50 text-cyan-700"
          }`}
        >
          <span className="[&>svg]:h-5 [&>svg]:w-5">
            {icon}
          </span>
        </div>

        <span className="text-3xl font-bold">
          {score}%
        </span>
      </div>

      <h3 className="mt-5 font-bold">
        {title}
      </h3>

      <p className="mt-1 text-sm leading-6 text-slate-500">
        {description}
      </p>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${
            violet
              ? "bg-violet-500"
              : "bg-cyan-500"
          }`}
          style={{
            width: `${Math.min(score, 100)}%`,
          }}
        />
      </div>
    </div>
  );
}

function CounterCard({
  title,
  value,
  total,
  icon,
  variant,
}: {
  title: string;
  value: number;
  total: number;
  icon: React.ReactNode;
  variant: "green" | "amber" | "red";
}) {
  const style = {
    green:
      "bg-emerald-50 text-emerald-700 border-emerald-100",
    amber:
      "bg-amber-50 text-amber-700 border-amber-100",
    red:
      "bg-rose-50 text-rose-700 border-rose-100",
  }[variant];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl border ${style}`}
        >
          <span className="[&>svg]:h-5 [&>svg]:w-5">
            {icon}
          </span>
        </div>

        <p className="text-3xl font-bold text-slate-900">
          {value}
        </p>
      </div>

      <p className="mt-4 font-bold">
        {title}
      </p>

      <p className="mt-1 text-xs text-slate-400">
        {value} of {total || 0} analyzed skills
      </p>
    </div>
  );
}

function SkillSection({
  title,
  subtitle,
  skills,
  type,
}: {
  title: string;
  subtitle: string;
  skills: string[];
  type: "matched" | "partial" | "missing";
}) {
  const config = {
    matched: {
      icon: <CheckCircle2 />,
      iconStyle:
        "bg-emerald-100 text-emerald-700",
      border: "border-emerald-100",
      background: "bg-emerald-50/40",
      chip: "bg-white text-emerald-800",
    },

    partial: {
      icon: <CircleDashed />,
      iconStyle: "bg-amber-100 text-amber-700",
      border: "border-amber-100",
      background: "bg-amber-50/40",
      chip: "bg-white text-amber-800",
    },

    missing: {
      icon: <AlertTriangle />,
      iconStyle: "bg-rose-100 text-rose-700",
      border: "border-rose-100",
      background: "bg-rose-50/40",
      chip: "bg-white text-rose-800",
    },
  }[type];

  return (
    <div
      className={`rounded-2xl border p-5 ${config.border} ${config.background}`}
    >
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-xl ${config.iconStyle}`}
      >
        <span className="[&>svg]:h-5 [&>svg]:w-5">
          {config.icon}
        </span>
      </div>

      <h3 className="mt-4 font-bold">
        {title}
      </h3>

      <p className="mt-1 min-h-10 text-sm leading-5 text-slate-500">
        {subtitle}
      </p>

      <div className="mt-5 space-y-2">
        {skills.length === 0 ? (
          <div className="rounded-xl bg-white/70 p-3 text-sm text-slate-400">
            No skills in this category.
          </div>
        ) : (
          skills.map((skill) => (
            <div
              key={skill}
              className={`rounded-xl px-3 py-2.5 text-sm font-semibold shadow-sm ${config.chip}`}
            >
              {skill}
            </div>
          ))
        )}
      </div>
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
      <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg">
        <Route className="h-5 w-5" />

        <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-tl-lg bg-cyan-300" />
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
