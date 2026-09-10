'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const activeClient = localStorage.getItem('fsra_active_client_id');
    if (!activeClient) {
      router.push('/login');
    } else {
      router.push('/projects');
    }
  }, [router]);

  return null;
}
