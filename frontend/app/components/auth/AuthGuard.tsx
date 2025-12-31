import { useEffect, type ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { useAuthStore } from '../../hooks/useAuthStore';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: ReactNode;
  /** Redirect path when not authenticated (default: /login) */
  redirectTo?: string;
  /** If true, redirect authenticated users away (for login/register pages) */
  requireGuest?: boolean;
  /** Path to redirect guests to (used with requireGuest) */
  guestRedirectTo?: string;
}

/**
 * AuthGuard - Protects routes that require authentication
 *
 * Usage:
 * <AuthGuard>
 *   <ProtectedPage />
 * </AuthGuard>
 *
 * For guest-only pages (login/register):
 * <AuthGuard requireGuest guestRedirectTo="/generate">
 *   <LoginPage />
 * </AuthGuard>
 */
export function AuthGuard({
  children,
  redirectTo = '/login',
  requireGuest = false,
  guestRedirectTo = '/generate',
}: AuthGuardProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoggedIn, isHydrated } = useAuthStore();

  useEffect(() => {
    // Wait for store hydration before checking auth
    if (!isHydrated) return;

    if (requireGuest) {
      // For guest-only pages, redirect authenticated users
      if (isLoggedIn) {
        navigate(guestRedirectTo, { replace: true });
      }
    } else {
      // For protected pages, redirect unauthenticated users
      if (!isLoggedIn) {
        // Save the current location to redirect back after login
        navigate(redirectTo, {
          replace: true,
          state: { from: location.pathname },
        });
      }
    }
  }, [
    isLoggedIn,
    isHydrated,
    navigate,
    location,
    redirectTo,
    requireGuest,
    guestRedirectTo,
  ]);

  // Show loading while hydrating
  if (!isHydrated) {
    return (
      <div className='flex items-center justify-center min-h-[50vh]'>
        <Loader2 className='w-8 h-8 animate-spin text-blue-600' />
      </div>
    );
  }

  // For protected routes, don't render until authenticated
  if (!requireGuest && !isLoggedIn) {
    return null;
  }

  // For guest routes, don't render if authenticated
  if (requireGuest && isLoggedIn) {
    return null;
  }

  return <>{children}</>;
}

export default AuthGuard;
