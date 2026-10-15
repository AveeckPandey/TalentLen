"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Header from "@/components/Header";
import BatchSummaryCards from "@/components/BatchSummary";
import CandidateCard from "@/components/CandidateCard";
import ResumeModal from "@/components/ResumeModal";
import PricingModal from "@/components/PricingModal";
import LoadingOverlay from "@/components/LoadingOverlay";
import Footer from "@/components/Footer";
import { openRazorpayCheckout } from "@/lib/razorpay";
import {
  Button,
  Card,
  SearchInput,
  SegmentedControl,
  Tabs,
} from "@/components/ui";
import {
  clearSession,
  exportFilteredCsv,
  exportFilteredDocx,
  exportFilteredExcel,
  exportFilteredJson,
  getResults,
  screenSampleResumes,
  uploadAndScreen,
  getUserQuota,
  listScreeningHistory,
  loadScreeningHistory,
  deleteScreeningHistory,
} from "@/lib/api";
import { getSupabaseClient } from "@/lib/supabase";
import type {
  ActiveTab,
  CandidateResult,
  ScreeningReport,
  TopNLimit,
  UserQuota,
  ScreeningHistoryItem,
} from "@/lib/types";

const TOPN_OPTIONS: { value: TopNLimit; label: string }[] = [
  { value: "all", label: "All" },
  { value: 5, label: "Top 5" },
  { value: 10, label: "Top 10" },
  { value: 20, label: "Top 20" },
];

