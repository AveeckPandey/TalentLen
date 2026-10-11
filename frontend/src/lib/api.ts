import type { CandidateResult, ScreeningReport } from "./types";

async function authHeader(): Promise<Record<string, string>> {
  // Supabase session is read client-side and attached as Bearer token,
  // matching the old static dashboard's authHeaders() behaviour.
  if (typeof window === "undefined") return {};
  try {
    const { getSupabaseClient } = await import("./supabase");
    const sb = getSupabaseClient();
    if (!sb) return {};
    const { data } = await sb.auth.getSession();
    const token = data.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

export async function screenSampleResumes(): Promise<ScreeningReport> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
  };
  const resp = await fetch("/screen", {
    method: "POST",
    headers,
    body: JSON.stringify({
      input_dir: "./resumes",
      min_cgpa: null,
      require_ai: true,
      require_experience: false,
      require_github_link: false,
    }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return (await resp.json()) as ScreeningReport;
}

export async function uploadAndScreen(files: File[]): Promise<ScreeningReport> {
  const form = new FormData();
  files.slice(0, 100).forEach((f) => form.append("files", f));
  form.append("require_ai", "true");
  form.append("require_experience", "false");
  form.append("require_github_link", "false");
  const resp = await fetch("/upload_and_screen", {
    method: "POST",
    headers: await authHeader(),
    body: form,
  });
  if (!resp.ok) throw new Error(await resp.text());
  return (await resp.json()) as ScreeningReport;
}

export async function clearSession(): Promise<void> {
  try {
    await fetch("/clear", { method: "POST", headers: await authHeader() });
  } catch {
    /* best-effort */
  }
}

export function resumeUrl(fileName: string): string {
  return `/resumes/${encodeURIComponent(fileName)}`;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportFilteredExcel(candidates: CandidateResult[], filterLabel: string) {
  const headers = { "Content-Type": "application/json", ...(await authHeader()) };
  const resp = await fetch("/export_filtered_excel", {
    method: "POST",
    headers,
    body: JSON.stringify({ candidates, filter_label: filterLabel }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  downloadBlob(await resp.blob(), `shortlist_${filterLabel.toLowerCase()}.xlsx`);
}

export async function exportFilteredDocx(candidates: CandidateResult[], filterLabel: string) {
  const headers = { "Content-Type": "application/json", ...(await authHeader()) };
  const resp = await fetch("/export_filtered_docx", {
    method: "POST",
    headers,
    body: JSON.stringify({ candidates, filter_label: filterLabel }),
  });
  if (!resp.ok) throw new Error(await resp.text());
  downloadBlob(await resp.blob(), `shortlist_${filterLabel.toLowerCase()}.docx`);
}

export function exportFilteredCsv(candidates: CandidateResult[], filterLabel: string) {
  const headers = [
    "Rank", "Candidate Name", "Email", "Phone", "Resume File", "Status",
    "Total Score", "AI Depth (40)", "Python (30)", "Cloud (15)", "GitHub (10)", "Eng (5)",
    "CGPA", "Experience", "GitHub Cohort", "GitHub Years", "Public Repos", "Original Repos",
    "Total Contributions", "Recent Commits", "PRs", "Stars", "Matched Skills", "Evaluation Justification",
  ];
  const q = (v: string) => `"${(v || "").replace(/"/g, '""')}"`;
  const rows = candidates.map((c) =>
    [
      c.rank !== null && c.rank !== undefined ? String(c.rank) : "Disqualified",
      q(c.candidate_name),
      q(c.email || "N/A"),
      q(c.phone || "N/A"),
      q(c.file_name),
      c.eligible ? "Eligible" : "Disqualified",
      String(c.total_score),
      String(c.score_breakdown?.ai_project_depth ?? 0),
      String(c.score_breakdown?.python_backend ?? 0),
      String(c.score_breakdown?.cloud_fullstack ?? 0),
      String(c.score_breakdown?.github ?? 0),
      String(c.score_breakdown?.engineering_depth ?? 0),
      c.cgpa ?? "N/A",
      c.has_related_experience ? "Yes" : "No",
      c.github_metrics ? q(c.github_metrics.cohort) : "N/A",
      String(c.github_metrics?.account_age_years ?? 0),
      String(c.github_metrics?.public_repos ?? 0),
      String(c.github_metrics?.original_repos_count ?? 0),
      String(c.github_metrics?.total_contributions ?? 0),
      String(c.github_metrics?.recent_commits ?? 0),
      String(c.github_metrics?.prs_count ?? 0),
      String(c.github_metrics?.total_stars ?? 0),
      q((c.matched_skills || []).join("; ")),
      q(c.reason_50_to_100_words || ""),
    ].join(",")
  );
  const blob = new Blob([[headers.join(","), ...rows].join("\n")], { type: "text/csv;charset=utf-8;" });
  downloadBlob(blob, `shortlist_${filterLabel.toLowerCase()}.csv`);
}

export function exportFilteredJson(candidates: CandidateResult[], filterLabel: string) {
  const blob = new Blob(
    [JSON.stringify({ filter_scope: filterLabel, candidate_count: candidates.length, candidates }, null, 2)],
    { type: "application/json" }
  );
  downloadBlob(blob, `shortlist_${filterLabel.toLowerCase()}.json`);
}
