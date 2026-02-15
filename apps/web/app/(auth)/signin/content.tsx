'use client';

import { signIn, useSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Sparkles, Loader2, AlertCircle } from 'lucide-react';

export default function SignInContent() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for error in URL params
  useEffect(() => {
    const errorParam = searchParams.get('error');
    if (errorParam) {
      setError(getErrorMessage(errorParam));
    }
  }, [searchParams]);

  useEffect(() => {
    if (session) {
      router.push('/');
    }
  }, [session, router]);

  const handleSignIn = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await signIn('azure-ad', { callbackUrl: '/' });
    } catch {
      setError('Failed to initiate sign in. Please try again.');
      setIsLoading(false);
    }
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-accent" aria-label="Loading" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-12">
          <div
            className="w-16 h-16 rounded-[20px] flex items-center justify-center mb-6"
            style={{
              backgroundColor: 'var(--accent)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08), 0 8px 32px rgba(0, 0, 0, 0.08)',
            }}
          >
            <Sparkles className="w-8 h-8 text-white" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold">Slide Builder</h1>
          <p className="text-text-secondary mt-2">Sign in to continue</p>
        </div>

        {/* Sign in card */}
        <div className="card">
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-2">Welcome</h2>
              <p className="text-text-secondary text-sm">
                Use your Microsoft account to sign in to Slide Builder.
              </p>
            </div>

            {/* Error message */}
            {error && (
              <div
                className="flex items-start gap-3 p-4 rounded-[12px] text-sm"
                style={{ backgroundColor: 'rgba(255, 59, 48, 0.1)', color: 'var(--error)' }}
                role="alert"
              >
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <p>{error}</p>
              </div>
            )}

            <button
              onClick={handleSignIn}
              disabled={isLoading}
              className="btn btn-primary w-full py-4 text-base"
              aria-busy={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                  Signing in...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" viewBox="0 0 21 21" fill="none" aria-hidden="true">
                    <rect width="10" height="10" fill="#F25022"/>
                    <rect x="11" width="10" height="10" fill="#7FBA00"/>
                    <rect y="11" width="10" height="10" fill="#00A4EF"/>
                    <rect x="11" y="11" width="10" height="10" fill="#FFB900"/>
                  </svg>
                  Sign in with Microsoft
                </>
              )}
            </button>

            <p className="text-xs text-text-secondary text-center">
              By signing in, you agree to our terms of service and privacy policy.
              Access is controlled by your organization administrator.
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-xs text-text-secondary text-center mt-8">
          Protected by Microsoft Entra ID
        </p>
      </div>
    </div>
  );
}

function getErrorMessage(error: string): string {
  switch (error) {
    case 'OAuthSignin':
    case 'OAuthCallback':
      return 'Authentication failed. Please check your Azure AD configuration.';
    case 'OAuthCreateAccount':
      return 'Could not create account. Contact your administrator.';
    case 'Callback':
      return 'Authentication callback error. Please try again.';
    case 'AccessDenied':
      return 'Access denied. You may not have permission to access this application.';
    case 'Configuration':
      return 'Server configuration error. Contact support.';
    default:
      return 'An authentication error occurred. Please try again.';
  }
}
