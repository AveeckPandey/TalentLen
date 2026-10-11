"use client";

import { useEffect, useMemo, useState } from "react";
import Header from "@/components/Header";
import HeroUpload from "@/components/HeroUpload";
import BatchSummaryCards from "@/components/BatchSummary";
import CandidateCard from "@/components/CandidateCard";
import ResumeModal from "@/components/ResumeModal";
import AuthModal, { type AuthMode } from "@/components/AuthModal";
import PricingModal from "@/components/PricingModal";
import LoadingOverlay from "@/components/LoadingOverlay";
import {
  Button,
  Card,
  EmptyState,
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
  screenSampleResumes,
  uploadAndScreen,
} from "@/lib/api";
import { getSupabaseClient } from "@/lib/supabase";
import type { ActiveTab, CandidateResult, ScreeningReport, TopNLimit } from "@/lib/types";

const TOPN_OPTIONS: { value: TopNLimit; label: string }[] = [
  { value: "all", label: "All" },
  { value: 5, label: "Top 5" },
  { value: 10, label: "Top 10" },
  { value: 20, label: "Top 20" },
];

export default function DashboardPage() {
  const [report, setReport] = useState<ScreeningReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [activeTab, setActiveTab] = useState<ActiveTab>("eligible");
  const [cutoff, setCutoff] = useState(0);
  const [topN, setTopN] = useState<TopNLimit>("all");
  const [query, setQuery] = useState("");
  const [preview, setPreview] = useState<CandidateResult | null>(null);

  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [pricingOpen, setPricingOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const authConfigured = Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );

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

    const sb = getSupabaseClient();
    if (!sb) return;
    sb.auth.getSession().then(({ data }) => setUserEmail(data.session?.user?.email ?? null));
    const { data: sub } = sb.auth.onAuthStateChange((_ev, session) =>
      setUserEmail(session?.user?.email ?? null)
    );
    return () => sub.subscription.unsubscribe();
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

  function handleBulkUpload() {
    const el = document.getElementById("ingest-box");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("ring-2", "ring-neutral-400");
      setTimeout(() => el.classList.remove("ring-2", "ring-neutral-400"), 1200);
    }
  }

  function openAuth(mode: AuthMode) {
    setAuthMode(mode);
    setAuthOpen(true);
  }

  async function runSample() {
    setBusy(true);
    setLoadingMsg("Screening 50 sample resumes from resumes/ directory…");
    try {
      const r = await screenSampleResumes();
      setReport(r);
      setActiveTab("eligible");
    } catch (e: unknown) {
      alert("Error screening resumes: " + (e instanceof Error ? e.message : String(e)));
    } finally {
      setBusy(false);
    }
  }

  async function runUpload(files: File[]) {
    if (files.length === 0) return runSample();
    setBusy(true);
    setLoadingMsg(`Uploading and parsing ${files.length} resumes…`);
    try {
      const r = await uploadAndScreen(files);
      setReport(r);
      setActiveTab("eligible");
    } catch (e: unknown) {
      alert("Upload failed: " + (e instanceof Error ? e.message : String(e)));
    } finally {
      setBusy(false);
    }
  }

  async function handleClear() {
    await clearSession();
    setReport(null);
    setQuery("");
    setCutoff(0);
    setTopN("all");
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
    <>
      <Header
        userEmail={userEmail}
        authConfigured={authConfigured}
        onLogin={() => openAuth("login")}
        onSignup={() => openAuth("signup")}
        onSignOut={async () => {
          await getSupabaseClient()?.auth.signOut();
          setUserEmail(null);
        }}
        onBulkUpload={handleBulkUpload}
        onPricing={() => setPricingOpen(true)}
        isDark={isDark}
        onToggleTheme={toggleTheme}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <HeroUpload busy={busy} onRunUpload={runUpload} onRunSample={runSample} />

        {report && (
          <Card className="p-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-1 bg-neutral-100 dark:bg-black/40 p-1 rounded-xl border border-neutral-200 dark:border-neutral-800">
              <span className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 px-2">
                Export (<span className="text-neutral-900 dark:text-white font-bold">{exportBadge} ({filtered.length})</span>):
              </span>
              <Button size="sm" onClick={() => withBusy(`Generating Excel for ${filtered.length} candidate(s) (${scopeLabel})…`, () => exportFilteredExcel(filtered, scopeLabel))} className="font-semibold rounded-lg">Excel</Button>
              <Button size="sm" onClick={() => withBusy(`Generating Word document for ${filtered.length} candidate(s) (${scopeLabel})…`, () => exportFilteredDocx(filtered, scopeLabel))} className="font-semibold rounded-lg">Word</Button>
              <Button size="sm" onClick={() => withBusy("Generating CSV…", () => exportFilteredCsv(filtered, scopeLabel))} className="font-semibold rounded-lg">CSV</Button>
              <Button size="sm" onClick={() => withBusy("Generating JSON…", () => exportFilteredJson(filtered, scopeLabel))} className="font-semibold rounded-lg">JSON</Button>
            </div>
            <Button variant="link" size="none" onClick={handleClear} className="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-300">
              Clear results
            </Button>
          </Card>
        )}

        {!report ? (
          <EmptyState
            title="No candidates ranked yet"
            hint={<>Click <span className="text-[#0066FF] font-semibold">Upload Resume</span> or <span className="text-neutral-900 dark:text-white font-semibold">⚡ Try 50 Samples</span> above to evaluate candidates.</>}
          />
        ) : (
          <>
            <BatchSummaryCards
              summary={report.batch_summary}
              cutoff={cutoff}
              onCutoff={setCutoff}
              avgOverride={`${avgEligible} / 100`}
            />

            <div className="space-y-6">
              <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-neutral-800 pb-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Tabs<ActiveTab>
                    active={activeTab}
                    onChange={setActiveTab}
                    options={[
                      { value: "eligible", label: `Ranked Eligible (${activeTab === "eligible" ? filtered.length : report.ranked_candidates.length})` },
                      { value: "rejected", label: `Disqualified (${activeTab === "rejected" ? filtered.length : report.rejected_candidates.length})` },
                    ]}
                  />

                  <SegmentedControl<TopNLimit>
                    label="Show:"
                    active={topN}
                    onChange={setTopN}
                    options={TOPN_OPTIONS}
                  />

                  <div className="flex items-center space-x-1 bg-neutral-100 dark:bg-neutral-900 p-1 rounded-xl border border-neutral-200 dark:border-neutral-800">
                    <span className="text-[11px] font-semibold text-neutral-500 dark:text-neutral-400 px-2">Download:</span>
                    <Button size="none" onClick={() => withBusy("Generating Excel…", () => exportFilteredExcel(filtered, scopeLabel))} className="px-2 py-1 text-xs font-semibold rounded-lg">Excel</Button>
                    <Button size="none" onClick={() => withBusy("Generating Word…", () => exportFilteredDocx(filtered, scopeLabel))} className="px-2 py-1 text-xs font-semibold rounded-lg">Docx</Button>
                    <Button size="none" onClick={() => withBusy("Generating CSV…", () => exportFilteredCsv(filtered, scopeLabel))} className="px-2 py-1 text-xs font-semibold rounded-lg">CSV</Button>
                  </div>
                </div>

                <div className="relative w-full lg:w-72">
                  <SearchInput
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search candidate or skill…"
                  />
                </div>
              </div>

              <div className="space-y-4">
                {filtered.length === 0 ? (
                  <div className="p-8 text-center text-neutral-400 bg-neutral-900 rounded-xl border border-neutral-800">
                    No candidates match the current filters or cutoff score (≥ {cutoff} pts).
                  </div>
                ) : (
                  filtered.map((c) => (
                    <CandidateCard key={`${c.file_name}-${c.candidate_name}`} candidate={c} onPreview={setPreview} />
                  ))
                )}
              </div>

              <div className="text-center">
                <Button variant="link" size="none" onClick={handleClear} className="text-xs text-neutral-500">
                  Clear results
                </Button>
              </div>
            </div>
          </>
        )}
      </main>

      <ResumeModal candidate={preview} onClose={() => setPreview(null)} />
      <PricingModal open={pricingOpen} onClose={() => setPricingOpen(false)} />
      <AuthModal open={authOpen} initialMode={authMode} onClose={() => setAuthOpen(false)} onAuthed={() => getSupabaseClient()?.auth.getSession().then(({ data }) => setUserEmail(data.session?.user?.email ?? null))} />
      {busy && <LoadingOverlay message={loadingMsg || "Processing candidate resumes…"} />}
    </>
  );
}
