'use client';

import Link from 'next/link';
import { useSession, signIn, signOut } from 'next-auth/react';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const { data: session, status } = useSession();
  const pathname = usePathname();
  if (!pathname) return null;
  const userRole = (session?.user as any)?.role;

  const navLinks = [
    { href: '/hackathons', label: 'Hackathons', show: true },
    { href: '/profile', label: 'Profile', show: true },
    { href: '/teams', label: 'Teams', show: true },
    { href: '/projects', label: 'Projects', show: true },
    { href: '/mentors', label: 'Mentors', show: true },
    { href: '/sponsors', label: 'Sponsors', show: true },
    { href: '/faq', label: 'FAQ', show: true },
    { href: '/contact', label: 'Contact', show: true },
    { href: '/judging', label: 'Judging', show: userRole === 'judge' || userRole === 'admin' },
    { href: '/admin', label: 'Admin', show: userRole === 'admin' },
  ];

  return (
    <nav className="bg-slate-800 text-white p-4 shadow-md">
      <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-2">
        <Link href="/" className="text-xl font-bold hover:text-slate-300 transition-colors">
          HackathonPlatform
        </Link>
        <div className="flex flex-wrap items-center gap-2 md:gap-4">
          {navLinks.filter(l => l.show).map(link => (
            <Link
              key={link.href}
              href={link.href}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${pathname.startsWith(link.href) ? 'bg-slate-700 text-white' : 'hover:bg-slate-700 hover:text-white text-slate-300'}`}
            >
              {link.label}
            </Link>
          ))}
        </div>
        <div className="flex items-center space-x-4 mt-2 md:mt-0">
          {status === 'loading' && <p className="text-sm">Loading...</p>}
          {status === 'unauthenticated' && (
            <button
              onClick={() => signIn()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors text-sm font-medium"
            >
              Sign In
            </button>
          )}
          {status === 'authenticated' && session?.user && (
            <>
              <span className="text-sm hidden md:inline">Welcome, {session.user.name || session.user.email}</span>
              <button
                onClick={() => signOut()}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors text-sm font-medium"
              >
                Sign Out
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
} 