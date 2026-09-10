'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getClients, createProject, createClient } from '@/lib/api';
import { X, Plus, Building2, Calendar, FileText, Loader2 } from 'lucide-react';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (projectId: string) => void;
}

export default function CreateProjectModal({ isOpen, onClose, onSuccess }: CreateProjectModalProps) {
  const queryClient = useQueryClient();
  
  const [title, setTitle] = useState('');
  const [auditYear, setAuditYear] = useState(new Date().getFullYear() - 1);
  const [clientId, setClientId] = useState('');
  const [description, setDescription] = useState('');

  // New Client write-in state
  const [isAddingNewClient, setIsAddingNewClient] = useState(false);
  const [newClientName, setNewClientName] = useState('');
  const [newClientIndustry, setNewClientIndustry] = useState('');

  const { data: clients, isLoading: isClientsLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: getClients,
    enabled: isOpen,
  });

  const createClientMutation = useMutation({
    mutationFn: createClient,
    onSuccess: (newClient) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      setClientId(newClient.id);
      setIsAddingNewClient(false);
    },
  });

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      onSuccess(newProject.id);
      onClose();
    },
  });

  if (!isOpen) return null;

  const handleAddNewClientSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClientName.trim()) return;
    createClientMutation.mutate({
      name: newClientName.trim(),
      industry: newClientIndustry.trim() || undefined,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !clientId) return;

    createProjectMutation.mutate({
      title: title.trim(),
      audit_year: Number(auditYear),
      client_id: clientId,
      description: description.trim() || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 overflow-y-auto animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-150">
        
        {/* Modal Header */}
        <div className="bg-slate-50 border-b border-slate-200 px-8 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#3C6E71]/10 border border-[#3C6E71]/20 text-[#3C6E71] flex items-center justify-center shadow-xs">
              <Plus className="w-5 h-5" />
            </div>
            <h2 className="font-extrabold text-lg text-slate-900">New Audit Engagement</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body Form */}
        <form onSubmit={handleSubmit} className="p-8 space-y-5">
          
          {/* Client Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Client / Corporate Entity <span className="text-rose-600">*</span>
            </label>
            
            {!isAddingNewClient ? (
              <div className="flex gap-2.5">
                <select
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                >
                  <option value="">Select a registered client...</option>
                  {clients?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} {c.industry ? `(${c.industry})` : ''}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => setIsAddingNewClient(true)}
                  className="px-4 py-3 bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-300 rounded-xl text-xs font-bold flex items-center gap-1.5 whitespace-nowrap transition-colors"
                >
                  <Plus className="w-4 h-4 text-[#3C6E71]" /> Add Client
                </button>
              </div>
            ) : (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
                <div className="flex justify-between items-center text-xs font-bold text-slate-800">
                  <span>Register New Corporate Entity</span>
                  <button
                    type="button"
                    onClick={() => setIsAddingNewClient(false)}
                    className="text-slate-500 hover:text-slate-800 text-xs"
                  >
                    Cancel
                  </button>
                </div>
                <input
                  type="text"
                  placeholder="Corporate Name (e.g. Acme Steel Ltd)"
                  value={newClientName}
                  onChange={(e) => setNewClientName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#3C6E71]"
                />
                <input
                  type="text"
                  placeholder="Industry (e.g. Manufacturing)"
                  value={newClientIndustry}
                  onChange={(e) => setNewClientIndustry(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:ring-2 focus:ring-[#3C6E71]"
                />
                <button
                  type="button"
                  onClick={handleAddNewClientSubmit}
                  disabled={createClientMutation.isPending || !newClientName.trim()}
                  className="w-full py-2.5 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-sm"
                >
                  {createClientMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                  Save & Select Client
                </button>
              </div>
            )}
          </div>

          {/* Project Title */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Engagement Title <span className="text-rose-600">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. FY 2024 Annual Financial Audit"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
            />
          </div>

          {/* Audit Fiscal Year */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Audit Fiscal Year <span className="text-rose-600">*</span>
            </label>
            <input
              type="number"
              required
              min={2000}
              max={2030}
              value={auditYear}
              onChange={(e) => setAuditYear(Number(e.target.value))}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-mono tabular-nums font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
            />
          </div>

          {/* Scope / Description */}
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
              Scope / Description
            </label>
            <textarea
              rows={3}
              placeholder="Provide context, audit scope, or notes for this engagement cycle..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
            />
          </div>

          {/* Submit Actions */}
          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-slate-600 hover:text-slate-900 text-sm font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createProjectMutation.isPending || !title.trim() || !clientId}
              className="px-6 py-2.5 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold shadow-sm flex items-center gap-2 disabled:opacity-50 transition-all"
            >
              {createProjectMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Engagement
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
