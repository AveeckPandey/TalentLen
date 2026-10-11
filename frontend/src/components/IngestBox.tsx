"use client";

import { useRef, useState } from "react";
import { Badge, Button, Card } from "./ui";

interface Props {
  busy: boolean;
  onRun: (files: File[]) => void;
}

const ACCEPT = /\.(pdf|docx|txt|doc|md)$/i;

export default function IngestBox({ busy, onRun }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const folderRef = useRef<HTMLInputElement>(null);
  const filesRef = useRef<HTMLInputElement>(null);

  function pick(list: FileList | null) {
    if (!list) return;
    let picked = Array.from(list).filter((f) => ACCEPT.test(f.name));
    if (picked.length > 100) {
      alert("Notice: Batch capped at 100 resumes. First 100 selected.");
      picked = picked.slice(0, 100);
    }
    setFiles(picked);
  }

  return (
    <Card id="ingest-box" className="max-w-2xl mx-auto p-6 rounded-2xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Ingest Resumes</h2>
        <Badge size="xs" pill className="font-semibold">
          Up to 100 Files
        </Badge>
      </div>
      <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-4">
        Upload a resume folder (PDF, DOCX, TXT) or individual files for batch screening.
      </p>

      <div
        onClick={() => folderRef.current?.click()}
        className="border-2 border-dashed border-neutral-300 dark:border-neutral-700 hover:border-neutral-500 dark:hover:border-neutral-400 rounded-xl p-8 text-center cursor-pointer transition bg-neutral-50/50 dark:bg-black/40 hover:bg-neutral-100/50 dark:hover:bg-neutral-800/40"
      >
        <p className="text-sm font-medium text-neutral-800 dark:text-neutral-200">Click to select folder or files</p>
        <p className="text-xs text-neutral-500 mt-1">PDF, DOCX, TXT supported</p>
        <input ref={folderRef} type="file" multiple className="hidden" onChange={(e) => pick(e.target.files)} />
        <input ref={filesRef} type="file" multiple className="hidden" onChange={(e) => pick(e.target.files)} />
      </div>
      <div className="flex justify-center space-x-4 mt-3">
        <Button variant="link" size="none" onClick={() => folderRef.current?.click()} className="text-xs text-neutral-600 dark:text-neutral-300">
          Select Folder
        </Button>
        <span className="text-neutral-400 dark:text-neutral-600">•</span>
        <Button variant="link" size="none" onClick={() => filesRef.current?.click()} className="text-xs text-neutral-600 dark:text-neutral-300">
          Select Files
        </Button>
      </div>
      {files.length > 0 && (
        <div className="mt-3 text-xs text-neutral-600 dark:text-neutral-400 text-center">✓ Selected {files.length} resume(s)</div>
      )}

      <Button
        variant="primary"
        size="lg"
        onClick={() => onRun(files)}
        disabled={busy}
        className="w-full mt-5 font-bold rounded-xl shadow-sm"
      >
        Run Screening &amp; Ranking
      </Button>
    </Card>
  );
}
