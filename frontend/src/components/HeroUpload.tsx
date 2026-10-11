"use client";

import { useRef, useState, type DragEvent } from "react";

interface Props {
  busy: boolean;
  onRunUpload: (files: File[]) => void;
  onRunSample: () => void;
}

const ACCEPT = /\.(pdf|docx|txt|doc|md)$/i;

export default function HeroUpload({ busy, onRunUpload, onRunSample }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  function handleFiles(list: FileList | null) {
    if (!list) return;
    let valid = Array.from(list).filter((f) => ACCEPT.test(f.name));
    if (valid.length === 0) {
      alert("Please select supported resume files (PDF, DOCX, TXT).");
      return;
    }
    if (valid.length > 100) {
      alert("Notice: Maximum 100 resumes per batch. First 100 selected.");
      valid = valid.slice(0, 100);
    }
    setSelectedFiles(valid);
    // Automatically trigger screening
    onRunUpload(valid);
  }

  function handleDrag(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }

  return (
    <section id="ingest-box" className="py-6 sm:py-10">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
        
        {/* Left Column: Recruiter Illustration & Bold Heading */}
        <div className="lg:col-span-7 space-y-6">
          <div className="max-w-md mx-auto lg:mx-0">
            <img
              src="/hero-recruiter.png"
              alt="Recruiter reviewing stacks of resumes"
              className="w-full h-auto max-h-[290px] object-contain drop-shadow-md select-none"
            />
          </div>

          <div className="space-y-3">
            <h1 className="text-3xl sm:text-4xl lg:text-[44px] font-extrabold text-neutral-900 dark:text-white tracking-tight leading-[1.18]">
              Remove confusion to pick the best candidate for jobs
            </h1>
            <div className="flex items-center gap-2 pt-1 text-sm sm:text-base font-medium text-neutral-600 dark:text-neutral-400">
              <span>100% Automatically and</span>
              <span className="bg-[#0066FF] text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-sm">
                Free
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Clean Elevated Upload Card (remove.bg style) */}
        <div className="lg:col-span-5 flex justify-center lg:justify-end">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`w-full max-w-md bg-white dark:bg-neutral-900 border ${
              dragActive
                ? "border-[#0066FF] ring-4 ring-[#0066FF]/20 bg-blue-50/20 dark:bg-blue-950/20"
                : "border-neutral-200/90 dark:border-neutral-800"
            } rounded-3xl p-8 sm:p-10 text-center shadow-xl dark:shadow-2xl/40 transition-all duration-200 flex flex-col items-center justify-center min-h-[320px]`}
          >
            {/* Hidden native inputs */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.doc"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <input
              ref={folderInputRef}
              type="file"
              multiple
              // @ts-expect-error webkitdirectory is supported in browsers
              webkitdirectory=""
              directory=""
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />

            {/* Main Action: Big Blue "Upload Resume" Button */}
            <button
              type="button"
              disabled={busy}
              onClick={() => fileInputRef.current?.click()}
              className="w-full max-w-[260px] py-3.5 px-6 rounded-full bg-[#0066FF] hover:bg-[#0052CC] active:bg-[#0047b3] text-white font-bold text-base shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              <span>Upload Resume</span>
            </button>

            {/* Drop helper text */}
            <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400 mt-5">
              or drop a file,
            </p>
            <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-0.5">
              PDF, DOCX, or TXT (up to 100 resumes)
            </p>

            {/* Secondary options */}
            <div className="flex items-center justify-center gap-2 mt-4 text-xs">
              <button
                type="button"
                onClick={() => folderInputRef.current?.click()}
                disabled={busy}
                className="text-[#0066FF] dark:text-blue-400 hover:underline font-semibold"
              >
                Select Folder
              </button>
              <span className="text-neutral-300 dark:text-neutral-700">•</span>
              <button
                type="button"
                onClick={onRunSample}
                disabled={busy}
                className="text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white underline"
              >
                ⚡ Try 50 Samples
              </button>
            </div>

            {/* Selected files feedback */}
            {selectedFiles.length > 0 && (
              <div className="mt-4 px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs text-blue-700 dark:text-blue-300 font-medium">
                ✓ Processing {selectedFiles.length} resume(s)…
              </div>
            )}
          </div>
        </div>

      </div>
    </section>
  );
}
