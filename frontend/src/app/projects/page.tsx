'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProjects, getClients, createProject, updateProject, deleteProject, createClient } from '@/lib/api';
import { Project } from '@/lib/types';
import { 
  FolderKanban, Plus, Search, Building2, Calendar, 
  ArrowRight, ShieldCheck, FileText, Loader2, Edit3, Trash2, X, AlertTriangle, CheckCircle2, RefreshCw
} from 'lucide-react';

export default function ProjectsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [activeClientId, setActiveClientId] = useState<string | null>(null);
  const [activeClientName, setActiveClientName] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProjectId, setDeletingProjectId] = useState<string | null>(null);

  // Form states for Create (2a) & Edit
  const [formTitle, setFormTitle] = useState('');
  const [formYear, setFormYear] = useState(new Date().getFullYear() - 1);
  const [formDesc, setFormDesc] = useState('');
  const [selectedClientForNew, setSelectedClientForNew] = useState('');

  useEffect(() => {
    const cid = localStorage.getItem('fsra_active_client_id');
    const cname = localStorage.getItem('fsra_active_client_name');
    if (!cid) {
      router.push('/login');
      return;
    }
    setActiveClientId(cid);
    setActiveClientName(cname);
    setSelectedClientForNew(cid);
  }, [router]);

  // Queries
  const { data: projects, isLoading: isProjectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: getClients,
  });

  const clientsMap = React.useMemo(() => {
    const map = new Map<string, string>();
    clients?.forEach((c) => map.set(c.id, c.name));
    return map;
  }, [clients]);

  // Filter projects strictly by authenticated active client + search query
  const filteredProjects = React.useMemo(() => {
    if (!projects || !activeClientId) return [];
    return projects.filter((p) => {
      const matchesClient = p.client_id === activeClientId;
      const term = searchQuery.toLowerCase();
      const matchesSearch = (
        p.title.toLowerCase().includes(term) ||
        p.audit_year.toString().includes(term)
      );
      return matchesClient && matchesSearch;
    });
  }, [projects, activeClientId, searchQuery]);

  // Create Project Mutation (2a)
  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (newProj) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setIsCreateModalOpen(false);
      resetForm();
    },
  });

  // Update Project Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; audit_year?: number; description?: string } }) =>
      updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setEditingProject(null);
      resetForm();
    },
  });

  // Delete Project Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setDeletingProjectId(null);
    },
  });

  const resetForm = () => {
    setFormTitle('');
    setFormYear(new Date().getFullYear() - 1);
    setFormDesc('');
  };

  const openCreateModal = () => {
    resetForm();
    setSelectedClientForNew(activeClientId || (clients && clients[0]?.id) || '');
    setIsCreateModalOpen(true);
  };

  const openEditModal = (proj: Project) => {
    setEditingProject(proj);
    setFormTitle(proj.title);
    setFormYear(proj.audit_year);
    setFormDesc(proj.description || '');
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim() || !selectedClientForNew) return;
    createMutation.mutate({
      title: formTitle.trim(),
      audit_year: Number(formYear),
      client_id: selectedClientForNew,
      description: formDesc.trim() || undefined,
    });
  };

  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProject || !formTitle.trim()) return;
    updateMutation.mutate({
      id: editingProject.id,
      data: {
        title: formTitle.trim(),
        audit_year: Number(formYear),
        description: formDesc.trim() || undefined,
      },
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-800 border border-emerald-300 shadow-xs">
            Cleared / Complete
          </span>
        );
      case 'in_progress':
      case 'processing':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-[#3C6E71]/10 text-[#3C6E71] border border-[#3C6E71]/30 shadow-xs animate-pulse">
            Processing...
          </span>
        );
      case 'under_review':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-50 text-amber-800 border border-amber-300 shadow-xs">
            Review Required
          </span>
        );
      case 'failed':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-rose-50 text-rose-800 border border-rose-300 shadow-xs">
            Failed
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-slate-100 text-slate-700 border border-slate-300 shadow-xs">
            Draft Stage
          </span>
        );
    }
  };

  return (
    <div className="space-y-8">
      
      {/* Page Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-6 md:p-8 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2 text-[#3C6E71] font-bold text-xs uppercase tracking-wider">
            <FolderKanban className="w-4 h-4" /> Client Audit Engagements
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            {activeClientName ? `${activeClientName} Engagements` : 'Corporate Audit Engagements'}
          </h1>
          <p className="text-sm text-slate-600 mt-1 leading-relaxed">
            Manage confidential audit packages, stage document bundles, and run the 7-Stage Audit Engine.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={openCreateModal}
            className="px-5 py-2.5 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold shadow-sm flex items-center justify-center gap-2 transition-all"
          >
            <Plus className="w-4 h-4" /> New Audit Project
          </button>
        </div>
      </div>

      {/* Search & Toolbar */}
      <div className="flex items-center gap-4 bg-white p-5 md:p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search engagements by company name, title, or fiscal year..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71] bg-slate-50 text-slate-900 font-medium"
          />
        </div>
      </div>

      {/* Projects Grid */}
      {isProjectsLoading ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <Loader2 className="w-8 h-8 text-[#3C6E71] animate-spin mb-3" />
          <p className="text-sm font-semibold text-slate-600">Loading audit engagements...</p>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300 p-8 shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-slate-50 text-slate-600 border border-slate-200 flex items-center justify-center mx-auto mb-4">
            <Building2 className="w-7 h-7 text-[#3C6E71]" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Projects Found</h3>
          <p className="text-sm text-slate-600 mt-1 max-w-sm mx-auto">
            {searchQuery ? 'No audit projects match your filter.' : 'Create your first audit project to start uploading financial statements.'}
          </p>
          {!searchQuery && (
            <button
              onClick={openCreateModal}
              className="mt-5 px-5 py-2.5 bg-[#3C6E71] text-white rounded-xl text-sm font-bold hover:bg-[#2B5356] inline-flex items-center gap-2 shadow-sm transition-all"
            >
              <Plus className="w-4 h-4" /> Create First Project
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:border-[#3C6E71] hover:shadow-md transition-all flex flex-col justify-between overflow-hidden group"
            >
              <div className="p-6 md:p-8 space-y-5">
                
                {/* Header Badge & Actions */}
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#3C6E71] bg-[#3C6E71]/10 px-3 py-1 rounded-lg border border-[#3C6E71]/20 font-mono tabular-nums">
                    <Calendar className="w-3.5 h-3.5" /> FY {project.audit_year}
                  </span>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(project.status)}
                  </div>
                </div>

                {/* Engagement Title & Corporate Name */}
                <div>
                  <h3 className="font-extrabold text-lg text-slate-900 group-hover:text-[#3C6E71] transition-colors leading-snug">
                    {project.title}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-slate-600 mt-1.5 font-semibold">
                    <Building2 className="w-4 h-4 text-[#6BA6A9]" />
                    <span>{clientsMap.get(project.client_id) || 'Corporate Client'}</span>
                  </div>
                </div>

                {/* Description Scope */}
                {project.description && (
                  <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-200 font-medium">
                    {project.description}
                  </p>
                )}

              </div>

              {/* Action Toolbar */}
              <div className="bg-slate-50 px-6 md:px-8 py-4 border-t border-slate-200 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEditModal(project)}
                    className="p-2 text-slate-600 hover:text-[#3C6E71] hover:bg-white rounded-lg transition-colors text-sm font-semibold flex items-center gap-1.5 border border-transparent hover:border-slate-200"
                    title="Update project"
                  >
                    <Edit3 className="w-4 h-4" /> Edit
                  </button>
                  <button
                    onClick={() => setDeletingProjectId(project.id)}
                    className="p-2 text-slate-600 hover:text-rose-700 hover:bg-white rounded-lg transition-colors text-sm font-semibold flex items-center gap-1.5 border border-transparent hover:border-slate-200"
                    title="Delete project"
                  >
                    <Trash2 className="w-4 h-4" /> Delete
                  </button>
                </div>

                <Link
                  href={`/projects/${project.id}`}
                  className="px-4 py-2 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  Open <ArrowRight className="w-4 h-4" />
                </Link>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Screen 2a: Create Project Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#334155]/40 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl shadow-xl border border-[#E2E8F0] w-full max-w-lg overflow-hidden animate-in fade-in duration-150">
            <div className="bg-[#F8FAFC] border-b border-[#E2E8F0] px-6 py-4 flex items-center justify-between">
              <h2 className="font-bold text-base text-[#334155] flex items-center gap-2">
                <Plus className="w-4 h-4 text-[#3C6E71]" /> Create New Audit Project (Screen 2a)
              </h2>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-[#64748B] hover:text-[#334155]">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#334155] uppercase tracking-wider mb-1">
                  Corporate Client Entity <span className="text-red-500">*</span>
                </label>
                <select
                  value={selectedClientForNew}
                  onChange={(e) => setSelectedClientForNew(e.target.value)}
                  required
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] text-[#334155] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                >
                  <option value="">Select client...</option>
                  {clients?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} {c.industry ? `(${c.industry})` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-[#334155] uppercase tracking-wider mb-1">
                  Project Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. FY 2024 Financial Statement Audit"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] text-[#334155] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#334155] uppercase tracking-wider mb-1">
                  Audit Fiscal Year <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  required
                  min={2000}
                  max={2030}
                  value={formYear}
                  onChange={(e) => setFormYear(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] text-[#334155] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#334155] uppercase tracking-wider mb-1">
                  Scope / Description
                </label>
                <textarea
                  rows={3}
                  placeholder="Scope, engagement notes or auditing instructions..."
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] text-[#334155] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>
              <div className="pt-3 border-t border-[#E2E8F0] flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-[#64748B] hover:text-[#334155]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-xs font-semibold shadow-sm flex items-center gap-1.5"
                >
                  {createMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Project Modal */}
      {editingProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#334155]/40 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl shadow-xl border border-[#E2E8F0] w-full max-w-lg overflow-hidden animate-in fade-in duration-150">
            <div className="bg-[#F8FAFC] border-b border-[#E2E8F0] px-6 py-4 flex items-center justify-between">
              <h2 className="font-bold text-base text-[#334155] flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-[#3C6E71]" /> Update Audit Project Details
              </h2>
              <button onClick={() => setEditingProject(null)} className="text-[#64748B] hover:text-[#334155]">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleUpdateSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#334155] uppercase tracking-wider mb-1">
                  Project Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] text-[#334155] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#334155] uppercase tracking-wider mb-1">
                  Audit Fiscal Year <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  required
                  min={2000}
                  max={2030}
                  value={formYear}
                  onChange={(e) => setFormYear(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] text-[#334155] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#334155] uppercase tracking-wider mb-1">
                  Scope / Description
                </label>
                <textarea
                  rows={3}
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-[#E2E8F0] text-[#334155] rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>
              <div className="pt-3 border-t border-[#E2E8F0] flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingProject(null)}
                  className="px-4 py-2 text-xs font-semibold text-[#64748B] hover:text-[#334155]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-xs font-semibold shadow-sm flex items-center gap-1.5"
                >
                  {updateMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingProjectId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#334155]/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-[#E2E8F0] w-full max-w-sm p-6 space-y-4">
            <div className="flex items-center gap-3 text-[#DC2626]">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="font-bold text-base text-[#334155]">Delete Audit Project?</h3>
            </div>
            <p className="text-xs text-[#64748B]">
              Are you sure you want to delete this project? All uploaded documents, audit results, and workpapers will be permanently removed.
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setDeletingProjectId(null)}
                className="px-3.5 py-2 text-xs font-medium text-[#64748B] hover:text-[#334155]"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteMutation.mutate(deletingProjectId)}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-[#DC2626] hover:bg-red-700 text-white rounded-xl text-xs font-semibold shadow-sm flex items-center gap-1.5"
              >
                {deleteMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Delete Project
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
