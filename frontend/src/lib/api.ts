import type {
  CandidateResult,
  ScreeningReport,
  UserQuota,
  PlanTier,
  CreateOrderResponse,
  VerifyPaymentResponse,
  ApiKeyItem,
  CreateApiKeyResponse,
  ScreeningHistoryItem,
} from "./types";

const LIVE_BACKEND_URL = "https://backend-talentlens.onrender.com";

export function getApiBaseUrl(): string {
  // 1. Explicit env var if set
  const envUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_URL;
  if (envUrl && !envUrl.includes("127.0.0.1") && !envUrl.includes("localhost")) {
    return envUrl.replace(/\/+$/, "");
  }

  // 2. Client-side browser execution
  if (typeof window !== "undefined") {
    // If running locally on localhost, use local proxy or relative URL
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return envUrl ? envUrl.replace(/\/+$/, "") : "";
    }
    // Deployed on Vercel / custom domain (talentlens.buildwithaveeck.com) -> use live Render backend directly
    return LIVE_BACKEND_URL;
  }

  // 3. Server-side in Node/Next.js
  return envUrl && !envUrl.includes("127.0.0.1") ? envUrl.replace(/\/+$/, "") : LIVE_BACKEND_URL;
}

export function apiUrl(path: string): string {
  const base = getApiBaseUrl();
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${cleanPath}` : cleanPath;
}

async function handleResponseError(resp: Response, fallbackPrefix: string): Promise<never> {
  let message = `${fallbackPrefix} (${resp.status})`;
  try {
    const text = await resp.text();
    try {
      const json = JSON.parse(text);
      if (json && json.detail) {
        message = typeof json.detail === "string" ? json.detail : JSON.stringify(json.detail);
      } else if (text) {
        message = text;
      }
    } catch {
      if (text) message = text;
    }
  } catch {
    /* fallback to status */
  }
  throw new Error(message);
}

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
  const resp = await fetch(apiUrl("/screen"), {
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
  if (!resp.ok) await handleResponseError(resp, "Screening failed");
  return (await resp.json()) as ScreeningReport;
}

export async function uploadAndScreen(files: File[]): Promise<ScreeningReport> {
  const form = new FormData();
  files.slice(0, 100).forEach((f) => form.append("files", f));
  form.append("require_ai", "true");
  form.append("require_experience", "false");
  form.append("require_github_link", "false");
  const resp = await fetch(apiUrl("/upload_and_screen"), {
    method: "POST",
    headers: await authHeader(),
    body: form,
  });
  if (!resp.ok) await handleResponseError(resp, "Upload failed");
  return (await resp.json()) as ScreeningReport;
}

export async function getResults(): Promise<ScreeningReport | null> {
  try {
    const resp = await fetch(apiUrl("/results"), {
      method: "GET",
      headers: await authHeader(),
    });
    if (!resp.ok) return null;
    return (await resp.json()) as ScreeningReport;
  } catch {
    return null;
  }
}

export async function clearSession(): Promise<void> {
  try {
    await fetch(apiUrl("/clear"), { method: "POST", headers: await authHeader() });
  } catch {
    /* best-effort */
  }
}

export function resumeUrl(fileName: string): string {
  return apiUrl(`/resumes/${encodeURIComponent(fileName)}`);
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
  const resp = await fetch(apiUrl("/export_filtered_excel"), {
    method: "POST",
    headers,
    body: JSON.stringify({ candidates, filter_label: filterLabel }),
  });
  if (!resp.ok) await handleResponseError(resp, "Excel export failed");
  downloadBlob(await resp.blob(), `shortlist_${filterLabel.toLowerCase()}.xlsx`);
}

export async function exportFilteredDocx(candidates: CandidateResult[], filterLabel: string) {
  const headers = { "Content-Type": "application/json", ...(await authHeader()) };
  const resp = await fetch(apiUrl("/export_filtered_docx"), {
    method: "POST",
    headers,
    body: JSON.stringify({ candidates, filter_label: filterLabel }),
  });
  if (!resp.ok) await handleResponseError(resp, "Word export failed");
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

export async function getUserQuota(): Promise<UserQuota> {
  const resp = await fetch(apiUrl("/api/user/quota"), {
    method: "GET",
    headers: await authHeader(),
  });
  if (!resp.ok) await handleResponseError(resp, "Failed to load quota");
  return (await resp.json()) as UserQuota;
}

export async function upgradeUserTier(tier: PlanTier): Promise<UserQuota> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
  };
  const resp = await fetch(apiUrl("/api/user/upgrade"), {
    method: "POST",
    headers,
    body: JSON.stringify({ tier }),
  });
  if (!resp.ok) await handleResponseError(resp, "Upgrade failed");
  return (await resp.json()) as UserQuota;
}

// -----------------------------------------------------------------
// Razorpay Payments
// -----------------------------------------------------------------

export async function createRazorpayOrder(
  tier: PlanTier = "pro_29",
  currency: string = "INR"
): Promise<CreateOrderResponse> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
  };
  const resp = await fetch(apiUrl("/api/payments/create-order"), {
    method: "POST",
    headers,
    body: JSON.stringify({ tier, currency }),
  });
  if (!resp.ok) await handleResponseError(resp, "Failed to create payment order");
  return (await resp.json()) as CreateOrderResponse;
}

export async function verifyRazorpayPayment(
  razorpay_order_id: string,
  razorpay_payment_id: string,
  razorpay_signature: string,
  tier: PlanTier = "pro_29"
): Promise<VerifyPaymentResponse> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
  };
  const resp = await fetch(apiUrl("/api/payments/verify"), {
    method: "POST",
    headers,
    body: JSON.stringify({
      razorpay_order_id,
      razorpay_payment_id,
      razorpay_signature,
      tier,
    }),
  });
  if (!resp.ok) await handleResponseError(resp, "Payment verification failed");
  return (await resp.json()) as VerifyPaymentResponse;
}

// -----------------------------------------------------------------
// Developer API Key Management
// -----------------------------------------------------------------

export async function listUserApiKeys(): Promise<ApiKeyItem[]> {
  const resp = await fetch(apiUrl("/api/user/keys"), {
    method: "GET",
    headers: await authHeader(),
  });
  if (!resp.ok) await handleResponseError(resp, "Failed to list API keys");
  return (await resp.json()) as ApiKeyItem[];
}

export async function createUserApiKey(name: string): Promise<CreateApiKeyResponse> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeader()),
  };
  const resp = await fetch(apiUrl("/api/user/keys"), {
    method: "POST",
    headers,
    body: JSON.stringify({ name }),
  });
  if (!resp.ok) await handleResponseError(resp, "Failed to create API key");
  return (await resp.json()) as CreateApiKeyResponse;
}

export async function deleteUserApiKey(keyId: string): Promise<void> {
  const resp = await fetch(apiUrl(`/api/user/keys/${encodeURIComponent(keyId)}`), {
    method: "DELETE",
    headers: await authHeader(),
  });
  if (!resp.ok) await handleResponseError(resp, "Failed to delete API key");
}

export const revokeUserApiKey = deleteUserApiKey;

// -----------------------------------------------------------------
// Previous Shortlistings / Screening History
// -----------------------------------------------------------------

export async function listScreeningHistory(): Promise<ScreeningHistoryItem[]> {
  try {
    const resp = await fetch(apiUrl("/api/history"), {
      method: "GET",
      headers: await authHeader(),
    });
    if (!resp.ok) return [];
    return (await resp.json()) as ScreeningHistoryItem[];
  } catch {
    return [];
  }
}

export async function loadScreeningHistory(batchId: string): Promise<ScreeningReport> {
  const resp = await fetch(apiUrl(`/api/history/${encodeURIComponent(batchId)}`), {
    method: "GET",
    headers: await authHeader(),
  });
  if (!resp.ok) await handleResponseError(resp, "Failed to load history batch");
  return (await resp.json()) as ScreeningReport;
}

export async function deleteScreeningHistory(batchId: string): Promise<void> {
  const resp = await fetch(apiUrl(`/api/history/${encodeURIComponent(batchId)}`), {
    method: "DELETE",
    headers: await authHeader(),
  });
  if (!resp.ok) await handleResponseError(resp, "Failed to delete history record");
}
