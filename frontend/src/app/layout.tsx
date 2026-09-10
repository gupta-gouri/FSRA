import type { Metadata } from 'next';
import './globals.css';
import ReactQueryProvider from '@/components/ReactQueryProvider';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'FSRA - Financial Statement Review & Risk Analytics System',
  description: 'Enterprise Financial Auditing, Verification & Forensic Suite',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#F8FAFC] text-[#334155] min-h-screen flex flex-col font-sans antialiased selection:bg-[#3C6E71]/20 selection:text-[#3C6E71]">
        <ReactQueryProvider>
          <Navbar />
          <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </main>
          <footer className="bg-white border-t border-[#E2E8F0] text-[#64748B] py-4 px-6 text-center text-xs">
            <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
              <span className="font-medium text-[#334155]">FSRA Systems • Enterprise Financial Statement Risk Analytics</span>
              <span>© {new Date().getFullYear()} FSRA. All rights reserved.</span>
            </div>
          </footer>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
