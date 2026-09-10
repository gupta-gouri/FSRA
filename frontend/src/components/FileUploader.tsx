'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, FileText, AlertCircle, Loader2 } from 'lucide-react';

interface FileUploaderProps {
  onFileUpload: (file: File) => Promise<void>;
  onFilesUpload?: (files: File[]) => Promise<void>;
  isUploading: boolean;
}

export default function FileUploader({ onFileUpload, onFilesUpload, isUploading }: FileUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [uploadProgressText, setUploadProgressText] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['xlsx', 'xls', 'pdf'];

  const validateAndUploadFiles = async (files: FileList | File[]) => {
    setErrorMsg(null);
    const fileList = Array.from(files);
    if (fileList.length === 0) return;

    // Validate all files
    for (const file of fileList) {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      if (!allowedExtensions.includes(ext)) {
        setErrorMsg(`Invalid file format for "${file.name}". Accepted formats: Excel (.xlsx, .xls) or PDF (.pdf)`);
        return;
      }

      if (file.size === 0) {
        setErrorMsg(`Selected file "${file.name}" is empty.`);
        return;
      }
    }

    try {
      if (onFilesUpload) {
        await onFilesUpload(fileList);
      } else {
        // Sequentially upload if only onFileUpload is provided
        for (let i = 0; i < fileList.length; i++) {
          const file = fileList[i];
          if (fileList.length > 1) {
            setUploadProgressText(`Uploading ${i + 1} of ${fileList.length}: ${file.name}...`);
          }
          await onFileUpload(file);
        }
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Document upload failed.');
    } finally {
      setUploadProgressText(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndUploadFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndUploadFiles(e.target.files);
      e.target.value = '';
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 md:p-10 text-center cursor-pointer transition-all ${
          isDragOver
            ? 'border-[#3C6E71] bg-[#3C6E71]/5 scale-[0.99]'
            : 'border-slate-300 hover:border-[#3C6E71]/60 bg-slate-50 hover:bg-white'
        } ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />

        <div className="max-w-md mx-auto flex flex-col items-center gap-3.5">
          <div className="w-14 h-14 rounded-2xl bg-[#3C6E71]/10 text-[#3C6E71] border border-[#3C6E71]/20 flex items-center justify-center shadow-xs">
            {isUploading ? (
              <Loader2 className="w-7 h-7 animate-spin" />
            ) : (
              <UploadCloud className="w-7 h-7" />
            )}
          </div>

          <div>
            <p className="text-sm font-bold text-slate-900">
              {uploadProgressText || (isUploading ? 'Uploading Financial Statement Package...' : 'Click to browse or drag & drop files here')}
            </p>
            <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
              Select multiple files simultaneously. Supports Excel (<span className="font-mono text-[#3C6E71] font-bold">.xlsx, .xls</span>) and PDF (<span className="font-mono text-[#3C6E71] font-bold">.pdf</span>)
            </p>
          </div>

          <div className="flex items-center justify-center gap-4 text-xs text-slate-600 font-semibold pt-2">
            <span className="flex items-center gap-1.5"><FileSpreadsheet className="w-4 h-4 text-[#3C6E71]" /> Balance Sheets / P&L</span>
            <span className="flex items-center gap-1.5"><FileText className="w-4 h-4 text-[#6BA6A9]" /> Trial Balances & Notes</span>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="mt-3 p-4 bg-rose-50 border border-rose-300 rounded-2xl flex items-center gap-2.5 text-xs font-bold text-rose-800 shadow-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
}

