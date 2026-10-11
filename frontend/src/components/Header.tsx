"use client";

import { Button } from "./ui";

interface Props {
  userEmail: string | null;
  authConfigured: boolean;
  onLogin: () => void;
  onSignup: () => void;
  onSignOut: () => void;
  onBulkUpload?: () => void;
  onPricing?: () => void;
  isDark?: boolean;
  onToggleTheme?: () => void;
}

export default function Header(p: Props) {
  return (
    <header className="bg-white dark:bg-neutral-950 border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Box 1 (Left): Name and Logo of the project */}
        <div className="flex items-center space-x-3 shrink-0 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
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

          {/* Pricing */}
          <button
            type="button"
            onClick={p.onPricing}
            className="px-3 py-1.5 text-xs font-medium text-neutral-700 dark:text-neutral-300 hover:text-black dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition"
          >
            Pricing
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

          {/* Auth: Log in and Sign up */}
          {p.userEmail ? (
            <div className="flex items-center gap-2">
              <span
                className="hidden sm:inline px-3 py-1 text-xs rounded-full bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 max-w-[180px] truncate"
                title="Signed in"
              >
                {p.userEmail}
              </span>
              <Button variant="navLink" size="md" onClick={p.onSignOut} className="font-medium rounded-full text-xs">
                Sign out
              </Button>
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
