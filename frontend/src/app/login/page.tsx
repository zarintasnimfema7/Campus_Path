"use client";

import {
  ArrowRight,
  CheckCircle2,
  Loader2,
  LockKeyhole,
  Mail,
  Route,
  Sparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event: FormEvent) {
    event.preventDefault();

    setError("");

    if (!email.trim()) {
      setError("Enter your email address.");
      return;
    }

    try {
      setLoading(true);

      const { error: loginError } =
        await supabase.auth.signInWithOtp({
          email: email.trim(),
          options: {
            shouldCreateUser: false,
          },
        });

      if (loginError) {
        setError(loginError.message);
        return;
      }

      sessionStorage.setItem(
        "campuspath_email",
        email.trim()
      );

      sessionStorage.setItem(
        "campuspath_auth_mode",
        "login"
      );

      router.push("/verify-otp");
    } catch {
      setError("Unable to send your login code.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[#F6F7FB] lg:grid lg:grid-cols-[1.05fr_0.95fr]">
      {/* BRAND SIDE */}
      <section className="relative hidden min-h-screen overflow-hidden bg-[#07111F] p-12 text-white lg:flex lg:flex-col lg:justify-between xl:p-16">
        <div className="absolute -left-32 top-32 h-96 w-96 animate-pulse rounded-full bg-violet-600/20 blur-[100px]" />

        <div className="absolute -bottom-28 right-0 h-96 w-96 rounded-full bg-cyan-400/10 blur-[110px]" />

        <div className="absolute right-20 top-20 h-24 w-24 rounded-full border border-white/10" />

        <div className="absolute right-32 top-32 h-24 w-24 rounded-full border border-violet-400/10" />

        <div className="relative z-10">
          <Logo dark />
        </div>

        <div className="relative z-10 max-w-xl animate-[fadeUp_700ms_ease-out]">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.17em] text-cyan-200">
            <Sparkles className="h-3.5 w-3.5" />
            Autonomous career intelligence
          </div>

          <h1 className="text-5xl font-bold leading-[1.08] tracking-tight xl:text-6xl">
            Your career path,
            <span className="bg-gradient-to-r from-violet-300 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">
              {" "}
              continuously improving.
            </span>
          </h1>

          <p className="mt-7 max-w-lg text-lg leading-8 text-slate-300">
            CampusPath analyzes your skills, creates your
            learning roadmap, verifies real project evidence,
            and replans as you progress.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            <Feature label="Analyze" />
            <Feature label="Verify" />
            <Feature label="Replan" />
          </div>
        </div>

        <p className="relative z-10 text-xs text-slate-500">
          CampusPath Agent · Career readiness that adapts.
        </p>
      </section>

      {/* FORM SIDE */}
      <section className="relative flex min-h-screen items-center justify-center px-5 py-10 sm:px-10">
        <div className="absolute right-10 top-10 h-40 w-40 rounded-full bg-violet-100/70 blur-3xl" />

        <div className="relative w-full max-w-[520px] animate-[fadeUp_600ms_ease-out]">
          <div className="mb-12 lg:hidden">
            <Logo />
          </div>

          <div className="mb-9">
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#07111F] text-cyan-300 shadow-xl shadow-slate-900/10">
              <LockKeyhole className="h-6 w-6" />
            </div>

            <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-600">
              Welcome back
            </p>

            <h2 className="mt-3 text-4xl font-bold tracking-tight text-[#07111F] sm:text-5xl">
              Continue your path.
            </h2>

            <p className="mt-4 leading-7 text-slate-500">
              Enter your registered email. We&apos;ll send you
              a secure one-time verification code.
            </p>
          </div>

          <form onSubmit={handleLogin}>
            <label className="text-sm font-bold text-slate-700">
              Email address
            </label>

            <div className="relative mt-2">
              <Mail className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
                autoComplete="email"
                className="h-16 w-full rounded-2xl border border-slate-200 bg-white pl-12 pr-4 text-base text-slate-900 shadow-sm outline-none transition duration-300 placeholder:text-slate-400 focus:-translate-y-0.5 focus:border-violet-400 focus:shadow-lg focus:shadow-violet-100 focus:ring-4 focus:ring-violet-100"
              />
            </div>

            {error && (
              <div className="mt-5 animate-[fadeUp_250ms_ease-out] rounded-2xl border border-rose-100 bg-rose-50 px-5 py-4 text-sm font-medium text-rose-700">
                {error}
              </div>
            )}

            <button
              disabled={loading}
              className="group mt-6 flex h-16 w-full items-center justify-center gap-3 rounded-2xl bg-[#07111F] text-sm font-bold text-white shadow-xl shadow-slate-900/10 transition duration-300 hover:-translate-y-0.5 hover:bg-[#102039] hover:shadow-2xl disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Sending code...
                </>
              ) : (
                <>
                  Continue securely
                  <ArrowRight className="h-5 w-5 text-cyan-300 transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>
          </form>

          <div className="my-8 flex items-center gap-4">
            <div className="h-px flex-1 bg-slate-200" />
            <span className="text-xs font-medium text-slate-400">
              NEW TO CAMPUSPATH?
            </span>
            <div className="h-px flex-1 bg-slate-200" />
          </div>

          <button
            onClick={() => router.push("/register")}
            className="h-14 w-full rounded-2xl border border-slate-200 bg-white text-sm font-bold text-slate-700 transition duration-300 hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700"
          >
            Create an account
          </button>
        </div>
      </section>
    </main>
  );
}

function Feature({
  label,
}: {
  label: string;
}) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.05] px-3 py-3 text-sm font-medium text-slate-300 backdrop-blur">
      <CheckCircle2 className="h-4 w-4 text-cyan-300" />
      {label}
    </div>
  );
}

function Logo({
  dark = false,
}: {
  dark?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex h-11 w-11 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-900/20">
        <Route className="h-5 w-5" />

        <span className="absolute bottom-0 right-0 h-3 w-3 rounded-tl-lg bg-cyan-300" />
      </div>

      <span
        className={`text-2xl font-bold tracking-tight ${
          dark ? "text-white" : "text-[#07111F]"
        }`}
      >
        CampusPath
      </span>
    </div>
  );
}