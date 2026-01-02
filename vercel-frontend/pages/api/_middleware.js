/**
 * /pages/api/_middleware.js (Optional)
 * Middleware for all API routes - adds common headers and logging
 */

export function middleware(request) {
  const response = new Response();
  
  // Add security headers
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  
  // Log API calls in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`[${new Date().toISOString()}] ${request.method} ${request.nextUrl.pathname}`);
  }
  
  return response;
}

export const config = {
  matcher: '/api/:path*',
};
