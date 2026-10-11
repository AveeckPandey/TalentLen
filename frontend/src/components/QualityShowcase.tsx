"use client";

import { useState } from "react";

interface CandidateProfile {
  id: string;
  name: string;
  role: string;
  degree: string;
  category: string;
  score: number;
  grade: string;
  skills: string[];
  strengths: string[];
  rawText: {
    education: string;
    experience: string;
    projects: string;
  };
  breakdown: {
    label: string;
    score: number;
    max: number;
  }[];
}

const CANDIDATES: CandidateProfile[] = [
  {
    id: "aditya",
    name: "Aditya Sharma",
    role: "Python & Machine Learning",
    degree: "B.Tech CSE",
    category: "Python & ML",
    score: 94,
    grade: "Top 2% Eligible",
    skills: ["Python", "PyTorch", "FastAPI", "Docker", "LangChain", "Vector DBs"],
    strengths: [
      "Built production RAG pipeline with sub-100ms vector retrieval",
      "Clean async Python patterns and comprehensive pytest suite",
      "Active open-source contributions with verified commit history",
    ],
    rawText: {
      education: "B.Tech Computer Science & Engineering (2022-2026) • CGPA 8.9/10",
      experience: "Software Intern @ AI Labs: Worked on LLM evaluation harnesses, prompt optimization.",
      projects: "Autonomous Agent Tooling: Python CLI orchestrating tool calls with LangChain and FAISS.",
    },
    breakdown: [
      { label: "Python Fundamentals & OOP", score: 29, max: 30 },
      { label: "Agentic AI & System Design", score: 28, max: 30 },
      { label: "Project Depth & Git Quality", score: 24, max: 25 },
      { label: "Problem Solving & CS Core", score: 13, max: 15 },
    ],
  },
  {
    id: "sneha",
    name: "Sneha Iyer",
    role: "Agentic AI & LLM Systems",
    degree: "B.Tech ECE",
    category: "Agentic AI",
    score: 95,
    grade: "Top 1% Eligible",
    skills: ["Python", "Multi-Agent Architectures", "LangGraph", "FastAPI", "PostgreSQL"],
    strengths: [
      "Engineered multi-agent collaboration workflow with self-correcting loops",
      "Extensive benchmarking against SWE-bench style reasoning tasks",
      "Exceptional code readability and strict type safety",
    ],
    rawText: {
      education: "B.Tech Electronics & Communication (2021-2025) • CGPA 9.1/10",
      experience: "Research Assistant: Evaluated multi-agent debate protocols on complex code generation.",
      projects: "Self-Reflective Coding Assistant: Python daemon monitoring workspace state and running lints.",
    },
    breakdown: [
      { label: "Agentic Architecture & Logic", score: 30, max: 30 },
      { label: "Python Mastery & Async APIs", score: 28, max: 30 },
      { label: "Test Rigor & Verification", score: 24, max: 25 },
      { label: "Domain Understanding", score: 13, max: 15 },
    ],
  },
  {
    id: "priya",
    name: "Priya Mehta",
    role: "Data Science & Analysis",
    degree: "B.Tech AI",
    category: "Data Science",
    score: 92,
    grade: "Top 5% Eligible",
    skills: ["Python", "Pandas", "SQL", "Scikit-Learn", "FastAPI", "Data Pipelines"],
    strengths: [
      "Processed 1M+ candidate datasets with automated anomaly detection",
      "High mathematical rigor and statistical reasoning",
      "Well-documented Jupyter benchmarks with reproducible pipelines",
    ],
    rawText: {
      education: "B.Tech Artificial Intelligence & Data (2022-2026) • CGPA 8.8/10",
      experience: "Data Analytics Intern: Designed real-time dashboards and feature stores using DuckDB.",
      projects: "Algorithmic Fairness Auditor: Python toolkit inspecting model inferences for bias mitigation.",
    },
    breakdown: [
      { label: "Data Modeling & SQL", score: 28, max: 30 },
      { label: "Python & Scientific Stack", score: 28, max: 30 },
      { label: "Statistical Soundness", score: 23, max: 25 },
      { label: "Documentation & Clarity", score: 13, max: 15 },
    ],
  },
  {
    id: "rahul",
    name: "Rahul Verma",
    role: "Full Stack Engineer",
    degree: "B.Tech CSE",
    category: "Full Stack",
    score: 89,
    grade: "Top 8% Eligible",
    skills: ["Next.js", "TypeScript", "Python", "PostgreSQL", "TailwindCSS", "REST APIs"],
    strengths: [
      "Built full-stack Next.js + FastAPI portal supporting 10k monthly visitors",
      "Clean UI component hierarchy with strict accessibility standards",
      "Optimized server-side queries reducing payload latency by 45%",
    ],
    rawText: {
      education: "B.Tech Computer Science (2021-2025) • CGPA 8.6/10",
      experience: "Full-Stack Developer: Built reactive analytics portals in React & Python FastAPI.",
      projects: "Candidate Tracker: Real-time board with drag-and-drop state management and secure auth.",
    },
    breakdown: [
      { label: "Frontend & UI Engineering", score: 27, max: 30 },
      { label: "Backend APIs & Python", score: 26, max: 30 },
      { label: "System Architecture & DB", score: 23, max: 25 },
      { label: "Code Craftsmanship", score: 13, max: 15 },
    ],
  },
  {
    id: "karan",
    name: "Karan Patel",
    role: "Cloud & DevOps Engineer",
    degree: "B.Tech CSE",
    category: "Cloud & DevOps",
    score: 87,
    grade: "Top 10% Eligible",
    skills: ["Docker", "Kubernetes", "CI/CD", "Python", "AWS", "Terraform"],
    strengths: [
      "Configured automated GitHub Actions workflows with zero-downtime deploy",
      "Designed secure container sandboxing for untrusted code execution",
      "Strong Linux internals and infrastructure monitoring",
    ],
    rawText: {
      education: "B.Tech Computer Science (2022-2026) • CGPA 8.4/10",
      experience: "DevOps Apprentice: Maintained Kubernetes clusters and Dockerized microservices.",
      projects: "Cloud Sandbox: Auto-provisioning isolated container runner for code interview evaluation.",
    },
    breakdown: [
      { label: "Cloud & Container Systems", score: 27, max: 30 },
      { label: "Automation & Python Scripting", score: 26, max: 30 },
      { label: "Infrastructure Security", score: 22, max: 25 },
      { label: "Reliability & Observability", score: 12, max: 15 },
    ],
  },
];

