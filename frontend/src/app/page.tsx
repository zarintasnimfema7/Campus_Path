"use client";

import { Loader2, Route } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomePage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useAuth();

  useEffect(() => {
    function redirectUser() {
      if (!isLoaded) return;

      if (!isSignedIn) {
        router.replace("/login");
        return;
      }

      const workflow =
        sessionStorage.getItem("campuspath_workflow");

      if (workflow) {
        router.replace("/dashboard");
      } else {
        router.replace("/onboarding");
      }
    }

    redirectUser();
  }, [isLoaded, isSignedIn, router]);

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#07111F] text-white">
      <div className="absolute h-72 w-72 animate-pulse rounded-full bg-violet-600/20 blur-[100px]" />

      <div className="relative text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 shadow-2xl shadow-violet-900/40">
          <Route className="h-7 w-7" />
        </div>

        <h1 className="mt-5 text-2xl font-bold">
          CampusPath
        </h1>

        <div className="mt-5 flex items-center justify-center gap-2 text-sm text-slate-400">
          <Loader2 className="h-4 w-4 animate-spin text-cyan-300" />
          Preparing your workspace
        </div>
      </div>
    </main>
  );
}
