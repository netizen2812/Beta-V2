import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if the request is targeted for our API endpoints
  if (request.nextUrl.pathname.startsWith('/api/')) {
    // Clone request headers to append our secure client key
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set('x-app-client-key', 'faith_tech_client_key_2026');

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
