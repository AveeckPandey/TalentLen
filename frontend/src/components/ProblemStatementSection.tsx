"use client";

interface SolutionCard {
  id: string;
  icon: string;
  title: string;
  description: string;
}

const CARDS: SolutionCard[] = [
  {
    id: "fatigue",
    icon: "⏱️",
    title: "for 10-Second Resume Fatigue",
    description: "Eliminate human reviewer fatigue and never miss top candidates in 10–30s rushed scans.",
  },
  {
    id: "outdated",
    icon: "🛠️",
    title: "for Outdated Project Sifting",
    description: "Filter out generic to-do lists and basic CRUD apps to surface real engineering depth.",
  },
  {
    id: "tech-hr",
    icon: "🎯",
    title: "for Non-Technical & Junior HR",
    description: "Provide clear, objective scoring rubrics without requiring deep software engineering expertise.",
  },
  {
    id: "campus",
    icon: "🎓",
    title: "for Campus & Placement Drives",
    description: "Screen hundreds of student applicants simultaneously with consistent benchmark standards.",
  },
  {
    id: "sde-ai",
    icon: "🤖",
    title: "for Modern SDE & Agentic AI",
    description: "Evaluate authentic Python proficiency, asynchronous APIs, and real agent architectures.",
  },
  {
    id: "batch",
    icon: "⚡",
    title: "for High-Volume Ingestion",
    description: "Bulk process 100+ resumes in seconds with instant candidate leaderboards and scoring.",
  },
  {
    id: "startups",
    icon: "🚀",
    title: "for Fast-Moving Startups",
    description: "Skip weeks of manual resume sorting and jump straight to interviewing top-tier talent.",
  },
  {
    id: "bias-free",
    icon: "🛡️",
    title: "for Unbiased Blind Evaluation",
    description: "Neutralize demographic, gender, and school brand biases to evaluate candidates purely on merit.",
  },
  {
    id: "enterprise",
    icon: "🏢",
    title: "for Enterprise HR Teams",
    description: "Export standardized shortlists to Excel, Word, CSV, and JSON with complete audit trails.",
  },
];

export default function ProblemStatementSection() {
  function handleCardClick() {
    const el = document.getElementById("ingest-box");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("ring-2", "ring-neutral-400");
      setTimeout(() => el.classList.remove("ring-2", "ring-neutral-400"), 1200);
    }
  }

  return (
    <section className="py-16 sm:py-24 border-t border-neutral-200/80 dark:border-neutral-800/80">
      <div className="max-w-6xl mx-auto px-4 text-center">
        
        {/* Section Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs font-semibold text-[#0066FF] dark:text-blue-400 mb-4">
          <span>Problem Solved</span>
          <span>•</span>
          <span>The 10–30 Second Resume Bottleneck</span>
        </div>

        {/* Headline (remove.bg style: "One tool, endless uses") */}
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-neutral-900 dark:text-white tracking-tight">
          One platform, endless hiring solutions
        </h2>

        {/* Problem Statement Narrative */}
        <div className="mt-5 max-w-3xl mx-auto space-y-3 text-sm sm:text-base text-neutral-600 dark:text-neutral-300 leading-relaxed">
          <p>
            When recruiters review applicants, they typically spend only{" "}
            <strong className="text-neutral-900 dark:text-white font-semibold">
              10 to 30 seconds per resume
            </strong>
            . In that rush, exceptional candidates easily get overlooked because humans get tired, and mistakes happen.
          </p>
          <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400">
            Compounding the challenge, today's applicant pools are flooded with low-effort projects—outdated to-do lists and basic management systems created without real skill. For busy or newer HR teams, separating superficial projects from genuine engineering rigor takes countless hours. TalentLens automates this evaluation instantly so you never miss top talent.
          </p>
        </div>

        {/* 3x3 Grid of Solution Cards (remove.bg style) */}
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 text-left">
          {CARDS.map((card) => (
            <div
              key={card.id}
              onClick={handleCardClick}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && handleCardClick()}
              className="group p-6 rounded-2xl bg-white dark:bg-neutral-900/90 border border-neutral-200/90 dark:border-neutral-800 hover:border-neutral-300 dark:hover:border-neutral-700 shadow-sm hover:shadow-xl transition-all duration-200 cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl select-none">{card.icon}</span>
                  <span className="text-neutral-400 group-hover:text-neutral-900 dark:group-hover:text-white group-hover:translate-x-1 transition-all text-sm font-bold">
                    →
                  </span>
                </div>
                <h3 className="text-base font-bold text-neutral-900 dark:text-white mt-4 group-hover:text-[#0066FF] dark:group-hover:text-blue-400 transition-colors">
                  {card.title}
                </h3>
                <p className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 mt-2 leading-relaxed">
                  {card.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800/80 flex items-center text-[11px] font-semibold text-[#0066FF] dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Start screening candidates</span>
                <span className="ml-1">↗</span>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