export default function QualityShowcase() {
  const [activeTab, setActiveTab] = useState<string>("Python & ML");
  const [viewMode, setViewMode] = useState<"scorecard" | "raw">("scorecard");

  const candidate = CANDIDATES.find((c) => c.category === activeTab) || CANDIDATES[0];

  return (
    <section className="py-12 sm:py-16">
      {/* Section Header */}
      <div className="text-center space-y-3 max-w-3xl mx-auto px-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-900 text-xs font-semibold text-[#0066FF] dark:text-blue-400">
          <span>🛡️ Merit-First Evaluation</span>
          <span>•</span>
          <span>Zero Unconscious Bias</span>
        </div>
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-neutral-900 dark:text-white tracking-tight">
          Good quality candidates scanned by AI with zero bias
        </h2>
        <p className="text-sm sm:text-base text-neutral-600 dark:text-neutral-400">
          See how TalentLens converts raw, unorganized resumes into objective, transparent scorecards—evaluating pure technical competency with zero human bias.
        </p>
      </div>

      {/* Category Filter Pills (remove.bg style) */}
      <div className="flex flex-wrap items-center justify-center gap-2 mt-8 px-4">
        {CANDIDATES.map((c) => {
          const isActive = activeTab === c.category;
          return (
            <button
              key={c.category}
              type="button"
              onClick={() => setActiveTab(c.category)}
              className={`px-4 sm:px-5 py-2 rounded-full text-xs sm:text-sm font-semibold transition-all duration-150 ${
                isActive
                  ? "bg-neutral-900 text-white dark:bg-white dark:text-black shadow-md scale-105"
                  : "bg-white dark:bg-neutral-900 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white border border-neutral-200 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700"
              }`}
            >
              {c.category}
            </button>
          );
        })}
      </div>

      {/* Showcase Card */}
      <div className="mt-8 max-w-5xl mx-auto px-4">
        <div className="rounded-3xl border border-neutral-200/90 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-2xl p-6 sm:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* Left: Happy Recruiter with Laptop Showing Selected Students */}
            <div className="lg:col-span-5 flex flex-col items-center justify-center">
              <div className="relative w-full max-w-sm">
                <img
                  src="/quality-recruiter.png"
                  alt="Recruiter happy with selected students"
                  className="w-full h-auto object-contain drop-shadow-lg select-none"
                />
              </div>
              <div className="mt-3 text-center">
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-3 py-1 rounded-full border border-emerald-200 dark:border-emerald-800">
                  ✓ Selected Students • Pure Merit
                </span>
              </div>
            </div>

            {/* Right: Candidate Evaluation Details */}
            <div className="lg:col-span-7 space-y-4">
              
              {/* View Switcher: AI Scorecard vs Raw Resume */}
              <div className="flex items-center justify-between pb-3 border-b border-neutral-200 dark:border-neutral-800">
                <div className="inline-flex p-1 rounded-xl bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700">
                  <button
                    type="button"
                    onClick={() => setViewMode("scorecard")}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${
                      viewMode === "scorecard"
                        ? "bg-white dark:bg-neutral-900 text-[#0066FF] dark:text-blue-400 shadow-sm"
                        : "text-neutral-500 hover:text-neutral-900 dark:hover:text-white"
                    }`}
                  >
                    AI Scorecard (Zero-Bias)
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode("raw")}
                    className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${
                      viewMode === "raw"
                        ? "bg-white dark:bg-neutral-900 text-[#0066FF] dark:text-blue-400 shadow-sm"
                        : "text-neutral-500 hover:text-neutral-900 dark:hover:text-white"
                    }`}
                  >
                    Raw Resume (Unscreened)
                  </button>
                </div>

                <span className="text-xs font-semibold text-neutral-400">
                  {candidate.category}
                </span>
              </div>

              {viewMode === "scorecard" ? (
                <div className="space-y-4">
                  {/* Candidate Name & Score */}
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-xl font-bold text-neutral-900 dark:text-white">
                          {candidate.name}
                        </h3>
                        <span className="text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 px-2.5 py-0.5 rounded-full">
                          ★ {candidate.grade}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                        {candidate.degree} • {candidate.role}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="text-3xl font-black text-neutral-900 dark:text-white leading-none">
                        {candidate.score}
                      </div>
                      <div className="text-[10px] text-neutral-400 font-semibold uppercase tracking-wider mt-0.5">
                        Score / 100
                      </div>
                    </div>
                  </div>

                  {/* Skills Pills */}
                  <div>
                    <div className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider mb-1.5">
                      Verified Skills Matrix
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {candidate.skills.map((s) => (
                        <span
                          key={s}
                          className="px-2.5 py-1 rounded-md text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200/80 dark:border-neutral-700/80"
                        >
                          ✓ {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Key Strengths */}
                  <div className="space-y-1.5 bg-neutral-50 dark:bg-neutral-800/40 p-3 rounded-xl border border-neutral-200/70 dark:border-neutral-800">
                    <div className="text-[11px] font-bold text-neutral-400 uppercase tracking-wider">
                      AI Evaluation Highlights
                    </div>
                    <ul className="space-y-1 text-xs text-neutral-700 dark:text-neutral-300">
                      {candidate.strengths.map((str) => (
                        <li key={str} className="flex items-start gap-2">
                          <span className="text-emerald-500 font-bold shrink-0">✓</span>
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Rubric Breakdown Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                    {candidate.breakdown.map((b) => (
                      <div
                        key={b.label}
                        className="p-2.5 rounded-xl bg-white dark:bg-black/30 border border-neutral-200 dark:border-neutral-800 text-center"
                      >
                        <div className="text-[10px] text-neutral-500 dark:text-neutral-400 font-medium truncate">
                          {b.label}
                        </div>
                        <div className="text-sm font-bold text-neutral-900 dark:text-white mt-0.5">
                          {b.score} <span className="text-[10px] font-normal text-neutral-400">/ {b.max}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-3 font-mono text-xs text-neutral-700 dark:text-neutral-300">
                  <div className="p-3 bg-neutral-50 dark:bg-neutral-800/60 rounded-xl border border-neutral-200 dark:border-neutral-700">
                    <div className="text-xs font-bold text-neutral-900 dark:text-white font-sans flex items-center justify-between">
                      <span>[ANONYMIZED APPLICANT #{candidate.id.toUpperCase()}]</span>
                      <span className="text-[10px] text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-800 font-mono">
                        UNSTRUCTURED PDF
                      </span>
                    </div>
                    <div className="text-[11px] text-neutral-500 mt-1">
                      applicant_resume.pdf • 142 KB • 2 pages
                    </div>
                  </div>

                  <div className="p-2.5 bg-neutral-50 dark:bg-neutral-800/40 rounded-lg border border-neutral-200 dark:border-neutral-800 space-y-1">
                    <div className="font-bold text-[11px] text-neutral-500 uppercase tracking-wide">Education:</div>
                    <p className="text-neutral-600 dark:text-neutral-400">{candidate.rawText.education}</p>
                  </div>

                  <div className="p-2.5 bg-neutral-50 dark:bg-neutral-800/40 rounded-lg border border-neutral-200 dark:border-neutral-800 space-y-1">
                    <div className="font-bold text-[11px] text-neutral-500 uppercase tracking-wide">Experience:</div>
                    <p className="text-neutral-600 dark:text-neutral-400">{candidate.rawText.experience}</p>
                  </div>

                  <div className="p-2.5 bg-neutral-50 dark:bg-neutral-800/40 rounded-lg border border-neutral-200 dark:border-neutral-800 space-y-1">
                    <div className="font-bold text-[11px] text-neutral-500 uppercase tracking-wide">Projects:</div>
                    <p className="text-neutral-600 dark:text-neutral-400">{candidate.rawText.projects}</p>
                  </div>

                  <div className="text-[11px] text-amber-600 dark:text-amber-400 pt-1">
                    ⚠️ Raw manual review takes ~8 min/resume and is prone to human fatigue &amp; bias.
                  </div>
                </div>
              )}

              {/* Footer Audit Notice */}
              <div className="pt-3 border-t border-neutral-200 dark:border-neutral-800 flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400">
                <span className="flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Demographic, gender, and school brand biases decoupled
                </span>
                <span className="font-mono text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold">
                  AUDITED COMPLIANT
                </span>
              </div>

            </div>
          </div>
        </div>
      </div>

      {/* 3 Pillars of Zero-Bias AI Screening */}
      <div className="mt-12 max-w-5xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-white dark:bg-neutral-900/60 border border-neutral-200/90 dark:border-neutral-800 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/50 flex items-center justify-center text-[#0066FF] text-lg font-bold mb-4">
            ⚖️
          </div>
          <h4 className="text-base font-bold text-neutral-900 dark:text-white">
            100% Objective Scoring
          </h4>
          <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 mt-2 leading-relaxed">
            Every candidate is graded against the exact same rubric: Python fundamentals, project architecture, and problem solving.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-neutral-900/60 border border-neutral-200/90 dark:border-neutral-800 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 flex items-center justify-center text-emerald-600 text-lg font-bold mb-4">
            🛡️
          </div>
          <h4 className="text-base font-bold text-neutral-900 dark:text-white">
            Blind Review Protocol
          </h4>
          <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 mt-2 leading-relaxed">
            Names, photos, gender, ethnicity, and college brand names are decoupled to eliminate unconscious human bias.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white dark:bg-neutral-900/60 border border-neutral-200/90 dark:border-neutral-800 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 text-lg font-bold mb-4">
            ⚡
          </div>
          <h4 className="text-base font-bold text-neutral-900 dark:text-white">
            Instant Batch Screening
          </h4>
          <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 mt-2 leading-relaxed">
            Evaluate hundreds of resumes in seconds with verifiable scores, ranked leaderboards, and instant Excel/Word exports.
          </p>
        </div>
      </div>
    </section>
  );
}
