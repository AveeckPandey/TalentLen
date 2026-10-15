/** @type {import('next').NextConfig} */
const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const PASSTHROUGH = [
  "/screen",
  "/upload_and_screen",
  "/results",
  "/clear",
  "/health",
  "/me",
  "/config.js",
  "/download_csv",
  "/download_excel",
  "/download_docx",
  "/export_filtered_excel",
  "/export_filtered_docx",
];

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      ...PASSTHROUGH.map((source) => ({
        source,
        destination: `${API_URL}${source}`,
      })),
      { source: "/resumes/:path*", destination: `${API_URL}/resumes/:path*` },
      { source: "/api/:path*", destination: `${API_URL}/api/:path*` },
    ];
  },
};

export default nextConfig;
