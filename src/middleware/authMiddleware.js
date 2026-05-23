/**
 * Simple dummy auth middleware for local testing.
 * Bypasses Clerk requirements if clerkId is provided in headers or query.
 */
export const requireAuth = (req, res, next) => {
  // For local testing, we can inject a dummy user if not present
  req.auth = {
    userId: req.headers['x-user-id'] || 'test-user-123'
  };
  next();
};
