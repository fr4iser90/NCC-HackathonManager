import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { getToken } from 'next-auth/jwt'

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Get the session token
  // The secret MUST match the one used in [...nextauth].ts
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET })
  // console.log("[Middleware] JWT Token:", token); // For debugging 

  // Protect /admin routes
  if (pathname.startsWith('/admin')) {
    if (!token) {
      // User is not authenticated, redirect to sign-in page
      const signInUrl = new URL('/auth/signin', req.url)
      signInUrl.searchParams.set('callbackUrl', pathname) // Redirect back after login
      return NextResponse.redirect(signInUrl)
    }

    // Check if the user has the admin role
    // Ensure your JWT callback in [...nextauth].ts adds the role to the token
    if (token.role !== 'admin') {
      // User is authenticated but not an admin, redirect to an error page or home
      // For now, redirect to a generic "forbidden" page (you might want to create one)
      // Or redirect to home page with an error message (not implemented here)
      const forbiddenUrl = new URL('/auth/error?error=Forbidden', req.url) // Or a custom /403 page
      console.warn(`[Middleware] User with role '${token.role}' tried to access admin route: ${pathname}`);
      return NextResponse.redirect(forbiddenUrl)
    }
    // If authenticated and admin, allow access
    return NextResponse.next()
  }

  // Allow other routes to pass through
  return NextResponse.next()
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: [
    '/admin/:path*', // Protect all routes under /admin
    // Add other paths you want to protect, e.g.:
    // '/profile/:path*',
  ],
} 