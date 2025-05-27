'use client';

import Link from 'next/link';
import { useSession, signIn, signOut } from 'next-auth/react';
import { usePathname } from 'next/navigation';
import HackathonStatusBanner from './HackathonStatusBanner';

type UserWithRole = { role?: string };

export default function Navbar() {
  const { data: session, status } = useSession();
  const pathname = usePathname();
  if (!pathname) return null;
  const userRole = (session?.user as UserWithRole)?.role;

  const navLinks = [
    { href: '/hackathons', label: 'Hackathons', show: true },
    { href: '/mentors', label: 'Mentors', show: true },
    { href: '/sponsors', label: 'Sponsors', show: true },
    { href: '/faq', label: 'FAQ', show: true },
    { href: '/contact', label: 'Contact', show: true },
    {
      href: '/judging',
      label: 'Judging',
      show: userRole === 'judge' || userRole === 'admin',
    },
  ];

  return (
    <nav className="bg-slate-800 text-white p-4 shadow-md">
      <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-2">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="text-xl font-bold hover:text-slate-300 transition-colors"
          >
            HackathonPlatform
          </Link>
          {/* Hackathon-Status-Banner: Sichtbar, wenn User bei einem Hackathon registriert ist */}
          <div className="hidden md:block">
            {/* TODO: Dynamische Logik für aktiven Hackathon einbauen */}
            {/* Beispielhafte Anzeige für UI-Integration */}
            <HackathonStatusBanner
              hackathonName="Hackathon BLABLA"
              timeLeft="01:23:45"
              started={false}
            />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 md:gap-4">
          {navLinks
            .filter((l) => l.show)
            .map((link) => (
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
            <div className="relative group">
              <button
                className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium bg-slate-700 hover:bg-slate-600 transition-colors"
              >
                <span>
                  {session.user.name || session.user.email}
                  {/* Debug: Rolle anzeigen */}
                  <span className="ml-2 text-xs text-yellow-400">
                    [{String(userRole)}]
                  </span>
                </span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className="absolute right-0 mt-2 w-40 bg-white text-slate-800 rounded-md shadow-lg opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity z-50">
                <a
                  href="/profile"
                  className="block px-4 py-2 hover:bg-slate-100 rounded-t-md"
                >
                  Profile
                </a>
                {userRole === 'admin' && (
                  <a
                    href="/admin"
                    className="block px-4 py-2 hover:bg-slate-100"
                  >
                    Admin
                  </a>
                )}
                <button
                  onClick={() => signOut()}
                  className="block w-full text-left px-4 py-2 hover:bg-slate-100 text-red-600 rounded-b-md"
                >
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
