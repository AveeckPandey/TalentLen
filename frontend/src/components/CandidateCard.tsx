"use client";

import type { CandidateResult } from "@/lib/types";
import { resumeUrl } from "@/lib/api";
import { Badge, Button, Card } from "./ui";

function ScoreCell({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span className="text-neutral-500 dark:text-neutral-400 block text-[10px]">{label}</span>
      <span className="font-bold text-neutral-900 dark:text-white">{value} pts</span>
    </div>
  );
}

export default function CandidateCard({
  candidate,
  onPreview,
}: {
  candidate: CandidateResult;
  onPreview: (c: CandidateResult) => void;
}) {
  const c = candidate;
  const url = resumeUrl(c.file_name);

  if (c.eligible) {
    return (
      <Card className="p-5 space-y-4 transition shadow-sm hover:border-neutral-400 dark:hover:border-neutral-700">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 border-b border-neutral-200 dark:border-neutral-800 pb-3">
          <div className="flex items-center space-x-3">
            <span className="w-9 h-9 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white border border-neutral-300 dark:border-neutral-700 font-bold flex items-center justify-center text-sm">
              #{c.rank}
            </span>
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h3 className="text-base font-bold text-neutral-900 dark:text-white">
                  {c.candidate_name}
                  {c.github_metrics?.username && (
                    <a
                      href={`https://github.com/${c.github_metrics.username}`}
                      target="_blank"
                      rel="noreferrer"
                      title={`GitHub: ${c.github_metrics.username}`}
                      className="text-neutral-500 dark:text-neutral-400 hover:text-black dark:hover:text-white transition ml-2 text-sm"
                    >
                      GitHub ↗
                    </a>
                  )}
                </h3>
                <div className="inline-flex items-center space-x-1.5">
                  <button
                    onClick={() => onPreview(c)}
                    className="inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-lg bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-800 dark:text-neutral-200 border border-neutral-300 dark:border-neutral-600 transition"
                    title="Preview Original Resume in modal"
                  >
                    View Resume
                  </button>
                  <a
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-lg bg-neutral-50 hover:bg-neutral-200 dark:bg-neutral-950 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:text-black dark:hover:text-white border border-neutral-200 dark:border-neutral-800 transition"
                  >
                    Original File ↗
                  </a>
                </div>
              </div>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-0.5">
                <span className="font-mono">{c.file_name}</span>
                {c.email && <span className="text-neutral-700 dark:text-neutral-300">• {c.email}</span>}
                {c.phone && <span className="text-neutral-700 dark:text-neutral-300">• {c.phone}</span>}
                {c.cgpa ? (
                  <span className="text-neutral-700 dark:text-neutral-300">• CGPA: <span className="text-neutral-900 dark:text-white font-semibold">{c.cgpa}</span>/10</span>
                ) : (
                  "• CGPA: Not Listed"
                )}
              </p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-neutral-500 dark:text-neutral-400 block">Total Score</span>
            <span className="text-xl font-extrabold text-neutral-900 dark:text-white">
              {c.total_score.toFixed(1)}<span className="text-xs text-neutral-500"> / 100</span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs bg-neutral-50 dark:bg-black/60 p-3 rounded-lg border border-neutral-200 dark:border-neutral-800">
          <ScoreCell label="AI Project Depth (40)" value={c.score_breakdown.ai_project_depth} />
          <ScoreCell label="Python & Backend (30)" value={c.score_breakdown.python_backend} />
          <ScoreCell label="Cloud & Fullstack (15)" value={c.score_breakdown.cloud_fullstack} />
          <ScoreCell label="GitHub Activity (10)" value={c.score_breakdown.github} />
          <ScoreCell label="Engineering Depth (5)" value={c.score_breakdown.engineering_depth} />
        </div>

        {c.project_evaluation && (
          <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-700 dark:text-neutral-300 bg-blue-50/70 dark:bg-blue-950/30 p-2.5 rounded-lg border border-blue-200 dark:border-blue-900/50">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-[#0066FF] text-white">
              {c.project_evaluation.evaluation_source === "groq"
                ? "⚡ Groq Project Intelligence"
                : "⚡ Project Intelligence"}
            </span>
            <span>•</span>
            <span>
              <strong className="text-neutral-900 dark:text-white">
                {c.project_count || c.project_evaluation.project_count}
              </strong>{" "}
              Projects Scanned
            </span>
            <span>•</span>
            <span>
              AI Depth:{" "}
              <strong className="text-neutral-900 dark:text-white">
                {c.score_breakdown.ai_project_depth.toFixed(1)} / 40
              </strong>
            </span>
            {c.project_evaluation.is_tutorial_or_shallow && (
              <span className="text-amber-600 dark:text-amber-400 font-semibold text-[11px]">
                (⚠️ Shallow / Tutorial Signals Detected)
              </span>
            )}
            {c.project_evaluation.architectural_summary && (
              <p className="w-full text-[11px] text-neutral-600 dark:text-neutral-400 mt-1 italic">
                "{c.project_evaluation.architectural_summary}"
              </p>
            )}
          </div>
        )}

        {c.github_metrics && c.github_metrics.status === "enriched" && (
          <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-700 dark:text-neutral-300 bg-neutral-50 dark:bg-black/40 p-2.5 rounded-lg border border-neutral-200 dark:border-neutral-800">
            <Badge variant="bright" className="font-semibold">
              {c.github_metrics.cohort}
            </Badge>
            <span>•</span>
            <span><strong className="text-neutral-900 dark:text-white">{c.github_metrics.account_age_years}</strong> yrs on GitHub</span>
            <span>•</span>
            <span><strong className="text-neutral-900 dark:text-white">{c.github_metrics.public_repos}</strong> repos ({c.github_metrics.original_repos_count || 0} original)</span>
            <span>•</span>
            <span><strong className="text-neutral-900 dark:text-white">{c.github_metrics.total_contributions || c.github_metrics.recent_commits}</strong> contributions</span>
            <span>•</span>
            <span><strong className="text-neutral-900 dark:text-white">{c.github_metrics.recent_commits}</strong> commits</span>
            {c.github_metrics.prs_count > 0 && (<><span>•</span><span><strong className="text-neutral-900 dark:text-white">{c.github_metrics.prs_count}</strong> PRs</span></>)}
            {c.github_metrics.total_stars > 0 && (<><span>•</span><span>★ <strong className="text-neutral-900 dark:text-white">{c.github_metrics.total_stars}</strong> stars</span></>)}
          </div>
        )}

        <div className="bg-neutral-50/70 dark:bg-black/40 border border-neutral-200 dark:border-neutral-800 rounded-lg p-3 text-xs leading-relaxed text-neutral-700 dark:text-neutral-300">
          <span className="text-[11px] font-bold text-neutral-900 dark:text-neutral-200 uppercase tracking-wider block mb-1">
            50–100 Word Evaluation Justification:
          </span>
          <p>{c.reason_50_to_100_words}</p>
        </div>

        <div className="flex flex-wrap gap-1.5 pt-1">
          {(c.matched_skills || []).map((s) => (
            <Badge key={s}>{s}</Badge>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5 space-y-4 transition shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-neutral-200 dark:border-neutral-800 pb-3">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h3 className="text-base font-bold text-neutral-800 dark:text-neutral-200">{c.candidate_name}</h3>
            <div className="inline-flex items-center space-x-1.5">
              <Button
                variant="soft"
                size="xs"
                onClick={() => onPreview(c)}
                className="font-semibold rounded-lg"
              >
                View Resume
              </Button>
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="px-2 py-0.5 text-xs font-medium rounded-lg bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-950 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-neutral-300 dark:border-neutral-800 transition"
              >
                Original File ↗
              </a>
            </div>
          </div>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 flex flex-wrap items-center gap-x-2 mt-0.5">
            <span className="font-mono">{c.file_name}</span>
            {c.email && <span>• {c.email}</span>}
            {c.phone && <span>• {c.phone}</span>}
          </p>
        </div>
        <Badge variant="faint" size="sm" pill className="font-semibold">
          Disqualified
        </Badge>
      </div>

      <div className="space-y-1.5">
        <span className="text-[11px] font-bold text-neutral-600 dark:text-neutral-400 uppercase tracking-wider block">
          Explicit Disqualification Reasons:
        </span>
        <div className="flex flex-wrap gap-2">
          {(c.rejection_reasons || []).map((r) => (
            <Badge key={r} variant="muted" size="sm">
              ✕ {r}
            </Badge>
          ))}
        </div>
      </div>

      <div className="bg-neutral-50/70 dark:bg-black/40 border border-neutral-200 dark:border-neutral-800 rounded-lg p-3 text-xs leading-relaxed text-neutral-600 dark:text-neutral-400">
        <span className="text-[11px] font-bold uppercase tracking-wider block mb-1">Evaluation Notes:</span>
        <p>{c.reason_50_to_100_words}</p>
      </div>

      <div className="flex flex-wrap gap-1.5 pt-1">
        {(c.matched_skills || []).map((s) => (
          <Badge key={s} variant="faint">{s}</Badge>
        ))}
      </div>
    </Card>
  );
}
