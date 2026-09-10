'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ShieldCheck, LogOut, Building2, ChevronRight, FolderKanban } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [currentClientName, setCurrentClientName] = useState<string | null>(null);

  useEffect(() => {
    const clientName = localStorage.getItem('fsra_active_client_name');
    setCurrentClientName(clientName);
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem('fsra_active_client_id');
    localStorage.removeItem('fsra_active_client_name');
    router.push('/login');
  };

  if (pathname === '/login') return null;

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-50 shadow-xs select-none">
      <div className="max-w-[1600px] mx-auto flex items-center justify-between gap-4">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-4">
          <Link href="/projects" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-[#3C6E71] text-white flex items-center justify-center shadow-sm group-hover:bg-[#2B5356] transition-colors">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-xl text-slate-900 tracking-tight">FSRA</span>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-md bg-[#3C6E71]/10 text-[#3C6E71] border border-[#3C6E71]/20 uppercase tracking-wider">
                  Audit Suite
                </span>
              </div>
              <span className="text-xs text-slate-600 block font-medium">Financial Statement & Risk Analytics</span>
            </div>
          </Link>

          {/* Path / Active Context */}
          <div className="hidden md:flex items-center gap-2 text-sm text-slate-600 border-l border-slate-200 pl-4 py-1">
            <FolderKanban className="w-4 h-4 text-[#3C6E71]" />
            <Link href="/projects" className="hover:text-[#3C6E71] font-semibold transition-colors">
              Engagements
            </Link>
          </div>
        </div>

        {/* Right Actions: Active Client & Logout */}
        <div className="flex items-center gap-3">
          {currentClientName && (
            <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-800 font-semibold shadow-xs">
              <Building2 className="w-4 h-4 text-[#3C6E71]" />
              <span>{currentClientName}</span>
            </div>
          )}

          <button
            onClick={handleLogout}
            className="px-3 py-2 text-slate-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition-colors flex items-center gap-1.5 text-sm font-semibold border border-transparent hover:border-rose-200"
            title="Log out / Switch client"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>

      </div>
    </header>
  );
}
