"use client";

import { useEffect, useState } from "react";
import { getSupabaseClient } from "@/lib/supabase";
import { Button, Modal } from "./ui";

export type AuthMode = "login" | "signup";

const INPUT_CLS =
  "w-full px-3 py-2 text-sm rounded-lg bg-black border border-neutral-700 text-white placeholder-neutral-500 outline-none focus:border-neutral-400";

interface AuthModalProps {
  open: boolean;
  initialMode?: AuthMode;
  onClose: () => void;
  onAuthed: () => void;
}

export default function AuthModal({ open, initialMode = "login", onClose, onAuthed }: AuthModalProps) {
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  useEffect(() => {
    if (open) {
      setMode(initialMode);
      setError("");
      setInfo("");
    }
  }, [open, initialMode]);

  async function signIn() {
    const sb = getSupabaseClient();
    if (!sb) return setError("Auth not configured. Set NEXT_PUBLIC_SUPABASE_URL + ANON_KEY and restart.");
    setError(""); setInfo("");
    const { error } = await sb.auth.signInWithPassword({ email: email.trim(), password });
    if (error) return setError(error.message);
    onAuthed(); onClose();
  }

  async function signUp() {
    const sb = getSupabaseClient();
    if (!sb) return setError("Auth not configured.");
    setError(""); setInfo("");
    const { error } = await sb.auth.signUp({ email: email.trim(), password });
    if (error) return setError(error.message);
    setInfo("Account created — check your email to confirm, then log in.");
  }

  async function google() {
    const sb = getSupabaseClient();
    if (!sb) return setError("Auth not configured.");
    await sb.auth.signInWithOAuth({ provider: "google", options: { redirectTo: window.location.origin } });
  }

  const isLogin = mode === "login";
  const submit = isLogin ? signIn : signUp;

  return (
    <Modal open={open} onClose={onClose} panelClassName="max-w-sm" overlayClassName="bg-black/80" zClassName="z-[60]">
      <div className="w-full bg-neutral-900 border border-neutral-700 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white">
            {isLogin ? "Welcome back" : "Create your account"}
          </h3>
          <Button size="none" onClick={onClose} className="w-8 h-8 rounded-lg text-neutral-400 hover:text-white">✕</Button>
        </div>
        <p className="text-xs text-neutral-400">
          {isLogin
            ? "Log in with your recruiter account to run screenings."
            : "Sign up for a recruiter account to run screenings."}
        </p>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="you@company.com" className={INPUT_CLS} />
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Password" onKeyDown={(e) => e.key === "Enter" && submit()} className={INPUT_CLS} />
        {error && <p className="text-xs text-red-400">{error}</p>}
        {info && <p className="text-xs text-green-400">{info}</p>}
        <Button variant="primary" size="none" onClick={submit} className="w-full py-2 px-4 rounded-xl font-bold text-sm">
          {isLogin ? "Log in" : "Sign up"}
        </Button>
        <Button size="none" onClick={google} className="w-full py-2 px-4 rounded-xl font-semibold text-sm">Continue with Google</Button>
        <p className="text-xs text-neutral-400 text-center">
          {isLogin ? (
            <>New here? <Button variant="link" size="none" onClick={() => { setMode("signup"); setError(""); setInfo(""); }} className="text-xs text-neutral-200">Create an account</Button></>
          ) : (
            <>Have an account? <Button variant="link" size="none" onClick={() => { setMode("login"); setError(""); setInfo(""); }} className="text-xs text-neutral-200">Log in</Button></>
          )}
        </p>
      </div>
    </Modal>
  );
}
