"use client";

import {
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  Loader2,
  RefreshCw,
  Route,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";
import { FaGithub } from "react-icons/fa";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { supabase } from "@/lib/supabase";

type Task = {
  title?: string;
  skill?: string;
  description?: string;
  status?: string;
  estimated_time?: string;
};

type WorkflowData = {
  job?: {
    job_title?: string;
  };

  student?: {
    name?: string;
    skills?: string[];
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
    tasks?: Task[];
  };
};

type VerificationResult = {
  score?: number;
  verification_score?: number;
  verified?: boolean;
  status?: string;
  skill?: string;
  summary?: string;
  feedback?: string;
  evidence_summary?: string;
  technologies_found?: string[];
  matched_evidence?: string[];
  missing_evidence?: string[];
};

type ReplanResult = {
  readiness_score?: number;

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
    tasks?: Task[];
  };

  detail?: string;
  message?: string;
};

export default function EvidencePage() {
  const router = useRouter();

  const [workflow, setWorkflow] =
    useState<WorkflowData | null>(null);

  const [repoUrl, setRepoUrl] = useState("");
  const [selectedSkill, setSelectedSkill] = useState("");

  const [verification, setVerification] =
    useState<VerificationResult | null>(null);

  const [oldReadiness, setOldReadiness] = useState(0);

  const [newReadiness, setNewReadiness] =
    useState<number | null>(null);

  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [replanning, setReplanning] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadPage() {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (!session) {
          router.replace("/login");
          return;
        }

        const saved =
          sessionStorage.getItem("campuspath_workflow");

        if (!saved) {
          router.replace("/onboarding");
          return;
        }

        const parsed: WorkflowData =
          JSON.parse(saved);

        setWorkflow(parsed);

        const score = Math.round(
          parsed.skill_gap?.readiness_score ?? 0
        );

        setOldReadiness(score);

        const missing =
          parsed.skill_gap?.missing_skills ?? [];

        const partial =
          parsed.skill_gap?.partial_skills ?? [];

        if (missing.length > 0) {
          setSelectedSkill(missing[0]);
        } else if (partial.length > 0) {
          setSelectedSkill(partial[0]);
        }
      } catch {
        router.replace("/onboarding");
        return;
      } finally {
        setLoading(false);
      }
    }

    loadPage();
  }, [router]);

  const availableSkills = Array.from(
    new Set([
      ...(workflow?.skill_gap?.missing_skills ?? []),
      ...(workflow?.skill_gap?.partial_skills ?? []),
    ])
  );

  async function verifyEvidence() {
    setError("");
    setMessage("");
    setVerification(null);
    setNewReadiness(null);

    if (!repoUrl.trim()) {
      setError("Enter your GitHub repository URL.");
      return;
    }

    if (!selectedSkill) {
      setError(
        "Select the skill this repository demonstrates."
      );
      return;
    }

    if (!repoUrl.includes("github.com")) {
      setError(
        "Please enter a valid GitHub repository URL."
      );
      return;
    }

    try {
      setVerifying(true);

      const response = await apiFetch(
        "/evidence/verify-github",
        {
          method: "POST",
          body: JSON.stringify({
            repository_url: repoUrl.trim(),
            skill: selectedSkill,
          }),
        }
      );

      const result:
        | VerificationResult
        | {
            detail?: string;
            message?: string;
          } = await response.json();

      if (!response.ok) {
        const errorResult = result as {
          detail?: string;
          message?: string;
        };

        throw new Error(
          errorResult.detail ||
            errorResult.message ||
            "Evidence verification failed."
        );
      }

      setVerification(
        result as VerificationResult
      );

      setMessage(
        "Repository analyzed. Evidence verification is complete."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not verify this repository."
      );
    } finally {
      setVerifying(false);
    }
  }

  async function replanPath() {
    if (!verification || !workflow) {
      return;
    }

    setError("");
    setMessage("");

    try {
      setReplanning(true);

      const verificationScore =
        verification.verification_score ??
        verification.score ??
        0;

      const response = await apiFetch(
        "/replan",
        {
          method: "POST",
          body: JSON.stringify({
            skill_gap: workflow.skill_gap,
            verified_skill: selectedSkill,
            verification_score: verificationScore,
          }),
        }
      );

      const result: ReplanResult =
        await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail ||
            result.message ||
            "Could not update the learning path."
        );
      }

      const updatedGap =
        result.skill_gap ??
        workflow.skill_gap;

      const updatedPlan =
        result.plan ??
        workflow.plan;

      const updatedWorkflow: WorkflowData = {
        ...workflow,
        skill_gap: updatedGap,
        plan: updatedPlan,
      };

      const updatedScore = Math.round(
        result.readiness_score ??
          updatedGap?.readiness_score ??
          oldReadiness
      );

      setNewReadiness(updatedScore);
      setWorkflow(updatedWorkflow);

      sessionStorage.setItem(
        "campuspath_workflow",
        JSON.stringify(updatedWorkflow)
      );

      setMessage(
        "Readiness updated and your remaining learning path has been replanned."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Replanning failed."
      );
    } finally {
      setReplanning(false);
    }
  }

  if (loading || !workflow) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#F4F6FA]">
        <div className="text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-violet-600" />

          <p className="mt-4 text-sm font-medium text-slate-500">
            Preparing evidence workspace...
          </p>
        </div>
      </main>
    );
  }

  const score =
    verification?.verification_score ??
    verification?.score ??
    null;

  const verified =
    verification?.verified ??
    (verification?.status?.toLowerCase() ===
      "verified");

  return (
    <main className="min-h-screen bg-[#F4F6FA]">
      {/* TOP BAR */}
      <header className="border-b border-slate-200/80 bg-white">
        <div className="mx-auto flex h-20 max-w-[1400px] items-center justify-between px-5 sm:px-8 lg:px-10">
          <button
            onClick={() =>
              router.push("/dashboard")
            }
            className="flex items-center gap-3"
          >
            <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-900/20">
              <Route className="h-5 w-5" />

              <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-tl-lg bg-cyan-300" />
            </div>

            <span className="text-xl font-bold tracking-tight text-[#07111F]">
              CampusPath
            </span>
          </button>

          <button
            onClick={() =>
              router.push("/learning-path")
            }
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
          >
            <ArrowLeft className="h-4 w-4" />
            Learning Path
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-[1400px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
        {/* HERO */}
        <section className="relative overflow-hidden rounded-[32px] bg-[#07111F] p-7 text-white shadow-xl shadow-slate-900/5 sm:p-10">
          <div className="absolute -right-24 -top-28 h-80 w-80 rounded-full bg-violet-500/20 blur-3xl" />

          <div className="absolute -bottom-32 right-40 h-72 w-72 rounded-full bg-cyan-400/10 blur-3xl" />

          <div className="relative grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.16em] text-cyan-200">
                <ShieldCheck className="h-3.5 w-3.5" />
                Evidence Verification Agent
              </div>

              <h1 className="mt-5 max-w-3xl text-3xl font-bold tracking-tight sm:text-5xl">
                Turn your work into
                <span className="bg-gradient-to-r from-violet-300 to-cyan-300 bg-clip-text text-transparent">
                  {" "}
                  verified readiness.
                </span>
              </h1>

              <p className="mt-5 max-w-2xl leading-7 text-slate-300">
                Submit a GitHub repository. CampusPath
                analyzes the project for evidence of your
                target skill, updates your readiness, and
                replans your next steps.
              </p>
            </div>

            <div className="min-w-[190px] rounded-3xl border border-white/10 bg-white/[0.06] p-6 backdrop-blur">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Current readiness
              </p>

              <div className="mt-3 flex items-end gap-1">
                <span className="text-5xl font-bold">
                  {newReadiness ?? oldReadiness}
                </span>

                <span className="mb-1 text-xl text-cyan-300">
                  %
                </span>
              </div>

              {newReadiness !== null &&
                newReadiness !== oldReadiness && (
                  <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-2.5 py-1 text-xs font-bold text-emerald-300">
                    <TrendingUp className="h-3.5 w-3.5" />

                    {newReadiness > oldReadiness
                      ? `+${
                          newReadiness -
                          oldReadiness
                        }`
                      : newReadiness - oldReadiness}{" "}
                    points
                  </div>
                )}
            </div>
          </div>
        </section>

        <div className="mt-7 grid gap-7 xl:grid-cols-[0.9fr_1.1fr]">
          {/* SUBMISSION */}
          <section className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="mb-7 flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#07111F] text-cyan-300">
                <FaGithub className="h-6 w-6" />
              </div>

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet-600">
                  Step 01
                </p>

                <h2 className="mt-1 text-2xl font-bold tracking-tight">
                  Submit your evidence
                </h2>

                <p className="mt-1 text-sm leading-6 text-slate-500">
                  Choose a skill and provide the
                  repository where you demonstrated it.
                </p>
              </div>
            </div>

            <label className="text-sm font-bold text-slate-700">
              Skill to verify
            </label>

            <select
              value={selectedSkill}
              onChange={(event) =>
                setSelectedSkill(
                  event.target.value
                )
              }
              className="mt-2 h-14 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-100"
            >
              {availableSkills.length === 0 && (
                <option value="">
                  No missing skills available
                </option>
              )}

              {availableSkills.map((skill) => (
                <option
                  key={skill}
                  value={skill}
                >
                  {skill}
                </option>
              ))}
            </select>

            <label className="mt-6 block text-sm font-bold text-slate-700">
              GitHub repository
            </label>

            <div className="relative mt-2">
              <FaGithub className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

              <input
                type="url"
                value={repoUrl}
                onChange={(event) =>
                  setRepoUrl(
                    event.target.value
                  )
                }
                placeholder="https://github.com/username/project"
                className="h-14 w-full rounded-2xl border border-slate-200 bg-white pl-12 pr-4 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-violet-400 focus:ring-4 focus:ring-violet-100"
              />
            </div>

            <div className="mt-5 rounded-2xl border border-cyan-100 bg-cyan-50/60 p-4">
              <div className="flex gap-3">
                <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-cyan-700" />

                <p className="text-sm leading-6 text-slate-600">
                  The agent can inspect repository
                  metadata, languages and project
                  content to determine whether your work
                  provides meaningful evidence for the
                  selected skill.
                </p>
              </div>
            </div>

            {error && (
              <div className="mt-5 flex gap-3 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
                <XCircle className="h-5 w-5 shrink-0" />

                {error}
              </div>
            )}

            {message && (
              <div className="mt-5 flex gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-700">
                <CheckCircle2 className="h-5 w-5 shrink-0" />

                {message}
              </div>
            )}

            <button
              onClick={verifyEvidence}
              disabled={verifying}
              className="mt-6 flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 text-sm font-bold text-white shadow-lg shadow-violet-600/15 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {verifying ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Agent is inspecting repository...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Verify GitHub evidence
                </>
              )}
            </button>
          </section>

          {/* RESULT */}
          <section className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
            {!verification ? (
              <div className="flex min-h-[500px] flex-col items-center justify-center text-center">
                <div className="relative">
                  <div className="absolute inset-0 rounded-full bg-violet-400/20 blur-2xl" />

                  <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl border border-violet-100 bg-violet-50 text-violet-600">
                    <ShieldCheck className="h-9 w-9" />
                  </div>
                </div>

                <h2 className="mt-6 text-2xl font-bold">
                  Waiting for evidence
                </h2>

                <p className="mt-3 max-w-md text-sm leading-7 text-slate-500">
                  Your verification result will appear
                  here with an evidence score, detected
                  technologies, and feedback from the
                  verification agent.
                </p>

                <div className="mt-8 flex items-center gap-3 text-xs font-bold uppercase tracking-wider text-slate-400">
                  <span>GitHub</span>

                  <span className="h-px w-8 bg-slate-200" />

                  <span>Agent</span>

                  <span className="h-px w-8 bg-slate-200" />

                  <span>Readiness</span>
                </div>
              </div>
            ) : (
              <VerificationPanel
                result={verification}
                score={score}
                verified={verified}
                selectedSkill={selectedSkill}
                repoUrl={repoUrl}
                replanning={replanning}
                newReadiness={newReadiness}
                onReplan={replanPath}
                onLearningPath={() =>
                  router.push(
                    "/learning-path"
                  )
                }
              />
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

function VerificationPanel({
  result,
  score,
  verified,
  selectedSkill,
  repoUrl,
  replanning,
  newReadiness,
  onReplan,
  onLearningPath,
}: {
  result: VerificationResult;
  score: number | null;
  verified: boolean;
  selectedSkill: string;
  repoUrl: string;
  replanning: boolean;
  newReadiness: number | null;
  onReplan: () => void;
  onLearningPath: () => void;
}) {
  const technologies =
    result.technologies_found ?? [];

  const matched =
    result.matched_evidence ?? [];

  const missing =
    result.missing_evidence ?? [];

  return (
    <div>
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-violet-600">
            Verification result
          </p>

          <h2 className="mt-2 text-2xl font-bold">
            {selectedSkill}
          </h2>

          <a
            href={repoUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-slate-400 transition hover:text-violet-600"
          >
            View repository
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>

        <div
          className={`rounded-2xl px-5 py-4 ${
            verified
              ? "bg-emerald-50 text-emerald-700"
              : "bg-amber-50 text-amber-700"
          }`}
        >
          <p className="text-xs font-bold uppercase tracking-wider opacity-70">
            Evidence score
          </p>

          <p className="mt-1 text-3xl font-bold">
            {score ?? "—"}

            {score !== null && (
              <span className="text-lg">
                /100
              </span>
            )}
          </p>
        </div>
      </div>

      <div
        className={`mt-7 flex gap-3 rounded-2xl border p-4 ${
          verified
            ? "border-emerald-100 bg-emerald-50"
            : "border-amber-100 bg-amber-50"
        }`}
      >
        {verified ? (
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
        ) : (
          <ShieldCheck className="h-5 w-5 shrink-0 text-amber-600" />
        )}

        <div>
          <p className="text-sm font-bold text-slate-800">
            {verified
              ? "Strong evidence detected"
              : "Evidence needs improvement"}
          </p>

          <p className="mt-1 text-sm leading-6 text-slate-600">
            {result.summary ||
              result.feedback ||
              result.evidence_summary ||
              "CampusPath finished evaluating this repository."}
          </p>
        </div>
      </div>

      {technologies.length > 0 && (
        <div className="mt-7">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
            Technologies detected
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            {technologies.map(
              (technology) => (
                <span
                  key={technology}
                  className="rounded-xl border border-violet-100 bg-violet-50 px-3 py-2 text-xs font-bold text-violet-700"
                >
                  {technology}
                </span>
              )
            )}
          </div>
        </div>
      )}

      {matched.length > 0 && (
        <div className="mt-7">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
            Evidence found
          </p>

          <div className="mt-3 space-y-2">
            {matched.map(
              (item, index) => (
                <div
                  key={index}
                  className="flex gap-3 rounded-xl bg-emerald-50/70 p-3 text-sm text-slate-600"
                >
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />

                  {item}
                </div>
              )
            )}
          </div>
        </div>
      )}

      {missing.length > 0 && (
        <div className="mt-7">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">
            What could be stronger
          </p>

          <div className="mt-3 space-y-2">
            {missing.map(
              (item, index) => (
                <div
                  key={index}
                  className="flex gap-3 rounded-xl bg-amber-50/70 p-3 text-sm text-slate-600"
                >
                  <Target className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />

                  {item}
                </div>
              )
            )}
          </div>
        </div>
      )}

      <div className="mt-8 border-t border-slate-100 pt-6">
        {newReadiness === null ? (
          <>
            <div className="rounded-2xl bg-[#07111F] p-5 text-white">
              <div className="flex gap-3">
                <Sparkles className="h-5 w-5 shrink-0 text-cyan-300" />

                <div>
                  <p className="font-bold">
                    Continue the agent loop
                  </p>

                  <p className="mt-1 text-sm leading-6 text-slate-300">
                    Apply this verification result,
                    recalculate readiness, and let
                    CampusPath regenerate your remaining
                    path.
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={onReplan}
              disabled={replanning}
              className="mt-4 flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-[#07111F] text-sm font-bold text-white transition hover:bg-[#102039] disabled:opacity-60"
            >
              {replanning ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Replanning your path...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 text-cyan-300" />
                  Update readiness & replan
                </>
              )}
            </button>
          </>
        ) : (
          <div className="rounded-2xl border border-emerald-100 bg-gradient-to-r from-emerald-50 to-cyan-50 p-5">
            <div className="flex gap-3">
              <CheckCircle2 className="h-6 w-6 shrink-0 text-emerald-600" />

              <div className="flex-1">
                <p className="font-bold text-slate-900">
                  Learning path updated
                </p>

                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Your readiness is now{" "}
                  <strong>
                    {newReadiness}%
                  </strong>
                  . The remaining tasks have been
                  adjusted using your verified evidence.
                </p>

                <button
                  onClick={onLearningPath}
                  className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-violet-700"
                >
                  View updated learning path

                  <ArrowLeft className="h-4 w-4 rotate-180" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}