export default function CandidateDashboardPage() {
  const router = useRouter();
  const [report, setReport] = useState<ScreeningReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("eligible");
  const [cutoff, setCutoff] = useState(0);
  const [topN, setTopN] = useState<TopNLimit>("all");
  const [query, setQuery] = useState("");
  const [preview, setPreview] = useState<CandidateResult | null>(null);

  const [pricingOpen, setPricingOpen] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const [userEmail, setUserEmail] = useState<string | null>("aveeck.pandey@gmail.com");
  const [quota, setQuota] = useState<UserQuota | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Previous shortlistings state
  const [history, setHistory] = useState<ScreeningHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showHistory, setShowHistory] = useState(true);

  const authConfigured = Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
      (process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
        process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY)
  );

  async function refreshQuota() {
    try {
      const q = await getUserQuota();
      setQuota(q);
    } catch {
      /* local dev fallback */
    }
  }

  async function refreshHistory() {
    try {
      setLoadingHistory(true);
      const items = await listScreeningHistory();
      setHistory(items);
    } catch (e) {
      console.error("Failed to load history:", e);
    } finally {
      setLoadingHistory(false);
    }
  }

  async function handleLoadHistory(batchId: string) {
    setBusy(true);
    setLoadingMsg("Loading previous shortlisting batch…");
    try {
      const past = await loadScreeningHistory(batchId);
      setReport(past);
      setActiveTab("eligible");
    } catch (e: any) {
      alert("Failed to load shortlist: " + e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteHistory(batchId: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to remove this shortlisting from your history?")) return;
    try {
      await deleteScreeningHistory(batchId);
      setHistory((prev) => prev.filter((h) => h.batch_id !== batchId));
    } catch (err: any) {
      alert("Failed to delete record: " + err.message);
    }
  }

  useEffect(() => {
    // Theme initialization (defaults to dark mode)
    const saved = typeof window !== "undefined" ? localStorage.getItem("talentlens-theme") : null;
    const initialDark = saved !== null ? saved === "dark" : true;
    setIsDark(initialDark);
    if (initialDark) {
      document.documentElement.classList.add("dark");
      document.body.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
      document.body.classList.remove("dark");
    }

    refreshQuota();
    refreshHistory();

    // Check for existing session report
    getResults().then((existing) => {
      if (existing) {
        setReport(existing);
      }
    });

    const sb = getSupabaseClient();
    if (sb) {
      sb.auth.getSession().then(({ data }) => {
        if (data.session?.user?.email) {
          setUserEmail(data.session.user.email);
        }
        refreshQuota();
      });
      const { data: sub } = sb.auth.onAuthStateChange((_ev, session) => {
        if (session?.user?.email) {
          setUserEmail(session.user.email);
        }
        refreshQuota();
      });
      return () => sub.subscription.unsubscribe();
    }
  }, []);

  function toggleTheme() {
    setIsDark((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        localStorage.setItem("talentlens-theme", next ? "dark" : "light");
        if (next) {
          document.documentElement.classList.add("dark");
          document.body.classList.add("dark");
        } else {
          document.documentElement.classList.remove("dark");
          document.body.classList.remove("dark");
        }
      }
      return next;
    });
  }

  async function runSample() {
    setBusy(true);
    setLoadingMsg("Screening 50 sample engineering resumes with Groq intelligence…");
    try {
      const r = await screenSampleResumes();
      setReport(r);
      setActiveTab("eligible");
      refreshQuota();
      refreshHistory();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      refreshQuota();
      if (msg.includes("limit reached") || msg.includes("Upgrade to Recruiter Pro") || msg.includes("403")) {
        setPricingOpen(true);
      }
      alert("Error screening resumes: " + msg);
    } finally {
      setBusy(false);
    }
  }

  async function runUpload(files: File[]) {
    if (files.length === 0) return runSample();
    setBusy(true);
    setLoadingMsg(`Parsing, evaluating & ranking ${files.length} candidate resume(s)…`);
    try {
      const r = await uploadAndScreen(files);
      setReport(r);
      setActiveTab("eligible");
      refreshQuota();
      refreshHistory();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      refreshQuota();
      if (msg.includes("limit reached") || msg.includes("Upgrade to Recruiter Pro") || msg.includes("403")) {
        setPricingOpen(true);
      }
      alert("Upload failed: " + msg);
    } finally {
      setBusy(false);
    }
  }

  async function handleClear() {
    if (confirm("Reset current screening session? This clears the in-memory results.")) {
      await clearSession();
      setReport(null);
      setQuery("");
      setCutoff(0);
      setTopN("all");
    }
  }

  function handleFileDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter((f) =>
      /\.(pdf|docx|txt|doc)$/i.test(f.name)
    );
    if (droppedFiles.length > 0) {
      runUpload(droppedFiles);
    }
  }

  function handleFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      runUpload(Array.from(e.target.files));
    }
  }

  const filtered = useMemo(() => {
    if (!report) return [];
    let list =
      activeTab === "eligible" ? [...report.ranked_candidates] : [...report.rejected_candidates];
    if (activeTab === "eligible" && cutoff > 0) list = list.filter((c) => c.total_score >= cutoff);
    const q = query.toLowerCase().trim();
    if (q) {
      list = list.filter(
        (c) =>
          c.candidate_name.toLowerCase().includes(q) ||
          (c.email || "").toLowerCase().includes(q) ||
          (c.phone || "").toLowerCase().includes(q) ||
          (c.matched_skills || []).some((s) => s.toLowerCase().includes(q)) ||
          (c.rejection_reasons || []).some((r) => r.toLowerCase().includes(q))
      );
    }
    if (activeTab === "eligible" && typeof topN === "number") {
      list = list.slice(0, topN);
    }
    return list;
  }, [report, activeTab, cutoff, topN, query]);

  const avgEligible = useMemo(() => {
    if (!report || report.ranked_candidates.length === 0) return 0;
    const subset =
      cutoff > 0 ? report.ranked_candidates.filter((c) => c.total_score >= cutoff) : report.ranked_candidates;
    if (subset.length === 0) return 0;
    const sum = subset.reduce((acc, c) => acc + c.total_score, 0);
    return Math.round((sum / subset.length) * 10) / 10;
  }, [report, cutoff]);

  const scopeLabel = useMemo(() => {
    if (activeTab === "rejected") return "Disqualified";
    if (typeof topN === "number") return `Top ${topN}`;
    return cutoff > 0 ? `Cutoff >= ${cutoff}` : "All Eligible";
  }, [activeTab, topN, cutoff]);

  const exportBadge = typeof topN === "number" ? `Top ${topN}` : "All";

  async function withBusy(msg: string, fn: () => Promise<void> | void) {
    setBusy(true);
    setLoadingMsg(msg);
    try {
      await fn();
    } catch (e: unknown) {
      alert("Export failed: " + (e instanceof Error ? e.message : String(e)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black text-neutral-900 dark:text-neutral-100 flex flex-col font-sans transition-colors">
      <Header
        userEmail={userEmail}
        authConfigured={authConfigured}
        onLogin={() => router.push("/login?mode=login")}
        onSignup={() => router.push("/login?mode=signup")}
        onSignOut={async () => {
          if (typeof window !== "undefined") {
            localStorage.removeItem("talentlens-demo-user");
          }
          await getSupabaseClient()?.auth.signOut();
          setUserEmail(null);
        }}
        onBulkUpload={() => {
          const el = document.getElementById("dashboard-uploader");
          el?.scrollIntoView({ behavior: "smooth" });
        }}
        onPricing={() => setPricingOpen(true)}
        quota={quota}
        isDark={isDark}
        onToggleTheme={toggleTheme}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 flex-1 w-full">
        {/* Top Breadcrumb & Page Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-neutral-200 dark:border-neutral-800">
          <div>
            <div className="flex items-center space-x-2 text-xs text-neutral-400 mb-1">
              <Link href="/" className="hover:text-blue-500 transition">Home</Link>
              <span>/</span>
              <span className="text-neutral-700 dark:text-neutral-300 font-semibold">Candidate Screening Dashboard</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-900 dark:text-white">
              Candidate Analysis &amp; Ranking
            </h1>
            <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">
              Automated 100-point explainable scoring, Groq project depth analysis &amp; GitHub verification.
            </p>
          </div>

          <div className="flex items-center space-x-2.5">
            <Button
              size="sm"
              variant="dark"
              onClick={runSample}
              disabled={busy}
              className="text-xs font-semibold rounded-xl bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-700"
            >
              ⚡ Screen 50 Sample Resumes
            </Button>
            <label className="cursor-pointer inline-flex items-center justify-center px-3.5 py-1.5 text-xs font-bold rounded-xl bg-[#0066FF] hover:bg-blue-600 text-white transition shadow-sm">
              <span>+ Upload Batch</span>
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={handleFileInputChange}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Previous Shortlistings Section */}
        {history.length > 0 && (
          <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl p-4 sm:p-5 shadow-xs transition">
            <div
              className="flex items-center justify-between cursor-pointer select-none"
              onClick={() => setShowHistory(!showHistory)}
            >
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950/60 flex items-center justify-center text-sm text-[#0066FF]">
                  📜
                </div>
                <div>
                  <h3 className="text-sm font-bold text-neutral-900 dark:text-white flex items-center gap-2">
                    Previous Shortlistings
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-100 dark:bg-blue-950 text-[#0066FF] dark:text-blue-400">
                      {history.length}
                    </span>
                  </h3>
                  <p className="text-[11px] text-neutral-500">
                    Switch between past screening batches or restore archived candidate rankings.
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="text-xs font-semibold text-neutral-500 hover:text-black dark:hover:text-white transition px-2 py-1 rounded"
              >
                {showHistory ? "Hide ▲" : "Show ▼"}
              </button>
            </div>

            {showHistory && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-3 border-t border-neutral-100 dark:border-neutral-800">
                {history.map((item) => (
                  <div
                    key={item.batch_id}
                    className="p-3.5 rounded-xl border border-neutral-200/90 dark:border-neutral-800 bg-neutral-50/60 dark:bg-neutral-950 hover:border-[#0066FF] transition flex flex-col justify-between gap-3 group"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-bold text-xs text-neutral-900 dark:text-white line-clamp-1">
                          {item.target_role || "Python Developer"}
                        </span>
                        <span className="text-[10px] font-mono text-neutral-400 shrink-0">
                          {new Date(item.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
                        <span className="px-2 py-0.5 rounded bg-neutral-200/70 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 font-medium">
                          {item.total_resumes} Resumes
                        </span>
                        <span className="px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-semibold">
                          {item.eligible_count} Eligible
                        </span>
                        <span className="px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950 text-[#A16207] dark:text-amber-400 font-bold">
                          Top: {item.top_score.toFixed(1)} pts
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-neutral-200/60 dark:border-neutral-800/80 text-xs">
                      <button
                        type="button"
                        onClick={() => handleLoadHistory(item.batch_id)}
                        className="inline-flex items-center space-x-1 font-bold text-[#0066FF] hover:underline"
                      >
                        <span>Load Shortlist →</span>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteHistory(item.batch_id, e)}
                        className="text-neutral-400 hover:text-red-600 dark:hover:text-red-400 text-[11px] transition font-medium"
                        title="Delete from history"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* If no report is loaded yet, show drag-and-drop prompt */}
        {!report && (
          <div
            id="dashboard-uploader"
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleFileDrop}
            className={`p-10 md:p-14 rounded-2xl border-2 border-dashed text-center transition-all ${
              isDragging
                ? "border-[#0066FF] bg-blue-50/50 dark:bg-blue-950/20 scale-[0.99]"
                : "border-neutral-300 dark:border-neutral-800 bg-neutral-50/50 dark:bg-neutral-900/40 hover:border-neutral-400 dark:hover:border-neutral-700"
            }`}
          >
            <div className="w-14 h-14 mx-auto rounded-2xl bg-blue-100 dark:bg-blue-950/80 flex items-center justify-center text-2xl text-[#0066FF] mb-4 shadow-sm border border-blue-200 dark:border-blue-800">
              📂
            </div>
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white">
              No Candidates Screened Yet
            </h3>
            <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 mt-1 max-w-md mx-auto">
              Drag and drop candidate resumes (PDF, DOCX) here, or run the bundled 50 sample resumes to test ranking immediately.
            </p>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <label className="cursor-pointer px-5 py-2.5 rounded-xl text-xs font-bold bg-[#0066FF] hover:bg-blue-600 text-white transition shadow-sm">
                Browse Resume Files
                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
              </label>
              <button
                type="button"
                onClick={runSample}
                className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-white dark:bg-neutral-800 hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 border border-neutral-300 dark:border-neutral-700 transition"
              >
                Run 50 Pre-Bundled Resumes
              </button>
            </div>
          </div>
        )}

        {/* Active Analysis & Ranking Workspace */}
        {report && (
          <div className="space-y-6">
            {/* Export Toolbar */}
            <Card className="p-3 flex flex-wrap items-center justify-between gap-3 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800">
              <div className="flex items-center space-x-1.5 flex-wrap gap-y-2">
                <span className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 px-2">
                  Export (<span className="text-neutral-900 dark:text-white font-bold">{exportBadge} ({filtered.length})</span>):
                </span>
                <Button
                  size="sm"
                  onClick={() =>
                    withBusy(`Generating Excel for ${filtered.length} candidate(s) (${scopeLabel})…`, () =>
                      exportFilteredExcel(filtered, scopeLabel)
                    )
                  }
                  className="font-semibold rounded-lg text-xs"
                >
                  Excel
                </Button>
                <Button
                  size="sm"
                  onClick={() =>
                    withBusy(`Generating Word document for ${filtered.length} candidate(s) (${scopeLabel})…`, () =>
                      exportFilteredDocx(filtered, scopeLabel)
                    )
                  }
                  className="font-semibold rounded-lg text-xs"
                >
                  Word
                </Button>
                <Button
                  size="sm"
                  onClick={() =>
                    withBusy("Generating CSV…", () => exportFilteredCsv(filtered, scopeLabel))
                  }
                  className="font-semibold rounded-lg text-xs"
                >
                  CSV
                </Button>
                <Button
                  size="sm"
                  onClick={() =>
                    withBusy("Generating JSON…", () => exportFilteredJson(filtered, scopeLabel))
                  }
                  className="font-semibold rounded-lg text-xs"
                >
                  JSON
                </Button>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={handleClear}
                  className="text-xs text-neutral-500 hover:text-red-600 dark:hover:text-red-400 transition font-medium"
                >
                  Clear results
                </button>
              </div>
            </Card>

            {/* Metrics & Cutoff Slider */}
            <BatchSummaryCards
              summary={report.batch_summary}
              cutoff={cutoff}
              onCutoff={setCutoff}
              avgOverride={`${avgEligible} / 100`}
            />

            {/* Candidate Controls Bar */}
            <div className="space-y-6">
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-neutral-200 dark:border-neutral-800 pb-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Tabs<ActiveTab>
                    active={activeTab}
                    onChange={setActiveTab}
                    options={[
                      {
                        value: "eligible",
                        label: `Ranked Eligible (${
                          activeTab === "eligible" ? filtered.length : report.ranked_candidates.length
                        })`,
                      },
                      {
                        value: "rejected",
                        label: `Disqualified (${
                          activeTab === "rejected" ? filtered.length : report.rejected_candidates.length
                        })`,
                      },
                    ]}
                  />

                  {activeTab === "eligible" && (
                    <SegmentedControl<TopNLimit>
                      active={topN}
                      onChange={setTopN}
                      options={TOPN_OPTIONS}
                    />
                  )}
                </div>

                <div className="w-full lg:w-72">
                  <SearchInput
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search candidate or skill…"
                  />
                </div>
              </div>

              {/* Candidate Cards List */}
              <div className="space-y-4">
                {filtered.length === 0 ? (
                  <div className="p-12 text-center text-neutral-500 rounded-2xl border border-neutral-200 dark:border-neutral-800">
                    No candidates match the selected filters or search query.
                  </div>
                ) : (
                  filtered.map((c) => (
                    <CandidateCard
                      key={`${c.candidate_name}-${c.file_name}`}
                      candidate={c}
                      onPreview={setPreview}
                    />
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />

      <ResumeModal candidate={preview} onClose={() => setPreview(null)} />
      <PricingModal
        open={pricingOpen}
        onClose={() => setPricingOpen(false)}
        onSelectPlan={async (plan) => {
          if (plan === "pro_29") {
            await openRazorpayCheckout({
              tier: "pro_29",
              userEmail: userEmail,
              onSuccess: (updated) => {
                setQuota(updated);
                alert("Payment verified successfully! Your account is upgraded to Recruiter Pro (₹2,499 / $29). 30 screening runs & up to 100 resumes per batch unlocked.");
              },
              onError: (e) => {
                alert("Payment failed or cancelled: " + e.message);
              },
            });
          }
        }}
      />
      {busy && <LoadingOverlay message={loadingMsg || "Processing candidate resumes…"} />}
    </div>
  );
}
