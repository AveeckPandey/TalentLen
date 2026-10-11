"use client";

import type { CandidateResult } from "@/lib/types";
import { resumeUrl } from "@/lib/api";
import { Button, Modal } from "./ui";

export default function ResumeModal({
  candidate,
  onClose,
}: {
  candidate: CandidateResult | null;
  onClose: () => void;
}) {
  return (
    <Modal open={candidate !== null} onClose={onClose} panelClassName="max-w-5xl" overlayClassName="bg-black/90">
      {candidate && (
        <ResumePanel candidate={candidate} onClose={onClose} />
      )}
    </Modal>
  );
}

function ResumePanel({ candidate, onClose }: { candidate: CandidateResult; onClose: () => void }) {
  const url = resumeUrl(candidate.file_name);
  return (
    <div className="bg-neutral-950 border border-neutral-800 rounded-2xl w-full h-[92vh] flex flex-col shadow-2xl overflow-hidden">
      <div className="px-5 py-3.5 border-b border-neutral-800 flex items-center justify-between bg-black">
        <div>
          <h3 className="text-sm font-bold text-white">{candidate.candidate_name || "Original Resume"}</h3>
          <p className="text-xs text-neutral-400 font-mono">{candidate.file_name}</p>
        </div>
        <div className="flex items-center space-x-2">
          <a href={url} target="_blank" rel="noreferrer" className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 transition">
            Open in New Tab
          </a>
          <a href={url} download={candidate.file_name} className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-neutral-200 text-black transition">
            Download Original PDF
          </a>
          <Button size="none" onClick={onClose} className="w-8 h-8 rounded-lg text-neutral-400 hover:text-white">
            ✕
          </Button>
        </div>
      </div>
      <div className="flex-1 bg-black relative">
        <iframe src={url} className="w-full h-full border-0" title={candidate.file_name} />
      </div>
    </div>
  );
}
