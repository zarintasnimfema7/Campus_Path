"use client";

import {
  Award,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Mail,
  Route,
  Sparkles,
  Target,
  User,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { supabase } from "@/lib/supabase";

type Item = {
  degree?: string;
  institution?: string;
  field?: string;
  year?: string;

  role?: string;
  organization?: string;
  duration?: string;
  description?: string;
};

type Workflow = {
  student?: {
    name?: string;
    skills?: string[];
    education?: Item[];
    experience?: Item[];
    certifications?: string[];
  };

  job?: {
    job_title?: string;
  };

  skill_gap?: {
    readiness_score?: number;
  };
};

export default function ProfilePage() {
  const router = useRouter();

  const [workflow, setWorkflow] =
    useState<Workflow | null>(null);

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProfile() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.replace("/login");
        return;
      }

      setEmail(session.user.email ?? "");

      const stored =
        sessionStorage.getItem("campuspath_workflow");

      if (stored) {
        try {
          setWorkflow(JSON.parse(stored));
        } catch {
          setWorkflow({});
        }
      } else {
        setWorkflow({});
      }

      setLoading(false);
    }

    loadProfile();
  }, [router]);

  async function logout() {
    await supabase.auth.signOut();
    sessionStorage.clear();
    router.replace("/login");
  }

  if (loading || !workflow) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F6FA]">
        <div className="h-11 w-11 animate-spin rounded-full border-4 border-slate-200 border-t-violet-600" />
      </div>
    );
  }

  const student = workflow.student ?? {};

  const name =
    student.name ||
    sessionStorage.getItem("campuspath_name") ||
    "CampusPath Student";

  const initials = name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const readiness = Math.round(
    workflow.skill_gap?.readiness_score ?? 0
  );

  const skills = student.skills ?? [];
  const education = student.education ?? [];
  const experience = student.experience ?? [];
  const certifications =
    student.certifications ?? [];

  return (
    <div className="min-h-screen bg-[#F4F6FA]">
      {/* NAV */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-[1400px] items-center justify-between px-5 sm:px-8 lg:px-10">
          <Logo />

          <div className="flex items-center gap-2">
            <NavButton
              label="Dashboard"
              icon={<LayoutDashboard />}
              onClick={() =>
                router.push("/dashboard")
              }
            />

            <button
              onClick={logout}
              className="flex h-11 items-center gap-2 rounded-xl border border-slate-200 px-4 text-sm font-bold text-slate-500 transition hover:bg-rose-50 hover:text-rose-600"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">
                Sign out
              </span>
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1400px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
        {/* PROFILE HERO */}
        <section className="relative overflow-hidden rounded-[32px] bg-[#07111F] p-7 text-white shadow-xl shadow-slate-900/5 sm:p-10">
          <div className="absolute -right-20 -top-32 h-80 w-80 rounded-full bg-violet-500/20 blur-3xl" />

          <div className="absolute bottom-0 right-1/3 h-52 w-52 rounded-full bg-cyan-300/10 blur-3xl" />

          <div className="relative flex flex-col justify-between gap-8 md:flex-row md:items-center">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
              <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-[28px] bg-gradient-to-br from-violet-500 to-indigo-600 text-3xl font-bold shadow-2xl shadow-violet-900/30">
                {initials}
              </div>

              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-bold uppercase tracking-wider text-cyan-200">
                  <Sparkles className="h-3 w-3" />
                  Career profile
                </div>

                <h1 className="mt-3 text-3xl font-bold sm:text-4xl">
                  {name}
                </h1>

                <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-300">
                  {email && (
                    <span className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-violet-300" />
                      {email}
                    </span>
                  )}

                  {workflow.job?.job_title && (
                    <span className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-cyan-300" />
                      {workflow.job.job_title}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.06] px-7 py-5 backdrop-blur">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Readiness
              </p>

              <div className="mt-2 flex items-end">
                <span className="text-5xl font-bold">
                  {readiness}
                </span>

                <span className="mb-1 text-xl text-cyan-300">
                  %
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* STATS */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Stat
            icon={<CheckCircle2 />}
            value={skills.length}
            label="Skills detected"
            accent="violet"
          />

          <Stat
            icon={<BriefcaseBusiness />}
            value={experience.length}
            label="Experience entries"
            accent="cyan"
          />

          <Stat
            icon={<GraduationCap />}
            value={education.length}
            label="Education"
            accent="amber"
          />

          <Stat
            icon={<Award />}
            value={certifications.length}
            label="Certifications"
            accent="green"
          />
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          {/* SKILLS */}
          <Card
            title="Skill inventory"
            subtitle="Skills CampusPath extracted from your CV."
            icon={<Target />}
          >
            {skills.length === 0 ? (
              <Empty text="No skills available yet." />
            ) : (
              <div className="flex flex-wrap gap-2.5">
                {skills.map((skill) => (
                  <span
                    key={skill}
                    className="rounded-xl border border-violet-100 bg-violet-50 px-3.5 py-2 text-sm font-bold text-violet-700 transition hover:-translate-y-0.5 hover:shadow-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </Card>

          {/* TARGET */}
          <Card
            title="Career target"
            subtitle="The role your current roadmap is optimized for."
            icon={<Route />}
          >
            <div className="rounded-2xl bg-gradient-to-br from-[#07111F] to-[#102039] p-6 text-white">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-cyan-300">
                Current target
              </p>

              <h3 className="mt-3 text-2xl font-bold">
                {workflow.job?.job_title ||
                  "No target selected"}
              </h3>

              <p className="mt-3 text-sm leading-6 text-slate-300">
                CampusPath continuously compares your
                verified skills against this role.
              </p>

              <button
                onClick={() =>
                  router.push("/skill-gap")
                }
                className="mt-5 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-bold transition hover:bg-white/15"
              >
                View skill analysis
              </button>
            </div>
          </Card>
        </div>

        {/* EXPERIENCE */}
        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <Card
            title="Experience"
            subtitle="Professional experience extracted from your CV."
            icon={<BriefcaseBusiness />}
          >
            {experience.length === 0 ? (
              <Empty text="No experience entries detected." />
            ) : (
              <div className="space-y-3">
                {experience.map((item, index) => (
                  <TimelineItem
                    key={index}
                    title={
                      item.role ||
                      "Experience"
                    }
                    subtitle={
                      item.organization
                    }
                    meta={item.duration}
                    description={item.description}
                  />
                ))}
              </div>
            )}
          </Card>

          <Card
            title="Education"
            subtitle="Academic background extracted from your CV."
            icon={<GraduationCap />}
          >
            {education.length === 0 ? (
              <Empty text="No education entries detected." />
            ) : (
              <div className="space-y-3">
                {education.map((item, index) => (
                  <TimelineItem
                    key={index}
                    title={
                      item.degree ||
                      item.field ||
                      "Education"
                    }
                    subtitle={
                      item.institution
                    }
                    meta={item.year}
                  />
                ))}
              </div>
            )}
          </Card>
        </div>
      </main>
    </div>
  );
}

function Card({
  title,
  subtitle,
  icon,
  children,
}: {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="animate-[fadeUp_500ms_ease-out] rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm transition duration-300 hover:shadow-lg hover:shadow-slate-900/[0.04] sm:p-7">
      <div className="mb-6 flex gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
          <span className="[&>svg]:h-5 [&>svg]:w-5">
            {icon}
          </span>
        </div>

        <div>
          <h2 className="font-bold text-slate-950">
            {title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {subtitle}
          </p>
        </div>
      </div>

      {children}
    </section>
  );
}

function TimelineItem({
  title,
  subtitle,
  meta,
  description,
}: {
  title?: string;
  subtitle?: string;
  meta?: string;
  description?: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 transition hover:border-violet-100 hover:bg-violet-50/40">
      <div className="flex justify-between gap-4">
        <div>
          <p className="font-bold text-slate-800">
            {title}
          </p>

          {subtitle && (
            <p className="mt-1 text-sm text-slate-500">
              {subtitle}
            </p>
          )}
        </div>

        {meta && (
          <span className="shrink-0 text-xs font-bold text-violet-600">
            {meta}
          </span>
        )}
      </div>

      {description && (
        <p className="mt-3 text-sm leading-6 text-slate-500">
          {description}
        </p>
      )}
    </div>
  );
}

function Stat({
  icon,
  value,
  label,
  accent,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  accent: "violet" | "cyan" | "amber" | "green";
}) {
  const styles = {
    violet: "bg-violet-50 text-violet-600",
    cyan: "bg-cyan-50 text-cyan-700",
    amber: "bg-amber-50 text-amber-600",
    green: "bg-emerald-50 text-emerald-600",
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-lg">
      <div className="flex items-center justify-between">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl ${styles[accent]}`}
        >
          <span className="[&>svg]:h-5 [&>svg]:w-5">
            {icon}
          </span>
        </div>

        <span className="text-3xl font-bold">
          {value}
        </span>
      </div>

      <p className="mt-4 text-sm font-medium text-slate-500">
        {label}
      </p>
    </div>
  );
}

function Empty({
  text,
}: {
  text: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-400">
      {text}
    </div>
  );
}

function NavButton({
  label,
  icon,
  onClick,
}: {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="hidden h-11 items-center gap-2 rounded-xl px-4 text-sm font-bold text-slate-500 transition hover:bg-violet-50 hover:text-violet-700 sm:flex"
    >
      {icon}
      {label}
    </button>
  );
}

function Logo() {
  return (
    <button
      onClick={() => {}}
      className="flex items-center gap-3"
    >
      <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white">
        <Route className="h-5 w-5" />
        <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-tl-lg bg-cyan-300" />
      </div>

      <span className="text-xl font-bold text-[#07111F]">
        CampusPath
      </span>
    </button>
  );
}
