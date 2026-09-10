'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProjectById, getFilesForProject, uploadFile, deleteFile, runAuditPipeline, getClients } from '@/lib/api';
import FileUploader from '@/components/FileUploader';
import PipelineProgressModal from '@/components/PipelineProgressModal';
import { 
  ArrowLeft, FileSpreadsheet, FileText, X, Play, 
  ShieldCheck, Loader2, Calendar, Building2, AlertCircle, FileCheck
} from 'lucide-react';

export default function DocumentIngestionPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const queryClient = useQueryClient();

  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<'processing' | 'completed' | 'failed'>('processing');

  // Fetch Project Info
  const { data: project, isLoading: isProjectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId),
    refetchInterval: isProcessing ? 2000 : false,
  });

  // Fetch Clients for company lookup
  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: getClients,
  });

  const clientName = React.useMemo(() => {
    if (!project || !clients) return '';
    return clients.find((c) => c.id === project.client_id)?.name || '';
  }, [project, clients]);

  // Fetch Uploaded Files
  const { data: files, isLoading: isFilesLoading } = useQuery({
    queryKey: ['files', projectId],
    queryFn: () => getFilesForProject(projectId),
  });

  // Upload File Mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadFile(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files', projectId] });
    },
  });

  // Delete File Mutation
  const deleteMutation = useMutation({
    mutationFn: (fileId: string) => deleteFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files', projectId] });
    },
  });

  // Run Audit Pipeline Mutation
  const runAuditMutation = useMutation({
    mutationFn: () => runAuditPipeline(projectId),
    onSuccess: () => {
      setIsProcessing(true);
      setPipelineStatus('processing');
    },
  });

  // Monitor status polling
  useEffect(() => {
    if (project?.status === 'completed') {
      setPipelineStatus('completed');
    } else if (project?.status === 'failed') {
      setPipelineStatus('failed');
    }
  }, [project?.status]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isProjectLoading) {
    return (
      <div className="flex items-center justify-center py-20 bg-white rounded-2xl border border-[#E2E8F0]">
        <Loader2 className="w-8 h-8 text-[#3C6E71] animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-6 md:p-8 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <Link
            href="/projects"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-[#3C6E71] transition-colors mb-2"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Engagements Hub
          </Link>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-xl text-xs font-bold bg-[#3C6E71]/10 text-[#3C6E71] border border-[#3C6E71]/20 font-mono tabular-nums">
              FY {project?.audit_year}
            </span>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">{project?.title}</h1>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-600 mt-1.5">
            <Building2 className="w-4 h-4 text-[#3C6E71]" />
            <span>{clientName || 'Corporate Client'}</span>
          </div>
        </div>

        <div className="flex items-center gap-3.5">
          <Link
            href={`/projects/${projectId}/dashboard`}
            className="px-5 py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-800 rounded-xl text-sm font-bold transition-all border border-slate-200 flex items-center gap-2"
          >
            View Dashboard
          </Link>

          <button
            onClick={() => runAuditMutation.mutate()}
            disabled={!files || files.length === 0 || runAuditMutation.isPending || isProcessing}
            className="px-6 py-2.5 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold shadow-sm flex items-center gap-2 disabled:opacity-50 transition-all"
          >
            {runAuditMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4 fill-white" />
            )}
            RUN AUDIT
          </button>
        </div>
      </div>

      {/* Screen 3: Upload Zone & Staged Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        
        {/* Drag and Drop Upload Area */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white p-6 md:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2">
              <FileCheck className="w-6 h-6 text-[#3C6E71]" /> Document Ingestion
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Upload Balance Sheets, Income Statements, Trial Balances, Notes or PDF packages for this audit cycle.
            </p>

            <FileUploader
              onFileUpload={async (file) => {
                await uploadMutation.mutateAsync(file);
              }}
              onFilesUpload={async (files) => {
                for (const file of files) {
                  await uploadMutation.mutateAsync(file);
                }
                queryClient.invalidateQueries({ queryKey: ['files', projectId] });
              }}
              isUploading={uploadMutation.isPending}
            />
          </div>
        </div>

        {/* Uploaded Documents List with top-right X remove option */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 px-6 md:px-8 py-5 flex items-center justify-between">
              <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#3C6E71]" /> Staged Documents ({files?.length || 0})
              </h3>
              <span className="text-xs font-semibold text-slate-600">Ready for Audit Pipeline Engine</span>
            </div>

            {isFilesLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-7 h-7 text-[#3C6E71] animate-spin" />
              </div>
            ) : !files || files.length === 0 ? (
              <div className="text-center py-16 p-8">
                <AlertCircle className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                <p className="text-sm font-bold text-slate-900">No documents staged for this audit engagement.</p>
                <p className="text-xs text-slate-600 mt-1">Upload Excel workbooks or PDF files on the left to activate the audit runner.</p>
              </div>
            ) : (
              <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
                {files.map((file) => (
                  <div 
                    key={file.id} 
                    className="relative bg-slate-50 border border-slate-200 rounded-2xl p-5 flex items-start gap-4 hover:shadow-sm transition-all group"
                  >
                    {/* Top-Right Corner Small Cross Removal Button */}
                    <button
                      onClick={() => deleteMutation.mutate(file.id)}
                      disabled={deleteMutation.isPending}
                      className="absolute top-3 right-3 p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-full transition-colors"
                      title="Remove uploaded document"
                    >
                      <X className="w-4 h-4" />
                    </button>

                    <div className="w-12 h-12 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 shadow-xs">
                      {file.file_type === 'pdf' ? (
                        <FileText className="w-6 h-6 text-rose-600" />
                      ) : (
                        <FileSpreadsheet className="w-6 h-6 text-emerald-600" />
                      )}
                    </div>

                    <div className="pr-6 space-y-1.5 overflow-hidden">
                      <h4 className="text-sm font-bold text-slate-900 truncate" title={file.filename}>
                        {file.filename}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-slate-600 font-medium">
                        <span className="uppercase font-mono font-bold text-[#3C6E71]">{file.file_type}</span>
                        <span>•</span>
                        <span className="tabular-nums">{formatBytes(file.file_size_bytes)}</span>
                      </div>
                      <span className="inline-block text-xs font-extrabold uppercase px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-300">
                        {file.status}
                      </span>
                    </div>

                  </div>
                ))}
              </div>
            )}

            {/* Run Audit Callout */}
            {files && files.length > 0 && (
              <div className="p-6 bg-[#3C6E71]/5 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2.5 text-sm font-semibold text-[#3C6E71]">
                  <ShieldCheck className="w-5 h-5 shrink-0 text-[#3C6E71]" />
                  <span>{files.length} document(s) staged. Click "RUN AUDIT" to trigger the 7-stage engine.</span>
                </div>
                <button
                  onClick={() => runAuditMutation.mutate()}
                  disabled={runAuditMutation.isPending || isProcessing}
                  className="w-full sm:w-auto px-6 py-3 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-2 shrink-0"
                >
                  <Play className="w-4 h-4 fill-white" /> RUN AUDIT
                </button>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Screen 4: Progress Stepper Modal */}
      <PipelineProgressModal
        isOpen={isProcessing}
        status={pipelineStatus}
        onComplete={() => {
          setIsProcessing(false);
          router.push(`/projects/${projectId}/dashboard`);
        }}
        onClose={() => setIsProcessing(false)}
      />

    </div>
  );
}
