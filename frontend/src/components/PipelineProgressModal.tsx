'use client';

import React from 'react';
import { Loader2, CheckCircle2, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';

interface PipelineProgressModalProps {
  isOpen: boolean;
  status: 'processing' | 'completed' | 'failed';
  onComplete: () => void;
  onClose: () => void;
}

export default function PipelineProgressModal({ isOpen, status, onComplete, onClose }: PipelineProgressModalProps) {
  if (!isOpen) return null;

  const steps = [
    { title: 'Stage 1: Document Ingestion & Classification', desc: 'Parsing Excel grids & PDF OCR pages' },
    { title: 'Stage 2: Financial Statement & TB Extraction', desc: 'Extracting line items & Trial Balance scale' },
    { title: 'Stage 3: Footing Verification & Guardrails', desc: 'Running MathEngine Footing & Assets = L+E' },
    { title: 'Stage 4: Forensics & Analytics Engine', desc: 'Altman Z-Score, Beneish M-Score & Sloan Accruals' },
    { title: 'Stage 5: Driver-Based 3-Statement & Monte Carlo', desc: 'Executing 5,000 stochastic simulation runs' },
    { title: 'Stage 6 & 7: Visualizations & Workpaper Export', desc: 'Compiling PDF report & Excel supporting workpapers' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="bg-slate-50 border-b border-slate-200 p-8 text-center relative">
          <div className="w-16 h-16 rounded-2xl bg-[#3C6E71]/10 border border-[#3C6E71]/20 flex items-center justify-center mx-auto mb-4 shadow-xs">
            {status === 'processing' && <Cpu className="w-8 h-8 text-[#3C6E71] animate-pulse" />}
            {status === 'completed' && <ShieldCheck className="w-8 h-8 text-emerald-600" />}
            {status === 'failed' && <AlertTriangle className="w-8 h-8 text-rose-600" />}
          </div>
          <h2 className="text-xl font-bold text-slate-900">
            {status === 'processing' && 'Executing Audit Engine Pipeline...'}
            {status === 'completed' && 'Audit Engine Pipeline Complete!'}
            {status === 'failed' && 'Pipeline Execution Failed'}
          </h2>
          <p className="text-sm text-slate-600 mt-1.5 leading-relaxed">
            {status === 'processing' && 'Running 7-stage deterministic math & forensic engine'}
            {status === 'completed' && 'All financial statements, ratios & workpapers generated cleanly.'}
            {status === 'failed' && 'An error occurred during statement processing.'}
          </p>
        </div>

        {/* Stepper Body */}
        <div className="p-8 space-y-6">
          <div className="space-y-4">
            {steps.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3.5">
                <div className="mt-0.5 shrink-0">
                  {status === 'processing' ? (
                    idx === 2 ? (
                      <Loader2 className="w-5 h-5 text-[#3C6E71] animate-spin" />
                    ) : idx < 2 ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    ) : (
                      <div className="w-5 h-5 rounded-full border border-slate-300 bg-slate-100" />
                    )
                  ) : status === 'completed' ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-rose-600" />
                  )}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{step.title}</h4>
                  <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Action Footer */}
          <div className="pt-4 border-t border-slate-200 flex justify-end">
            {status === 'completed' && (
              <button
                onClick={onComplete}
                className="w-full py-3 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-2"
              >
                Proceed to Audit Dashboard
              </button>
            )}
            {status === 'failed' && (
              <button
                onClick={onClose}
                className="w-full py-3 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-sm font-semibold border border-slate-200 transition-all"
              >
                Close & Review Staged Documents
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
