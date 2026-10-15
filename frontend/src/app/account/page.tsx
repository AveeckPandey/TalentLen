"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import Footer from "@/components/Footer";
import PricingModal from "@/components/PricingModal";
import { getSupabaseClient } from "@/lib/supabase";
import {
  getUserQuota,
  listUserApiKeys,
  createUserApiKey,
  deleteUserApiKey,
} from "@/lib/api";
import { openRazorpayCheckout } from "@/lib/razorpay";
import type { UserQuota, PlanTier, ApiKeyItem, CreateApiKeyResponse } from "@/lib/types";

type AccountTab = "credits" | "billing" | "api_keys" | "settings";

export default function AccountDashboardPage() {
  const [activeTab, setActiveTab] = useState<AccountTab>("api_keys");
  const [pricingOpen, setPricingOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>("aveeck.pandey@gmail.com");
  const [displayName, setDisplayName] = useState<string>("aveeck kumar");
  const [quota, setQuota] = useState<UserQuota | null>(null);
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  const [newKeyModalOpen, setNewKeyModalOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<CreateApiKeyResponse | null>(null);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [isDark, setIsDark] = useState(false);

  // Live API keys state
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);

  const dropdownRef = useRef<HTMLDivElement>(null);

  function refreshKeys() {
    setLoadingKeys(true);
    listUserApiKeys()
      .then((keys) => setApiKeys(keys))
      .catch((err) => console.error("Failed to fetch API keys:", err))
      .finally(() => setLoadingKeys(false));
  }

  function refreshQuota() {
    getUserQuota()
      .then((q) => setQuota(q))
      .catch(() => {});
  }

  useEffect(() => {
    // Check Supabase session if active
    const sb = getSupabaseClient();
    if (sb) {
      sb.auth.getSession().then(({ data }) => {
        if (data.session?.user?.email) {
          setUserEmail(data.session.user.email);
          if (!data.session.user.email.includes("aveeck")) {
            setDisplayName(data.session.user.email.split("@")[0].replace(/[._-]/g, " "));
          }
        }
      });
    }

    refreshQuota();
    refreshKeys();

    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const credits = quota ? quota.screenings_remaining : 0;

  // Derive initials
  const parts = displayName.trim().split(/\s+/);
  const initials =
    parts.length >= 2
      ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      : displayName.slice(0, 2).toUpperCase() || "AK";

  async function handleCreateApiKey(e: React.FormEvent) {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await createUserApiKey(newKeyName.trim());
      setCreatedKey(res);
      setNewKeyName("");
      refreshKeys();
    } catch (err: any) {
      alert("Failed to create API key: " + err.message);
    }
  }

  async function handleDeleteKey(keyId: string) {
    if (!confirm("Are you sure you want to permanently delete this API key? This action cannot be undone and any applications using it will immediately lose access.")) {
      return;
    }
    try {
      await deleteUserApiKey(keyId);
      refreshKeys();
    } catch (err: any) {
      alert("Failed to delete API key: " + err.message);
    }
  }

  function handleCopyKey(id: string, text: string) {
    navigator.clipboard.writeText(text);
    setCopiedKeyId(id);
    setTimeout(() => setCopiedKeyId(null), 2000);
  }

  async function handleSignOut() {
    const sb = getSupabaseClient();
    if (sb) {
      await sb.auth.signOut();
    }
    window.location.href = "/";
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 flex flex-col font-sans transition-colors">
      {/* 1. Top Notice Bar matching Image 2 */}
      <div className="bg-[#DBEAFE] dark:bg-blue-950/70 border-b border-blue-200 dark:border-blue-900/50 py-2.5 px-4 text-xs text-neutral-800 dark:text-neutral-200 text-center leading-relaxed">
        <span>
          TalentLens AI candidate intelligence and deep project ranking are now live. Explore API integrations with your ATS. You can{" "}
          <a
            href="https://portfolio.buildwithaveeck.com/"
            target="_blank"
            rel="noreferrer"
            className="text-[#0066FF] hover:underline font-semibold"
          >
            learn more here
          </a>
          , and visit our{" "}
          <a href="#" className="text-[#0066FF] hover:underline font-semibold">
            API Documentation
          </a>
          .
        </span>
      </div>

      {/* 2. Top Navigation Bar matching Image 2 */}
      <header className="bg-white dark:bg-neutral-950 border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-40 transition-colors shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Navigation Links */}
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-3 shrink-0">
              <img
                src="/logo.png"
                alt="TalentLens logo"
                className="h-9 w-9 rounded-xl object-cover shrink-0 shadow-sm border border-neutral-100 dark:border-neutral-800"
              />
              <span className="text-lg font-bold text-neutral-900 dark:text-white tracking-tight">
                TalentLens
              </span>
            </Link>

            <nav className="hidden md:flex items-center space-x-6 text-xs font-medium text-neutral-600 dark:text-neutral-300">
              <Link href="/" className="hover:text-black dark:hover:text-white transition">
                Uploads
              </Link>
              <Link href="/dashboard" className="hover:text-black dark:hover:text-white transition">
                Screening
              </Link>
              <button
                type="button"
                onClick={() => setActiveTab("api_keys")}
                className="hover:text-black dark:hover:text-white transition"
              >
                API
              </button>
              <button
                type="button"
                onClick={() => setPricingOpen(true)}
                className="hover:text-black dark:hover:text-white transition"
              >
                Pricing
              </button>
            </nav>
          </div>

          {/* User Avatar Circle (matching Image 1 & 2) with Popover */}
          <div className="flex items-center space-x-2.5">
            {quota?.tier && quota.tier !== "free" && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-[#0066FF] text-white shadow-xs tracking-wider uppercase border border-blue-400/30">
                <span className="text-[10px]">★</span> PRO
              </span>
            )}

            <button
              type="button"
              onClick={() => setPricingOpen(true)}
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700 transition"
            >
              {quota ? `${quota.screenings_remaining} Credits` : "30 Credits"}
            </button>

            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className={`w-10 h-10 rounded-full bg-neutral-200/90 hover:bg-neutral-300 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-200 font-bold text-xs flex items-center justify-center transition shadow-sm border ${
                  quota?.tier && quota.tier !== "free"
                    ? "border-[#0066FF] ring-2 ring-blue-500/20"
                    : "border-neutral-300/80 dark:border-neutral-700"
                } focus:outline-none`}
                title={displayName}
              >
                {initials}
              </button>

              {/* Popover matching Image 1 */}
              {dropdownOpen && (
                <div className="absolute right-0 mt-2.5 w-60 rounded-2xl bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 shadow-xl p-5 z-50 animate-in fade-in zoom-in-95 duration-100">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-sm font-semibold text-neutral-800 dark:text-neutral-100 truncate">
                      {displayName}
                    </p>
                    {quota?.tier && quota.tier !== "free" && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#0066FF] text-white uppercase tracking-wider">
                        PRO
                      </span>
                    )}
                  </div>

                  <div className="mb-4">
                    <p className="text-2xl font-extrabold text-[#A16207] dark:text-amber-400 tracking-tight">
                      {credits} Credit{credits !== 1 ? "s" : ""}
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setDropdownOpen(false);
                        setPricingOpen(true);
                      }}
                      className="text-xs font-semibold text-[#0066FF] hover:underline mt-1 block text-left"
                    >
                      Buy Credits or Subscribe
                    </button>
                  </div>

                  <div className="h-px bg-neutral-100 dark:bg-neutral-800 my-3" />

                  <div className="space-y-1">
                    <button
                      type="button"
                      onClick={() => {
                        setDropdownOpen(false);
                        setActiveTab("settings");
                      }}
                      className="block w-full text-left px-2 py-2 text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800/60 rounded-xl transition font-medium"
                    >
                      My Account
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setDropdownOpen(false);
                        handleSignOut();
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
        </div>
      </header>

      {/* 3. Hero Header Banner matching Image 2 */}
      <div className="relative overflow-hidden bg-gradient-to-r from-[#70B4FF] via-[#7BB3F5] to-[#7BD3AE] py-16 md:py-20 text-center select-none shadow-inner">
        {/* Decorative background shapes matching Image 2 */}
        <div className="absolute top-1/2 left-6 md:left-12 -translate-y-1/2 w-16 h-16 md:w-24 md:h-24 rounded-full bg-white/20 blur-xs pointer-events-none" />
        <div className="absolute top-8 right-12 md:right-24 w-0 h-0 border-l-[28px] border-l-transparent border-r-[28px] border-r-transparent border-b-[50px] border-b-white/25 pointer-events-none transform rotate-12" />

        <div className="relative z-10 max-w-4xl mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight drop-shadow-xs">
            My Dashboard
          </h1>
          <p className="text-white/90 text-sm md:text-base font-medium mt-2 tracking-wide">
            {displayName}
          </p>
        </div>
      </div>

      {/* 4. Overlapping Main Content Card matching Image 2 */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 w-full -mt-10 md:-mt-12 relative z-20 pb-16">
        <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl border border-neutral-200/90 dark:border-neutral-800 overflow-hidden">
          {/* Horizontal Tab Bar matching Image 2 */}
          <div className="flex border-b border-neutral-200 dark:border-neutral-800 overflow-x-auto scrollbar-none bg-neutral-50/50 dark:bg-neutral-900">
            <button
              onClick={() => setActiveTab("credits")}
              className={`px-5 py-3.5 text-xs md:text-sm font-semibold whitespace-nowrap transition border-t-2 -mt-[1px] ${
                activeTab === "credits"
                  ? "border-[#0066FF] text-[#0066FF] bg-white dark:bg-neutral-900"
                  : "border-transparent text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
              }`}
            >
              Credits & Plan
            </button>
            <button
              onClick={() => setActiveTab("billing")}
              className={`px-5 py-3.5 text-xs md:text-sm font-semibold whitespace-nowrap transition border-t-2 -mt-[1px] ${
                activeTab === "billing"
                  ? "border-[#0066FF] text-[#0066FF] bg-white dark:bg-neutral-900"
                  : "border-transparent text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
              }`}
            >
              Payment & Billing
            </button>
            <button
              onClick={() => setActiveTab("api_keys")}
              className={`px-5 py-3.5 text-xs md:text-sm font-semibold whitespace-nowrap transition border-t-2 -mt-[1px] ${
                activeTab === "api_keys"
                  ? "border-[#0066FF] text-[#0066FF] bg-white dark:bg-neutral-900"
                  : "border-transparent text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
              }`}
            >
              API Keys
            </button>
            <button
              onClick={() => setActiveTab("settings")}
              className={`px-5 py-3.5 text-xs md:text-sm font-semibold whitespace-nowrap transition border-t-2 -mt-[1px] ${
                activeTab === "settings"
                  ? "border-[#0066FF] text-[#0066FF] bg-white dark:bg-neutral-900"
                  : "border-transparent text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white"
              }`}
            >
              Account Settings
            </button>
          </div>

          {/* TAB 1: CREDITS & PLAN */}
          {activeTab === "credits" && (
            <div className="p-6 md:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-xl bg-blue-50/70 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/50">
                <div>
                  <span className="text-xs uppercase font-bold text-blue-600 dark:text-blue-400 tracking-wider">
                    Current Active Tier
                  </span>
                  <h3 className="text-xl font-extrabold text-neutral-900 dark:text-white mt-0.5">
                    {quota?.tier_display_name || "Starter (Free)"}
                  </h3>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                    {quota?.tier === "pro_29"
                      ? "Pro Tier with 30 screening runs & 100 resumes per batch."
                      : "Starter free plan with 3 screening runs & 50 resumes per batch."}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setPricingOpen(true)}
                  className="px-5 py-2.5 rounded-full text-xs font-bold text-white bg-[#0066FF] hover:bg-blue-600 shadow-md transition shrink-0"
                >
                  Buy Credits or Subscribe
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/60 dark:bg-neutral-900">
                  <span className="text-xs text-neutral-500 block">Remaining Credits</span>
                  <span className="text-2xl font-black text-[#A16207] dark:text-amber-400">
                    {credits}
                  </span>
                </div>
                <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/60 dark:bg-neutral-900">
                  <span className="text-xs text-neutral-500 block">Max Resumes / Batch</span>
                  <span className="text-2xl font-black text-neutral-900 dark:text-white">
                    {quota?.max_resumes_per_batch ?? 50}
                  </span>
                </div>
                <div className="p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/60 dark:bg-neutral-900">
                  <span className="text-xs text-neutral-500 block">AI Intelligence</span>
                  <span className="text-2xl font-black text-blue-600 dark:text-blue-400">
                    Groq Fast
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PAYMENT & BILLING */}
          {activeTab === "billing" && (
            <div className="p-6 md:p-8 space-y-6">
              <div>
                <h3 className="text-base font-bold text-neutral-900 dark:text-white">Payment Method</h3>
                <p className="text-xs text-neutral-500 mt-0.5">Manage your stored payment methods for recurring subscriptions.</p>
              </div>

              <div className="flex items-center justify-between p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-900">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-6 rounded bg-neutral-200 dark:bg-neutral-800 flex items-center justify-center font-mono text-[10px] font-bold">
                    CARD
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 block">
                      Visa ending in •••• 4242
                    </span>
                    <span className="text-[11px] text-neutral-500">Expires 12/28</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setPricingOpen(true)}
                  className="text-xs font-semibold text-[#0066FF] hover:underline"
                >
                  Update
                </button>
              </div>

              <div className="pt-4 border-t border-neutral-200 dark:border-neutral-800">
                <h4 className="text-sm font-bold text-neutral-900 dark:text-white mb-2">Billing History</h4>
                <div className="text-xs text-neutral-500 py-6 text-center border border-dashed border-neutral-200 dark:border-neutral-800 rounded-xl">
                  No invoices yet. Upgraded plans will generate downloadable receipts here.
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: API KEYS (MATCHING IMAGE 2 EXACTLY) */}
          {activeTab === "api_keys" && (
            <div className="p-6 md:p-8 space-y-6">
              {/* Top description and Action Button matching Image 2 */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <p className="text-xs md:text-sm text-neutral-700 dark:text-neutral-300 max-w-xl leading-relaxed">
                  API Keys let you use TalentLens from within other tools or your own software. Check out our{" "}
                  <a href="#tools" className="text-[#0066FF] underline font-medium">
                    list of tools
                  </a>{" "}
                  and{" "}
                  <a href="#api" className="text-[#0066FF] underline font-medium">
                    API
                  </a>{" "}
                  to see what you can do!
                </p>

                <button
                  type="button"
                  onClick={() => setNewKeyModalOpen(true)}
                  className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-full text-xs font-bold text-white bg-[#0066FF] hover:bg-blue-600 transition shadow-sm shrink-0"
                >
                  <span>+ New API Key</span>
                </button>
              </div>

              {/* API Keys Table */}
              <div className="border border-neutral-200 dark:border-neutral-800 rounded-xl overflow-hidden">
                <div className="bg-neutral-50/70 dark:bg-neutral-800/50 px-4 py-2.5 border-b border-neutral-200 dark:border-neutral-800 text-[11px] font-bold text-neutral-500 uppercase tracking-wider flex justify-between">
                  <span>Key Name & Secret</span>
                  <span>Actions</span>
                </div>
                <div className="divide-y divide-neutral-200 dark:divide-neutral-800 text-xs">
                  {loadingKeys ? (
                    <div className="p-6 text-center text-xs text-neutral-400">Loading API keys...</div>
                  ) : apiKeys.length === 0 ? (
                    <div className="p-8 text-center text-xs text-neutral-500 space-y-2">
                      <p>No active API keys found.</p>
                      <button
                        type="button"
                        onClick={() => setNewKeyModalOpen(true)}
                        className="text-[#0066FF] hover:underline font-semibold"
                      >
                        + Create your first API key
                      </button>
                    </div>
                  ) : (
                    apiKeys.map((item) => (
                      <div key={item.key_id} className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white dark:bg-neutral-900">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-neutral-900 dark:text-white">{item.name}</span>
                            <span className="text-[10px] text-neutral-400">
                              • Created {item.created_at ? new Date(item.created_at).toLocaleDateString() : "Active"}
                            </span>
                          </div>
                          <div className="mt-1 flex items-center space-x-2">
                            <code className="bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 px-2 py-0.5 rounded font-mono text-[11px]">
                              {item.key_prefix}
                            </code>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleDeleteKey(item.key_id)}
                          className="px-2.5 py-1 text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg transition"
                          title="Permanently delete this key"
                        >
                          Delete
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Developer API Documentation & cURL Showcase */}
              <div className="mt-8 pt-8 border-t border-neutral-200 dark:border-neutral-800">
                <div className="text-center mb-6">
                  <h4 className="text-sm font-bold text-neutral-900 dark:text-white">
                    TalentLens Developer Public API
                  </h4>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    Integrate automated candidate screening into Greenhouse, Lever, ATS platforms, or custom scripts.
                  </p>
                  <span className="inline-block mt-2 text-[10px] px-2.5 py-0.5 rounded-full bg-blue-50 text-[#0066FF] dark:bg-blue-950/60 dark:text-blue-400 font-semibold border border-blue-200 dark:border-blue-900">
                    Rate Limit: 5 requests / minute
                  </span>
                </div>

                <div className="bg-neutral-50 dark:bg-neutral-950 p-4 rounded-xl border border-neutral-200 dark:border-neutral-800 font-mono text-[11px] text-neutral-700 dark:text-neutral-300 overflow-x-auto">
                  <span className="text-neutral-400 block mb-1"># Public Developer API (Multipart Upload):</span>
                  <code>
                    curl -X POST http://127.0.0.1:8000/api/v1/screen \<br />
                    &nbsp;&nbsp;-H &quot;X-API-Key: {apiKeys[0]?.key_prefix || "tl_test_your_key_here"}&quot; \<br />
                    &nbsp;&nbsp;-F &quot;files=@candidate_resume.pdf&quot; \<br />
                    &nbsp;&nbsp;-F &quot;target_role=Python Developer&quot;
                  </code>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: ACCOUNT SETTINGS */}
          {activeTab === "settings" && (
            <div className="p-6 md:p-8 space-y-6">
              <div>
                <h3 className="text-base font-bold text-neutral-900 dark:text-white">Account Details</h3>
                <p className="text-xs text-neutral-500 mt-0.5">Manage your contact information and preferences.</p>
              </div>

              <div className="space-y-4 max-w-md">
                <div>
                  <label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 block mb-1">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-800 dark:text-neutral-200 outline-none focus:border-[#0066FF]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 block mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={userEmail || ""}
                    onChange={(e) => setUserEmail(e.target.value)}
                    className="w-full text-xs px-3 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-950 text-neutral-800 dark:text-neutral-200 outline-none focus:border-[#0066FF]"
                  />
                </div>

                <button
                  type="button"
                  onClick={() => alert("Profile updated!")}
                  className="px-5 py-2 rounded-full text-xs font-bold text-white bg-[#0066FF] hover:bg-blue-600 transition shadow-sm"
                >
                  Save Changes
                </button>
              </div>

              <div className="pt-6 border-t border-neutral-200 dark:border-neutral-800">
                <h4 className="text-xs font-bold text-red-600 uppercase tracking-wider mb-2">Danger Zone</h4>
                <p className="text-xs text-neutral-500 mb-3">
                  Deleting your account will purge your screening history and stored resume analyses permanently.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    if (confirm("Are you sure you want to delete your account?")) {
                      handleSignOut();
                    }
                  }}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-red-600 bg-red-50 hover:bg-red-100 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 transition"
                >
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* New API Key Modal */}
      {newKeyModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            {createdKey ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400">
                  <span className="text-lg">✓</span>
                  <h3 className="text-base font-bold text-neutral-900 dark:text-white">API Key Created!</h3>
                </div>
                <p className="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 p-2.5 rounded-lg">
                  ⚠️ <strong>Save this key now!</strong> For security, this is the only time the full secret token will ever be displayed.
                </p>

                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block">
                    Secret API Key
                  </span>
                  <div className="flex items-center space-x-2 bg-neutral-100 dark:bg-neutral-950 border border-neutral-200 dark:border-neutral-800 rounded-lg p-2.5">
                    <code className="text-xs font-mono text-neutral-900 dark:text-white flex-1 break-all select-all">
                      {createdKey.api_key}
                    </code>
                    <button
                      type="button"
                      onClick={() => handleCopyKey("new_key_secret", createdKey.api_key)}
                      className="px-3 py-1 bg-[#0066FF] hover:bg-blue-600 text-white rounded-md text-xs font-bold shrink-0 transition"
                    >
                      {copiedKeyId === "new_key_secret" ? "Copied!" : "Copy"}
                    </button>
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setCreatedKey(null);
                      setNewKeyModalOpen(false);
                    }}
                    className="px-4 py-2 rounded-lg text-xs font-bold text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <h3 className="text-base font-bold text-neutral-900 dark:text-white mb-1">Create New API Key</h3>
                <p className="text-xs text-neutral-500 mb-4">Give your key a descriptive name to identify its integration.</p>

                <form onSubmit={handleCreateApiKey} className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-neutral-700 dark:text-neutral-300 block mb-1">
                      Key Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. ATS Integration, Zapier, Python Script"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-950 outline-none focus:border-[#0066FF]"
                      autoFocus
                    />
                  </div>

                  <div className="flex items-center justify-end space-x-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setNewKeyModalOpen(false)}
                      className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={!newKeyName.trim()}
                      className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-[#0066FF] hover:bg-blue-600 disabled:opacity-50 transition"
                    >
                      Create Key
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pricing Modal */}
      <PricingModal
        open={pricingOpen}
        onClose={() => setPricingOpen(false)}
        onSelectPlan={async (plan) => {
          if (plan === "pro_29") {
            await openRazorpayCheckout({
              tier: "pro_29",
              userEmail: userEmail,
              onSuccess: (upgraded) => {
                setQuota(upgraded);
                alert("Payment verified successfully! Your account has been upgraded to Recruiter Pro (₹2,499 / $29). 30 screening runs & up to 100 resumes per batch unlocked.");
              },
              onError: (e) => {
                alert("Payment failed or cancelled: " + e.message);
              },
            });
          }
        }}
      />

      {/* Footer with remove.bg style blue wave */}
      <Footer />
    </div>
  );
}
