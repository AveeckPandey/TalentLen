import { Suspense } from "react";
import Link from "next/link";
import LoginForm from "./LoginForm";

export const metadata = {
  title: "Log in — TalentLens",
  description: "Log in or create your TalentLens recruiter account.",
};

export default function LoginPage() {
  return (
    <main className="min-h-screen flex flex-col bg-neutral-50 dark:bg-black text-neutral-900 dark:text-neutral-100">
      <header className="bg-white dark:bg-neutral-950 border-b border-neutral-200 dark:border-neutral-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3">
            <img
              src="/logo.png"
              alt="TalentLens logo"
              className="h-10 w-10 rounded-xl object-cover shadow-sm border border-neutral-100 dark:border-neutral-800"
            />
            <span className="text-lg font-bold tracking-tight">TalentLens</span>
          </Link>
          <Link
            href="/"
            className="px-3 py-1.5 text-xs font-medium text-neutral-600 dark:text-neutral-300 hover:text-black dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition"
          >
            ← Back to dashboard
          </Link>
        </div>
      </header>

      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <Suspense fallback={<div className="text-sm text-neutral-500">Loading…</div>}>
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
