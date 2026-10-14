import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TalentLens — AI Candidate Screening & Ranking",
  description: "AI Candidate Screening & Ranking across Full-Stack, AI/ML, Data Analysis, and Engineering roles.",
  icons: { icon: "/logo.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen antialiased bg-neutral-50 text-neutral-900 dark:bg-black dark:text-neutral-100 transition-colors duration-200">
        {children}
      </body>
    </html>
  );
}
