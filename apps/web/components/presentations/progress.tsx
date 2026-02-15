'use client';

import { useEffect, useState } from 'react';
import { Check, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ProgressViewProps {
  sessionId: string;
  onComplete: () => void;
}

interface ProgressEvent {
  stage: string;
  message: string;
  progress: number;
}

const stages = [
  { id: 'initializing', label: 'Initializing' },
  { id: 'researching', label: 'Researching' },
  { id: 'curating', label: 'Curating Content' },
  { id: 'styling', label: 'Applying Style' },
  { id: 'exporting', label: 'Exporting' },
  { id: 'completed', label: 'Complete' },
];

export function ProgressView({ sessionId, onComplete }: ProgressViewProps) {
  const [currentStage, setCurrentStage] = useState('initializing');
  const [message, setMessage] = useState('Starting...');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const eventSource = new EventSource(
      `${apiUrl}/api/v1/presentations/${sessionId}/stream`,
      { withCredentials: true }
    );

    eventSource.addEventListener('progress', (event) => {
      const data: ProgressEvent = JSON.parse(event.data);
      setCurrentStage(data.stage);
      setMessage(data.message);
      setProgress(data.progress);

      if (data.stage === 'completed') {
        eventSource.close();
        setTimeout(onComplete, 1500);
      }

      if (data.stage === 'error') {
        setError(data.message);
        eventSource.close();
      }
    });

    eventSource.onerror = () => {
      // Try polling fallback
      eventSource.close();
      pollProgress();
    };

    const pollProgress = async () => {
      try {
        const response = await fetch(
          `${apiUrl}/api/v1/presentations/${sessionId}`
        );
        const data = await response.json();

        setCurrentStage(data.stage || 'processing');
        setProgress(data.progress || 50);

        if (data.status === 'completed') {
          onComplete();
        } else if (data.status === 'error') {
          setError(data.error);
        } else {
          setTimeout(pollProgress, 2000);
        }
      } catch {
        // Retry on error with backoff
        setTimeout(pollProgress, 3000);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId, onComplete]);

  const currentStageIndex = stages.findIndex((s) => s.id === currentStage);

  if (error) {
    return (
      <div className="card text-center py-12">
        <div className="w-16 h-16 rounded-full bg-error/10 flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-8 h-8 text-error" />
        </div>
        <h3 className="text-xl font-semibold mb-2">Something went wrong</h3>
        <p className="text-text-secondary max-w-md mx-auto">{error}</p>
      </div>
    );
  }

  return (
    <div className="card" role="status" aria-live="polite" aria-label="Presentation generation progress">
      {/* Progress ring */}
      <div className="flex justify-center mb-8">
        <div className="relative w-32 h-32" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
          <svg className="w-full h-full transform -rotate-90" aria-hidden="true">
            <circle
              cx="64"
              cy="64"
              r="56"
              fill="none"
              stroke="var(--surface)"
              strokeWidth="8"
            />
            <circle
              cx="64"
              cy="64"
              r="56"
              fill="none"
              stroke="var(--accent)"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray="352"
              strokeDashoffset={352 - (352 * progress) / 100}
              className="transition-all duration-500 ease-apple"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold">{progress}%</span>
          </div>
        </div>
      </div>

      {/* Current message */}
      <p className="text-center text-lg font-medium mb-8">{message}</p>

      {/* Stage indicators */}
      <div className="relative" role="list" aria-label="Generation stages">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" aria-hidden="true" />

        <div className="space-y-4">
          {stages.map((stage, index) => {
            const isComplete = index < currentStageIndex;
            const isCurrent = index === currentStageIndex;
            const isPending = index > currentStageIndex;

            return (
              <div
                key={stage.id}
                role="listitem"
                aria-current={isCurrent ? 'step' : undefined}
                className={cn(
                  'relative flex items-center gap-4 pl-10',
                  'transition-opacity duration-300',
                  isPending && 'opacity-40'
                )}
              >
                {/* Status indicator */}
                <div
                  className={cn(
                    'absolute left-2 w-5 h-5 rounded-full flex items-center justify-center',
                    'transition-all duration-300',
                    isComplete && 'bg-success',
                    isCurrent && 'bg-accent',
                    isPending && 'bg-surface border-2 border-border'
                  )}
                >
                  {isComplete && <Check className="w-3 h-3 text-white" />}
                  {isCurrent && (
                    <Loader2 className="w-3 h-3 text-white animate-spin" />
                  )}
                </div>

                <span
                  className={cn(
                    'font-medium',
                    (isComplete || isCurrent) && 'text-text-primary',
                    isPending && 'text-text-secondary'
                  )}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
