"use client";

import type { BatchSummary } from "@/lib/types";
import { Badge, Card, Slider, Stat } from "./ui";

interface Props {
  summary: BatchSummary;
  cutoff: number;
  onCutoff: (v: number) => void;
  avgOverride?: string;
}

export default function BatchSummaryCards({ summary, cutoff, onCutoff, avgOverride }: Props) {
  const avg = avgOverride ?? `${summary.average_score_eligible} / 100`;
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Stat label="Total Ingested" value={summary.total_resumes} />
        <Stat label="Successfully Parsed" value={summary.successfully_parsed} />
        <Stat label="Eligible Candidates" value={summary.eligible} />
        <Stat label="Disqualified" value={summary.rejected} valueClassName="text-neutral-400" />
        <div className="bg-neutral-900 border border-neutral-700 rounded-xl p-3.5 text-center col-span-2 md:col-span-1 flex flex-col justify-between">
          <Slider
            label="Min Passing Score:"
            display={cutoff === 0 ? "≥ 0 pts" : `≥ ${cutoff} pts`}
            min={0}
            max={95}
            step={5}
            value={cutoff}
            onChange={onCutoff}
            marks={[0, 40, 60, 80, 95]}
          />
          <div className="mt-2 pt-1.5 border-t border-neutral-800 flex items-center justify-between">
            <span className="text-[11px] font-medium text-neutral-400">Avg Eligible Score</span>
            <span className="text-lg font-extrabold text-white">{avg}</span>
          </div>
        </div>
      </div>

      <Card className="p-4 flex flex-wrap items-center justify-between gap-4">
        <span className="text-xs font-semibold text-neutral-300">GitHub Developer Cohorts:</span>
        <div className="flex flex-wrap gap-2 text-xs">
          {Object.entries(summary.github_cohorts || {}).map(([cohort, count]) => (
            <Badge key={cohort} size="sm" pill>
              <span className="font-semibold text-white">{count}</span> {cohort}
            </Badge>
          ))}
        </div>
      </Card>
    </div>
  );
}
