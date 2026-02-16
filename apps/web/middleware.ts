import { withAuth } from 'next-auth/middleware';
import { NextResponse } from 'next/server';

export default withAuth(
  function middleware(req) {
    // If authenticated and visiting the root landing page, redirect to dashboard
    if (req.nextUrl.pathname === '/' && req.nextauth.token) {
      return NextResponse.redirect(new URL('/dashboard', req.url));
    }
    return NextResponse.next();
  },
  {
    callbacks: {
      // Return true to allow the request to proceed, false to redirect to signin
      authorized: ({ token, req }) => {
        const protectedPaths = ['/dashboard', '/new', '/presentations'];
        const isProtected = protectedPaths.some((path) =>
          req.nextUrl.pathname.startsWith(path)
        );
        // Allow all non-protected routes; require auth for protected ones
        if (!isProtected) return true;
        return !!token;
      },
    },
    pages: {
      signIn: '/signin',
    },
  }
);

export const config = {
  matcher: ['/', '/dashboard/:path*', '/new/:path*', '/presentations/:path*'],
};
