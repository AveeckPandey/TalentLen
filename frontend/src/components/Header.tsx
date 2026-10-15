"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Button } from "./ui";
import type { UserQuota } from "@/lib/types";

interface Props {
  userEmail: string | null;
  authConfigured: boolean;
  onLogin: () => void;
  onSignup: () => void;
  onSignOut: () => void;
  onBulkUpload?: () => void;
  onPricing?: () => void;
  quota?: UserQuota | null;
  isDark?: boolean;
  onToggleTheme?: () => void;
}

export default function Header(p: Props) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const displayName = p.userEmail
    ? p.userEmail.includes("aveeck")
      ? "aveeck kumar"
      : p.userEmail.split("@")[0].replace(/[._-]/g, " ") || "aveeck kumar"
    : "aveeck kumar";

  // Derive initials (e.g. "AK")
  const parts = displayName.trim().split(/\s+/);
  const initials =
    parts.length >= 2
      ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      : displayName.slice(0, 2).toUpperCase() || "AK";

  const credits = p.quota ? p.quota.screenings_remaining : 0;

  return (
    <header className="bg-white dark:bg-neutral-950 border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Box 1 (Left): Name, Logo, and Navigation Links */}
        <div className="flex items-center space-x-6">
          <Link href="/" className="flex items-center space-x-3 shrink-0">
            <img
              src="/logo.png"
              alt="TalentLens logo"
              className="h-10 w-10 rounded-xl object-cover shrink-0 shadow-sm border border-neutral-100 dark:border-neutral-800"
            />
            <div className="min-w-0">
              <h1 className="text-lg font-bold text-neutral-900 dark:text-white tracking-tight flex items-center gap-1.5">
                TalentLens
              </h1>
            </div>
          </Link>

          <nav className="hidden md:flex items-center space-x-4 text-xs font-medium text-neutral-600 dark:text-neutral-300">
            <Link href="/" className="hover:text-black dark:hover:text-white transition">
              Uploads
            </Link>
            <Link href="/dashboard" className="hover:text-black dark:hover:text-white transition">
              Dashboard
            </Link>
          </nav>
        </div>

        {/* Box 2 (Right): Bulk upload, Dark mode, Pricing, and Log in / Sign up */}
        <div className="flex items-center gap-1.5 sm:gap-2.5">
          {/* Bulk upload */}
          <button
            type="button"
            onClick={p.onBulkUpload}
            className="px-3 py-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition flex items-center gap-1.5"
          >
            <svg className="w-3.5 h-3.5 text-neutral-500 dark:text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span>Bulk upload</span>
          </button>

          {/* Pricing & Tier Quota */}
          <button
            type="button"
            onClick={p.onPricing}
            className="px-3 py-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition flex items-center gap-1.5"
          >
            <span>Pricing</span>
            {p.quota && (
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold tracking-tight ${
                  p.quota.tier === "free"
                    ? "bg-blue-100 text-[#0066FF] dark:bg-blue-950 dark:text-blue-400 border border-blue-200 dark:border-blue-900"
                    : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                }`}
              >
                {p.quota.tier === "free" ? "Free" : "Pro"}: {p.quota.screenings_remaining}/{p.quota.screenings_limit}
              </span>
            )}
          </button>

          {/* Dark mode */}
          <button
            type="button"
            onClick={p.onToggleTheme}
            className="px-3 py-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition flex items-center gap-1.5"
            title="Toggle color theme"
          >
            {p.isDark ? (
              <>
                <svg className="w-3.5 h-3.5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
                <span className="hidden sm:inline">Light mode</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <span className="hidden sm:inline">Dark mode</span>
              </>
            )}
          </button>

          <div className="h-4 w-px bg-neutral-200 dark:bg-neutral-800 mx-1 hidden sm:block" />

          {/* Auth: Log in and Sign up OR User Avatar Popover */}
          {p.userEmail ? (
            <div className="flex items-center space-x-2">
              {p.quota?.tier && p.quota.tier !== "free" && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-[#0066FF] text-white shadow-xs tracking-wider uppercase border border-blue-400/30">
                  <span className="text-[10px]">★</span> PRO
                </span>
              )}

              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className={`w-9 h-9 rounded-full bg-neutral-200/90 hover:bg-neutral-300 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-200 font-bold text-xs flex items-center justify-center transition shadow-sm border ${
                    p.quota?.tier && p.quota.tier !== "free"
                      ? "border-[#0066FF] ring-2 ring-blue-500/20"
                      : "border-neutral-300/80 dark:border-neutral-700"
                  } focus:outline-none`}
                  title={`Signed in as ${displayName}`}
                >
                  {initials}
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-2.5 w-60 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-xl p-5 z-50">
                    {/* User Name */}
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-neutral-800 dark:text-neutral-100 truncate">
                        {displayName}
                      </p>
                      {p.quota?.tier && p.quota.tier !== "free" && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#0066FF] text-white uppercase tracking-wider">
                          PRO
                        </span>
                      )}
                    </div>

                  {/* Credits & Subscribe Link */}
                  <div className="mb-4">
                    <p className="text-2xl font-extrabold text-[#A16207] dark:text-amber-400 tracking-tight">
                      {credits} Credit{credits !== 1 ? "s" : ""}
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setDropdownOpen(false);
                        p.onPricing?.();
                      }}
                      className="text-xs font-semibold text-[#0066FF] hover:underline mt-1 block text-left"
                    >
                      Buy Credits or Subscribe
                    </button>
                  </div>

                  {/* Divider */}
                  <div className="h-px bg-neutral-100 dark:bg-neutral-800 my-3" />

                  {/* Menu items */}
                  <div className="space-y-1">
                    <Link
                      href="/dashboard"
                      onClick={() => setDropdownOpen(false)}
                      className="block w-full text-left px-2 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800/60 rounded-xl transition font-medium"
                    >
                      Screening Dashboard
                    </Link>
                    <Link
                      href="/account"
                      onClick={() => setDropdownOpen(false)}
                      className="block w-full text-left px-2 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800/60 rounded-xl transition font-medium"
                    >
                      My Account
                    </Link>
                    <button
                      type="button"
                      onClick={() => {
                        setDropdownOpen(false);
                        p.onSignOut();
                      }}
                      className="block w-full text-left px-2 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800/60 rounded-xl transition font-medium"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
            <div className="flex items-center gap-1.5 sm:gap-2">
              <Button
                variant="navLink"
                size="md"
                onClick={p.onLogin}
                className="font-medium rounded-full text-xs text-neutral-600 dark:text-neutral-300 hover:text-black dark:hover:text-white"
              >
                Log in
              </Button>
              <Button
                variant="pill"
                size="md"
                onClick={p.onSignup}
                className="font-medium rounded-full px-4 text-xs bg-neutral-100 dark:bg-white text-neutral-900 dark:text-black hover:bg-neutral-200 shadow-sm"
              >
                Sign up
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
