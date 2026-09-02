"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowRight,
  BriefcaseBusiness,
  LockKeyhole,
  Mail,
  Sparkles,
  User,
} from "lucide-react";

import { useSignUp } from "@clerk/nextjs";

export default function RegisterPage() {
  const router = useRouter();

  const { signUp, fetchStatus } = useSignUp();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [error, setError] = useState("");

  const loading = fetchStatus === "fetching";

  async function handleRegister(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");

    if (!name.trim()) {
      setError("Please enter your full name.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      const { error: signUpError } =
        await signUp.password({
          emailAddress: email.trim(),
          password,

          // Keep the full name with the Clerk user.
          unsafeMetadata: {
            full_name: name.trim(),
          },
        });

      if (signUpError) {
        setError(
          signUpError.message ||
            "Could not create your account."
        );
        return;
      }

      const { error: verificationError } =
        await signUp.verifications.sendEmailCode();

      if (verificationError) {
        setError(
          verificationError.message ||
            "Could not send verification code."
        );
        return;
      }

      // Keep only for displaying on OTP page.
      sessionStorage.setItem(
        "campuspath_email",
        email.trim()
      );

      sessionStorage.setItem(
        "campuspath_name",
        name.trim()
      );

      router.push("/verify-otp");

    } catch (err) {
      console.error(err);

      setError(
        "Something went wrong. Please try again."
      );
    }
  }

  return (
    <main className="min-h-screen bg-slate-950">
      <div className="grid min-h-screen lg:grid-cols-2">

        {/* LEFT SIDE */}
        <section className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950">

          <div>
            <div className="flex items-center gap-3">

              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-500">
                <BriefcaseBusiness className="h-6 w-6 text-white" />
              </div>

              <span className="text-xl font-semibold text-white">
                CampusPath
              </span>

            </div>
          </div>

          <div className="max-w-xl">

            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-indigo-200">
              <Sparkles className="h-4 w-4" />
              AI-powered career readiness
            </div>

            <h1 className="text-5xl font-semibold leading-tight text-white">
              Turn your career goal into
              an actionable path.
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">
              CampusPath analyzes your CV,
              identifies your skill gaps and
              builds a personalized learning
              path backed by real evidence.
            </p>

          </div>

          <p className="text-sm text-slate-500">
            Analyze. Learn. Verify. Improve.
          </p>

        </section>


        {/* RIGHT SIDE */}
        <section className="flex items-center justify-center bg-white px-6 py-12">

          <div className="w-full max-w-md">

            {/* MOBILE LOGO */}
            <div className="mb-10 lg:hidden">

              <div className="flex items-center gap-3">

                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600">
                  <BriefcaseBusiness className="h-5 w-5 text-white" />
                </div>

                <span className="text-xl font-semibold text-slate-900">
                  CampusPath
                </span>

              </div>

            </div>


            {/* HEADING */}
            <div className="mb-8">

              <p className="mb-2 text-sm font-medium text-indigo-600">
                GET STARTED
              </p>

              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
                Create your account
              </h2>

              <p className="mt-3 text-slate-500">
                Start building your personalized
                career-readiness plan.
              </p>

            </div>


            {/* FORM */}
            <form
              onSubmit={handleRegister}
              className="space-y-5"
            >

              {/* NAME */}
              <div>

                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Full name
                </label>

                <div className="relative">

                  <User className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(event) =>
                      setName(event.target.value)
                    }
                    placeholder="Your name"
                    autoComplete="name"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                  />

                </div>

              </div>


              {/* EMAIL */}
              <div>

                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Email address
                </label>

                <div className="relative">

                  <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(event) =>
                      setEmail(event.target.value)
                    }
                    placeholder="you@example.com"
                    autoComplete="email"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                  />

                </div>

              </div>


              {/* PASSWORD */}
              <div>

                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Password
                </label>

                <div className="relative">

                  <LockKeyhole className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    placeholder="At least 8 characters"
                    autoComplete="new-password"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                  />

                </div>

              </div>


              {/* CONFIRM PASSWORD */}
              <div>

                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Confirm password
                </label>

                <div className="relative">

                  <LockKeyhole className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />

                  <input
                    type="password"
                    required
                    minLength={8}
                    value={confirmPassword}
                    onChange={(event) =>
                      setConfirmPassword(
                        event.target.value
                      )
                    }
                    placeholder="Confirm your password"
                    autoComplete="new-password"
                    className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                  />

                </div>

              </div>


              {/* ERROR */}
              {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  {error}
                </div>
              )}


              {/* Clerk bot protection */}
              <div
                id="clerk-captcha"
                data-cl-theme="light"
                data-cl-size="flexible"
              />


              {/* SUBMIT */}
              <button
                type="submit"
                disabled={loading}
                className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >

                {loading
                  ? "Creating account..."
                  : "Create account"}

                {!loading && (
                  <ArrowRight className="h-4 w-4" />
                )}

              </button>

            </form>


            <p className="mt-8 text-center text-sm text-slate-500">

              Already have an account?{" "}

              <Link
                href="/login"
                className="font-medium text-indigo-600 hover:text-indigo-700"
              >
                Sign in
              </Link>

            </p>

          </div>

        </section>

      </div>
    </main>
  );
}