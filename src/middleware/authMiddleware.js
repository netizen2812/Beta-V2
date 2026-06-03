import { createClerkClient } from '@clerk/backend';

const clerkSecretKey = process.env.CLERK_SECRET_KEY;
const clerkPublishableKey = process.env.CLERK_PUBLISHABLE_KEY || process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

// Only instantiate clerkClient if secret key is present
const clerkClient = clerkSecretKey && clerkSecretKey !== "INSERT_CLERK_SECRET_KEY_HERE"
  ? createClerkClient({ 
      secretKey: clerkSecretKey,
      publishableKey: clerkPublishableKey
    })
  : null;

/**
 * Robust Clerk auth middleware.
 * Verifies Clerk session JWT in production and falls back to dummy user in development.
 */
export const requireAuth = async (req, res, next) => {
  // Check if we are in local development
  const isDev = process.env.NODE_ENV === "development";
  
  if (isDev) {
    // Development fallback
    req.auth = {
      userId: req.headers['x-user-id'] || 'test-user-123'
    };
    return next();
  }

  // Strict check in production: fail secure if clerkClient is unconfigured
  if (!clerkClient) {
    console.error("❌ Clerk SDK client is uninitialized in production. CLERK_SECRET_KEY is missing or invalid.");
    return res.status(500).json({
      status: "error",
      message: "Internal Server Error: Authentication service configuration failure."
    });
  }

  try {
    // Reconstruct the full absolute URL for the Clerk SDK.
    // Respect x-forwarded-proto and x-forwarded-host from Vercel edge proxy.
    const protocol = req.headers['x-forwarded-proto'] || 'https';
    let host = req.headers['x-forwarded-host'] || req.get('host') || 'imamv2.vercel.app';
    
    // In production, override IP/localhost hosts with the canonical domain to prevent Clerk SDK validation failures
    const isIpOrLocal = host.includes('127.0.0.1') || host.includes('localhost') || /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/.test(host);
    if (isIpOrLocal) {
      host = 'imamv2.vercel.app';
    }

    const fullUrl = `${protocol}://${host}${req.originalUrl || req.url}`;

    // Create a request-like object that Clerk authenticateRequest can parse correctly
    const clerkCompatibleReq = {
      headers: req.headers,
      method: req.method,
      url: fullUrl,
    };

    // authenticateRequest handles standard Clerk token validation from either:
    // 1. Authorization: Bearer <token>
    // 2. Cookie: __session=<token>
    const requestState = await clerkClient.authenticateRequest(clerkCompatibleReq);
    
    if (requestState.isSignedIn) {
      req.auth = {
        userId: requestState.toAuth().userId
      };
      return next();
    }
  } catch (err) {
    console.error("❌ Clerk authentication failed:", err.message);
  }

  // Reject unauthenticated requests in production
  return res.status(401).json({
    status: "error",
    message: "Unauthorized: Invalid or missing Clerk session token."
  });
};

