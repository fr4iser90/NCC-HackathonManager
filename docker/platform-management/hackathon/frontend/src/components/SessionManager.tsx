'use client';

import { useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { usePathname, useRouter } from 'next/navigation';

export default function SessionManager() {
  const { status, data: session } = useSession();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    // console.log(`[SessionManager] Path: ${pathname}, Status: ${status}, Role: ${(session?.user as any)?.role}`);

    if (status === 'loading') {
      return; // Don't do anything while session is loading
    }

    const authRelatedPaths = ['/auth/signin', '/auth/register', '/auth/error', '/auth/signup'];
    const isAdminPath = pathname.startsWith('/admin');
    // Determine if the current path is public. Add any other top-level public paths here.
    const isPublicPath = (pathname === '/'); 

    if (status === 'unauthenticated') {
      // If user is unauthenticated, and NOT on an auth-related page, AND NOT on a designated public path,
      // then redirect them to sign-in.
      if (!authRelatedPaths.some(p => pathname.startsWith(p)) && !isPublicPath) {
        console.log(`[SessionManager] Unauthenticated on protected path ${pathname}. Redirecting to signin.`);
        // Consider if signOut is needed here. If session is truly unauthenticated, 
        // client state should reflect that. Forcing signOut might be redundant or cover edge cases.
        // signOut({ redirect: false }); // Optional: ensure client state is fully cleared
        router.push('/auth/signin?sessionExpired=true&reason=unauthenticated_on_protected_path');
      }
    } else if (status === 'authenticated') {
      // User is authenticated
      const userRole = (session?.user as any)?.role;

      // If on an admin path but not an admin role
      if (isAdminPath && userRole !== 'admin') {
        console.log(`[SessionManager] Authenticated user (Role: ${userRole}) on admin path ${pathname} without admin rights. Signing out.`);
        signOut({ redirect: false }).then(() => {
          router.push('/auth/signin?sessionExpired=true&reason=admin_path_non_admin_role');
        });
        return; // Exit early after initiating sign-out and redirect
      }

      // If an authenticated user is trying to access an auth page (e.g., signin, register)
      if (authRelatedPaths.some(p => pathname.startsWith(p))) {
        console.log(`[SessionManager] Authenticated user on auth page ${pathname}. Redirecting.`);
        // Redirect to a default page based on role, or a general dashboard
        router.push(userRole === 'admin' ? '/admin' : '/'); // Example: admin to /admin, others to homepage
      }
    }

    // Backend-Session-Check: Prüfe regelmäßig, ob das Token noch gültig ist
    let interval: NodeJS.Timeout | undefined;
    if (status === 'authenticated') {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
      // Ping-URL: /ping am Backend, Fallback /api/ping für Dev
      const pingUrl = apiBaseUrl
        ? apiBaseUrl.replace(/\/$/, '') + '/ping'
        : '/api/ping';
      const accessToken = (session?.user as any)?.accessToken;
      const checkSession = async () => {
        try {
          const res = await fetch(pingUrl, {
            headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
            credentials: 'include',
          });
          if (!res.ok) {
            if (res.status === 401 || res.status === 403) {
              console.warn('[SessionManager] Session invalid (backend 401/403). Signing out.');
              signOut({ callbackUrl: '/auth/signin?sessionExpired=true&reason=backend_invalid' });
            }
          }
        } catch (err) {
          // Netzwerkfehler o.ä. => optional auch signOut
          console.error('[SessionManager] Error during backend session check:', err);
        }
      };
      checkSession(); // Direkt beim Mount prüfen
      interval = setInterval(checkSession, 60 * 1000); // Alle 60 Sekunden prüfen
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [status, session, pathname, router]);

  return null; // This component does not render anything itself
} 