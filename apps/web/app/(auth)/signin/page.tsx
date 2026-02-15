import { Suspense } from 'react';
import { Loader2 } from 'lucide-react';
import SignInContent from './content';

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Loader2 className="w-8 h-8 animate-spin text-accent" aria-label="Loading" />
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <SignInContent />
    </Suspense>
  );
}
