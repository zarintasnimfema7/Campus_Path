"use client";

import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Mail,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useRouter } from "next/navigation";
import {
  ClipboardEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { supabase } from "@/lib/supabase";

const OTP_LENGTH = 8;
const RESEND_SECONDS = 60;

export default function VerifyOtpPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState<string[]>(
    Array(OTP_LENGTH).fill("")
  );

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [countdown, setCountdown] = useState(RESEND_SECONDS);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Get the email saved during registration
  useEffect(() => {
    const savedEmail = sessionStorage.getItem("campuspath_email");

    if (!savedEmail) {
      router.replace("/register");
      return;
    }

    setEmail(savedEmail);
  }, [router]);

  // Resend countdown
  useEffect(() => {
    if (countdown <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setCountdown((current) => current - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  // Handle one OTP box
  const handleChange = (index: number, value: string) => {
    const digit = value.replace(/\D/g, "").slice(-1);

    const newOtp = [...otp];
    newOtp[index] = digit;

    setOtp(newOtp);
    setError("");

    if (digit && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  // Handle backspace and arrow keys
  const handleKeyDown = (
    index: number,
    event: KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === "Backspace") {
      if (otp[index]) {
        const newOtp = [...otp];
        newOtp[index] = "";
        setOtp(newOtp);
      } else if (index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
    }

    if (event.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }

    if (
      event.key === "ArrowRight" &&
      index < OTP_LENGTH - 1
    ) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  // Allow user to paste the complete 8-digit OTP
  const handlePaste = (
    event: ClipboardEvent<HTMLInputElement>
  ) => {
    event.preventDefault();

    const pastedCode = event.clipboardData
      .getData("text")
      .replace(/\D/g, "")
      .slice(0, OTP_LENGTH);

    if (!pastedCode) {
      return;
    }

    const newOtp = Array(OTP_LENGTH).fill("");

    pastedCode.split("").forEach((digit, index) => {
      newOtp[index] = digit;
    });

    setOtp(newOtp);
    setError("");

    const nextIndex = Math.min(
      pastedCode.length,
      OTP_LENGTH - 1
    );

    inputRefs.current[nextIndex]?.focus();
  };

  // Verify OTP with Supabase
  const handleVerify = async () => {
    setError("");
    setMessage("");

    const token = otp.join("");

    if (token.length !== OTP_LENGTH) {
      setError(
        `Please enter the complete ${OTP_LENGTH}-digit verification code.`
      );
      return;
    }

    if (!email) {
      setError("Email address was not found. Please register again.");
      return;
    }

    try {
      setLoading(true);

      const { data, error: verifyError } =
        await supabase.auth.verifyOtp({
          email,
          token,
          type: "email",
        });

      if (verifyError) {
        setError(verifyError.message);
        return;
      }

      if (!data.session) {
        setError(
          "Verification succeeded, but no session was created. Please try signing in."
        );
        return;
      }

     sessionStorage.removeItem("campuspath_email");

const authMode =
  sessionStorage.getItem("campuspath_auth_mode");

sessionStorage.removeItem("campuspath_auth_mode");

if (authMode === "login") {
  const existingWorkflow =
    sessionStorage.getItem("campuspath_workflow");

  router.push(
    existingWorkflow ? "/dashboard" : "/onboarding"
  );

  return;
}

router.push("/onboarding");
    } catch (err) {
      console.error(err);

      setError(
        "Something went wrong while verifying your code."
      );
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP
  const handleResend = async () => {
    if (!email || countdown > 0 || resending) {
      return;
    }

    setError("");
    setMessage("");

    try {
      setResending(true);

      const { error: resendError } =
        await supabase.auth.signInWithOtp({
          email,
          options: {
            shouldCreateUser: true,
          },
        });

      if (resendError) {
        setError(resendError.message);
        return;
      }

      setOtp(Array(OTP_LENGTH).fill(""));
      setCountdown(RESEND_SECONDS);

      setMessage(
        "A new verification code has been sent to your email."
      );

      inputRefs.current[0]?.focus();
    } catch (err) {
      console.error(err);

      setError(
        "Something went wrong while resending the code."
      );
    } finally {
      setResending(false);
    }
  };

  return (
    <main className="min-h-screen bg-white lg:grid lg:grid-cols-2">
      {/* LEFT SIDE */}
      <section className="hidden min-h-screen flex-col justify-between bg-[#071126] p-12 text-white lg:flex xl:p-16">
        <div>
          <div className="mb-16 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600">
              <ShieldCheck className="h-6 w-6" />
            </div>

            <span className="text-2xl font-bold">
              CampusPath
            </span>
          </div>

          <div className="max-w-lg">
            <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-indigo-300">
              Secure verification
            </p>

            <h1 className="text-5xl font-bold leading-tight">
              One step closer to your career path.
            </h1>

            <p className="mt-6 text-lg leading-8 text-slate-300">
              Verify your email to continue building your
              personalized career-readiness plan.
            </p>
          </div>
        </div>

        <div className="space-y-5">
          <div className="flex items-center gap-4">
            <CheckCircle2 className="h-5 w-5 text-indigo-400" />
            <span className="text-slate-300">
              AI-powered skill analysis
            </span>
          </div>

          <div className="flex items-center gap-4">
            <CheckCircle2 className="h-5 w-5 text-indigo-400" />
            <span className="text-slate-300">
              Personalized learning plans
            </span>
          </div>

          <div className="flex items-center gap-4">
            <CheckCircle2 className="h-5 w-5 text-indigo-400" />
            <span className="text-slate-300">
              Evidence-based readiness tracking
            </span>
          </div>
        </div>
      </section>

      {/* RIGHT SIDE */}
      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8 lg:px-12">
        <div className="w-full max-w-xl">
          {/* Mobile logo */}
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
              <ShieldCheck className="h-5 w-5" />
            </div>

            <span className="text-xl font-bold text-slate-950">
              CampusPath
            </span>
          </div>

          <button
            type="button"
            onClick={() => router.push("/register")}
            className="mb-10 flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-950"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>

          <div className="mb-9">
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
              <Mail className="h-7 w-7" />
            </div>

            <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-indigo-600">
              Verify your email
            </p>

            <h2 className="text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">
              Check your inbox
            </h2>

            <p className="mt-4 leading-7 text-slate-500">
              We sent an {OTP_LENGTH}-digit verification
              code to
            </p>

            <p className="mt-1 font-semibold text-slate-800">
              {email || "your email address"}
            </p>
          </div>

          {/* OTP */}
          <div>
            <label className="mb-4 block font-medium text-slate-800">
              Verification code
            </label>

            <div className="grid grid-cols-4 gap-3 sm:grid-cols-8">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={(element) => {
                    inputRefs.current[index] = element;
                  }}
                  type="text"
                  inputMode="numeric"
                  autoComplete={
                    index === 0 ? "one-time-code" : "off"
                  }
                  maxLength={1}
                  value={digit}
                  onChange={(event) =>
                    handleChange(index, event.target.value)
                  }
                  onKeyDown={(event) =>
                    handleKeyDown(index, event)
                  }
                  onPaste={handlePaste}
                  aria-label={`Verification digit ${
                    index + 1
                  }`}
                  className="h-16 w-full rounded-2xl border border-slate-200 bg-white text-center text-2xl font-semibold text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 sm:h-20"
                />
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* Success message */}
          {message && (
            <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700">
              {message}
            </div>
          )}

          {/* Verify */}
          <button
            type="button"
            onClick={handleVerify}
            disabled={loading}
            className="mt-7 flex h-16 w-full items-center justify-center gap-3 rounded-2xl bg-slate-950 text-base font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                Verify & Continue
                <ArrowRight className="h-5 w-5" />
              </>
            )}
          </button>

          {/* Resend */}
          <div className="mt-7 text-center">
            <p className="text-sm text-slate-500">
              Didn&apos;t receive the code?
            </p>

            <button
              type="button"
              onClick={handleResend}
              disabled={countdown > 0 || resending}
              className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 transition hover:text-indigo-700 disabled:cursor-not-allowed disabled:text-slate-400"
            >
              {resending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Sending...
                </>
              ) : countdown > 0 ? (
                `Resend code in ${countdown}s`
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Resend verification code
                </>
              )}
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}