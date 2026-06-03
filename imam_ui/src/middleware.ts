import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if the request is targeted for our API endpoints
  if (request.nextUrl.pathname.startsWith('/api/')) {
    // Clone request headers to append our secure client key
    const requestHeaders = new Headers(request.headers);
    // In production, require INTERNAL_API_KEY to be set in Vercel.
    // In development, allow a fallback to prevent blocking local developers.
    const signature = process.env.INTERNAL_API_KEY || (
      process.env.NODE_ENV === 'production' ? '' : 'faith_tech_client_key_2026'
    );

    if (signature) {
      requestHeaders.set('x-app-client-key', signature);
    }

    // Proceed with the request using the injected headers
    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });
  }
  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
};
