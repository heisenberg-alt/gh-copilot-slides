'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { PresentationBuilder } from '@/components/presentations/builder';
import { ProgressView } from '@/components/presentations/progress';

export default function NewPresentationPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [step, setStep] = useState<'input' | 'processing' | 'complete'>('input');
  const router = useRouter();

  const handleStart = (id: string) => {
    setSessionId(id);
    setStep('processing');
  };

  const handleComplete = () => {
    setStep('complete');
    if (sessionId) {
      router.push(`/presentations/${sessionId}`);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/" className="btn btn-ghost p-2">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">New Presentation</h1>
          <p className="text-text-secondary mt-1">
            {step === 'input' && 'Describe your topic to get started'}
            {step === 'processing' && 'Creating your presentation...'}
            {step === 'complete' && 'Your presentation is ready!'}
          </p>
        </div>
      </div>

      {/* Content */}
      {step === 'input' && <PresentationBuilder onStart={handleStart} />}
      {step === 'processing' && sessionId && (
        <ProgressView sessionId={sessionId} onComplete={handleComplete} />
      )}
    </div>
  );
}
