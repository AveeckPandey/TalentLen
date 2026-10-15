"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { getSupabaseClient } from "@/lib/supabase";
import { Button } from "@/components/ui";

type AuthMode = "login" | "signup";

const INPUT_CLS =
  "w-full px-3 py-2 text-sm rounded-lg bg-white dark:bg-black border border-neutral-300 dark:border-neutral-700 text-neutral-900 dark:text-white placeholder-neutral-400 dark:placeholder-neutral-500 outline-none focus:border-neutral-500 dark:focus:border-neutral-400";

export default function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const modeParam = search.get("mode") === "signup" ? "signup" : "login";
  const next = search.get("next") || "/";

  const [mode, setMode] = useState<AuthMode>(modeParam);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setMode(search.get("mode") === "signup" ? "signup" : "login");
  }, [search]);

  useEffect(() => {
    // Apply saved theme (dashboard defaults to dark) so the auth page matches.
    try {
      const saved = localStorage.getItem("talentlens-theme");
      const dark = saved !== null ? saved === "dark" : true;
      document.documentElement.classList.toggle("dark", dark);
      document.body.classList.toggle("dark", dark);
    } catch {
      // ignore
    }
    // If already signed in, skip the auth page.
    const sb = getSupabaseClient();
    if (!sb) return;
    sb.auth.getSession().then(({ data }) => {
      if (data.session) router.replace(next.startsWith("/") ? next : "/");
    });
  }, [router, next]);

  function switchMode(m: AuthMode) {
    setMode(m);
    setError("");
    setInfo("");
    router.replace(`/login?mode=${m}${next !== "/" ? `&next=${encodeURIComponent(next)}` : ""}`);
  }

  async function signIn() {
    const sb = getSupabaseClient();
    if (!sb) return setError("Auth not configured. Set NEXT_PUBLIC_SUPABASE_URL + ANON_KEY and restart.");
    setError("");
    setInfo("");
    setBusy(true);
    try {
      const { error } = await sb.auth.signInWithPassword({ email: email.trim(), password });
      if (error) return setError(error.message);
      router.push(next.startsWith("/") ? next : "/");
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function signUp() {
    const sb = getSupabaseClient();
    if (!sb) return setError("Auth not configured.");
    setError("");
    setInfo("");
    setBusy(true);
    try {
      const { data, error } = await sb.auth.signUp({ email: email.trim(), password });
      if (error) return setError(error.message);
      if (data.session) {
        router.push(next.startsWith("/") ? next : "/");
        router.refresh();
      } else {
        setInfo("Account created — check your email to confirm, then log in.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function google() {
    const sb = getSupabaseClient();
    if (!sb) return setError("Auth not configured.");
    setError("");
    await sb.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
  }

  const isLogin = mode === "login";
  const submit = isLogin ? signIn : signUp;

  return (
    <div className="w-full max-w-sm bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-2xl p-6 space-y-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h1 className="text-base font-bold text-neutral-900 dark:text-white">
          {isLogin ? "Welcome back" : "Create your account"}
        </h1>
        <Link
          href="/"
          className="w-8 h-8 rounded-lg inline-flex items-center justify-center text-neutral-400 hover:text-neutral-900 dark:hover:text-white"
          aria-label="Back to home"
        >
          ✕
        </Link>
      </div>
      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        {isLogin
          ? "Log in with your recruiter account to run screenings."
          : "Sign up for a recruiter account to run screenings."}
      </p>

      <div className="grid grid-cols-2 gap-1 p-1 rounded-xl bg-neutral-100 dark:bg-black/40 border border-neutral-200 dark:border-neutral-800">
        {(["login", "signup"] as AuthMode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => switchMode(m)}
            className={`py-1.5 text-xs font-semibold rounded-lg transition ${
              mode === m
                ? "bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white shadow-sm"
                : "text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200"
            }`}
          >
            {m === "login" ? "Log in" : "Sign up"}
          </button>
        ))}
      </div>

      <input
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        type="email"
        autoComplete="email"
        placeholder="you@company.com"
        className={INPUT_CLS}
      />
      <input
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        type="password"
        autoComplete={isLogin ? "current-password" : "new-password"}
        placeholder="Password"
        onKeyDown={(e) => e.key === "Enter" && submit()}
        className={INPUT_CLS}
      />
      {error && <p className="text-xs text-red-500 dark:text-red-400">{error}</p>}
      {info && <p className="text-xs text-green-600 dark:text-green-400">{info}</p>}
      <Button
        variant="primary"
        size="none"
        onClick={submit}
        disabled={busy}
        className="w-full py-2 px-4 rounded-xl font-bold text-sm bg-neutral-900 text-white hover:bg-neutral-700 border-neutral-900 dark:bg-white dark:text-black dark:hover:bg-neutral-200 dark:border-white"
      >
        {busy ? "Please wait…" : isLogin ? "Log in" : "Sign up"}
      </Button>
      <Button size="none" onClick={google} className="w-full py-2 px-4 rounded-xl font-semibold text-sm">
        Continue with Google
      </Button>

      <button
        type="button"
        onClick={() => {
          localStorage.setItem("talentlens-demo-user", "aveeck.pandey@gmail.com");
          window.location.href = next.startsWith("/") ? next : "/";
        }}
        className="w-full py-2 px-4 rounded-xl font-semibold text-xs border border-dashed border-neutral-300 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-700 dark:text-neutral-300 transition"
      >
        ⚡ Demo Login as aveeck kumar
      </button>
      <p className="text-xs text-neutral-500 dark:text-neutral-400 text-center">
        <Link href="/" className="underline underline-offset-4 hover:text-neutral-900 dark:hover:text-neutral-200">
          ← Back to dashboard
        </Link>
      </p>
    </div>
  );
}
