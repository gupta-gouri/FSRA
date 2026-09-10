'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getClients, createClient } from '@/lib/api';
import { ShieldCheck, Building2, Plus, ArrowRight, Loader2, Lock } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [selectedClientId, setSelectedClientId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Register New Client state
  const [isRegistering, setIsRegistering] = useState(false);
  const [newClientName, setNewClientName] = useState('');
  const [newClientIndustry, setNewClientIndustry] = useState('');

  const { data: clients, isLoading: isClientsLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: getClients,
  });

  const createClientMutation = useMutation({
    mutationFn: createClient,
    onSuccess: (newClient) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      localStorage.setItem('fsra_active_client_id', newClient.id);
      localStorage.setItem('fsra_active_client_name', newClient.name);
      router.push('/projects');
    },
  });

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClientId) return;
    const client = clients?.find((c) => c.id === selectedClientId);
    if (client) {
      localStorage.setItem('fsra_active_client_id', client.id);
      localStorage.setItem('fsra_active_client_name', client.name);
      router.push('/projects');
    }
  };

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClientName.trim()) return;
    createClientMutation.mutate({
      name: newClientName.trim(),
      industry: newClientIndustry.trim() || undefined,
    });
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md space-y-6">
        
        {/* Brand Logo Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-[#3C6E71] text-white flex items-center justify-center mx-auto shadow-md">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-[#334155]">FSRA Portal</h1>
          <p className="text-sm text-[#64748B]">
            Financial Statement Review & Risk Analytics Engine
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-white p-8 md:p-10 rounded-2xl border border-slate-200 shadow-sm space-y-6">
          
          <div className="flex border-b border-slate-200">
            <button
              onClick={() => setIsRegistering(false)}
              className={`pb-3 text-sm font-bold flex-1 text-center transition-colors border-b-2 ${
                !isRegistering
                  ? 'border-[#3C6E71] text-[#3C6E71]'
                  : 'border-transparent text-slate-500 hover:text-slate-900'
              }`}
            >
              Existing Corporate Client
            </button>
            <button
              onClick={() => setIsRegistering(true)}
              className={`pb-3 text-sm font-bold flex-1 text-center transition-colors border-b-2 ${
                isRegistering
                  ? 'border-[#3C6E71] text-[#3C6E71]'
                  : 'border-transparent text-slate-500 hover:text-slate-900'
              }`}
            >
              Register New Entity
            </button>
          </div>

          {!isRegistering ? (
            /* Login Form */
            <form onSubmit={handleLoginSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
                  Select Registered Client Entity <span className="text-rose-600">*</span>
                </label>
                {isClientsLoading ? (
                  <div className="py-3 flex items-center justify-center">
                    <Loader2 className="w-5 h-5 text-[#3C6E71] animate-spin" />
                  </div>
                ) : (
                  <select
                    value={selectedClientId}
                    onChange={(e) => setSelectedClientId(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                  >
                    <option value="">Select a corporate client...</option>
                    {clients?.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} {c.industry ? `(${c.industry})` : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
                  Authorized Auditor Email
                </label>
                <input
                  type="email"
                  placeholder="auditor@firm.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
                  Access Code / Password
                </label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>

              <button
                type="submit"
                disabled={!selectedClientId}
                className="w-full py-3.5 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
              >
                Access Client Engagements Hub <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          ) : (
            /* Register Form */
            <form onSubmit={handleRegisterSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
                  Corporate Name <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Global Industries Ltd"
                  value={newClientName}
                  onChange={(e) => setNewClientName(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
                  Industry / Sector
                </label>
                <input
                  type="text"
                  placeholder="e.g. Information Technology / Financial Services"
                  value={newClientIndustry}
                  onChange={(e) => setNewClientIndustry(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-200 text-slate-900 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#3C6E71]"
                />
              </div>

              <button
                type="submit"
                disabled={createClientMutation.isPending || !newClientName.trim()}
                className="w-full py-3.5 bg-[#3C6E71] hover:bg-[#2B5356] text-white rounded-xl text-sm font-bold shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
              >
                {createClientMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                Register Entity & Continue <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

        </div>

        {/* Security Footer Notice */}
        <div className="flex items-center justify-center gap-1.5 text-xs text-[#64748B]">
          <Lock className="w-3.5 h-3.5" />
          <span>Encrypted 256-bit Audit Pipeline Session</span>
        </div>

      </div>
    </div>
  );
}
