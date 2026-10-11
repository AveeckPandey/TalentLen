"use client";

import { Button, Modal } from "./ui";

interface PricingModalProps {
  open: boolean;
  onClose: () => void;
  onSelectPlan?: (plan: string) => void;
}

export default function PricingModal({ open, onClose, onSelectPlan }: PricingModalProps) {
  return (
    <Modal open={open} onClose={onClose} panelClassName="max-w-3xl" overlayClassName="bg-black/80" zClassName="z-[60]">
      <div className="w-full bg-neutral-900 border border-neutral-700 rounded-2xl p-6 sm:p-8 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">TalentLens Plans &amp; Pricing</h2>
            <p className="text-xs sm:text-sm text-neutral-400 mt-1">
              Automated AI candidate screening built for high-volume engineering hiring.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-800 transition flex items-center justify-center text-sm"
          >
            ✕
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Free Tier */}
          <div className="bg-neutral-950/60 border border-neutral-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
            <div>
              <div className="inline-block px-2.5 py-0.5 text-[11px] font-semibold rounded-full bg-neutral-800 text-neutral-300 mb-2">
                Starter
              </div>
              <div className="text-2xl font-bold text-white">$0 <span className="text-xs font-normal text-neutral-400">/mo</span></div>
              <p className="text-xs text-neutral-400 mt-1">For recruiters testing small resume batches.</p>
              <ul className="text-xs text-neutral-300 mt-4 space-y-2">
                <li className="flex items-center gap-2">✓ Up to 50 resumes/batch</li>
                <li className="flex items-center gap-2">✓ Heuristic scoring engine</li>
                <li className="flex items-center gap-2">✓ CSV &amp; JSON exports</li>
                <li className="flex items-center gap-2">✓ Interactive CGPA dialer</li>
              </ul>
            </div>
            <Button
              variant="dark"
              size="sm"
              onClick={onClose}
              className="w-full font-medium rounded-lg text-xs"
            >
              Current Plan
            </Button>
          </div>

          {/* Pro Tier (Popular) */}
          <div className="bg-neutral-900 border-2 border-white rounded-xl p-5 flex flex-col justify-between space-y-4 relative shadow-lg">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 text-[10px] font-bold rounded-full bg-white text-black tracking-wide uppercase">
              Most Popular
            </span>
            <div>
              <div className="inline-block px-2.5 py-0.5 text-[11px] font-semibold rounded-full bg-neutral-800 text-white mb-2">
                Recruiter Pro
              </div>
              <div className="text-2xl font-bold text-white">$29 <span className="text-xs font-normal text-neutral-400">/mo</span></div>
              <p className="text-xs text-neutral-300 mt-1">Complete AI multi-agent evaluations.</p>
              <ul className="text-xs text-neutral-200 mt-4 space-y-2">
                <li className="flex items-center gap-2 font-medium">✓ Unlimited resume batches</li>
                <li className="flex items-center gap-2 font-medium">✓ Multi-Agent LLM (Groq / Qwen / Claude)</li>
                <li className="flex items-center gap-2">✓ 50–100 word narrative evaluations</li>
                <li className="flex items-center gap-2">✓ GitHub cohort verification</li>
                <li className="flex items-center gap-2">✓ Excel (.xlsx) &amp; Word (.docx) exports</li>
                <li className="flex items-center gap-2">✓ Supabase cloud team sync</li>
              </ul>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                if (onSelectPlan) onSelectPlan("pro");
                alert("Redirecting to Pro activation checkout...");
                onClose();
              }}
              className="w-full font-bold rounded-lg text-xs"
            >
              Upgrade to Pro
            </Button>
          </div>

          {/* Enterprise */}
          <div className="bg-neutral-950/60 border border-neutral-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
            <div>
              <div className="inline-block px-2.5 py-0.5 text-[11px] font-semibold rounded-full bg-neutral-800 text-neutral-300 mb-2">
                Enterprise
              </div>
              <div className="text-2xl font-bold text-white">Custom</div>
              <p className="text-xs text-neutral-400 mt-1">For talent teams and automated ATS workflows.</p>
              <ul className="text-xs text-neutral-300 mt-4 space-y-2">
                <li className="flex items-center gap-2">✓ ATS integration (Greenhouse, Lever)</li>
                <li className="flex items-center gap-2">✓ Custom scoring weights &amp; rules</li>
                <li className="flex items-center gap-2">✓ Private LLM deployment</li>
                <li className="flex items-center gap-2">✓ Dedicated account manager &amp; SLA</li>
              </ul>
            </div>
            <Button
              variant="dark"
              size="sm"
              onClick={() => {
                window.open("mailto:aveeckkumarpandey@gmail.com?subject=TalentLens Enterprise Inquiry", "_blank");
                onClose();
              }}
              className="w-full font-medium rounded-lg text-xs"
            >
              Contact Sales
            </Button>
          </div>
        </div>

        <p className="text-[11px] text-neutral-500 text-center">
          All plans include full GDPR/privacy compliance. Resumes are processed securely and never shared with third parties.
        </p>
      </div>
    </Modal>
  );
}
