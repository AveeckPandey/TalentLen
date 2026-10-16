import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/**
 * Keep-alive endpoint invoked automatically by Vercel Cron or monitoring services
 * every 5 minutes to prevent the Render backend free tier from idling into cold sleep.
 */
export async function GET() {
  const targetUrl =
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "https://backend-talentlens.onrender.com";
  const healthEndpoint = `${targetUrl.replace(/\/+$/, "")}/health`;
  const startTime = Date.now();

  try {
    const res = await fetch(healthEndpoint, {
      method: "GET",
      cache: "no-store",
      headers: {
        "User-Agent": "TalentLens-Vercel-Cron/1.0",
      },
    });

    const elapsed = Date.now() - startTime;
    let data: any = null;
    try {
      data = await res.json();
    } catch {
      data = { status: res.statusText };
    }

    return NextResponse.json({
      status: "ok",
      endpoint: healthEndpoint,
      backend_status: res.status,
      latency_ms: elapsed,
      backend_response: data,
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    const elapsed = Date.now() - startTime;
    return NextResponse.json(
      {
        status: "error",
        endpoint: healthEndpoint,
        latency_ms: elapsed,
        error: err.message || "Failed to reach backend",
        timestamp: new Date().toISOString(),
      },
      { status: 502 }
    );
  }
}
