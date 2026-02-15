'use client';

import Link from 'next/link';
import { Plus, FileText, Clock, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

// Note: This would fetch from API when the list endpoint is available
// For now, we show empty state as presentations are stored in-memory on backend
async function fetchPresentations() {
  // TODO: Implement when backend has GET /api/v1/presentations endpoint
  // const response = await fetch('/api/v1/presentations');
  // return response.json();
  return { presentations: [] };
}

interface Presentation {
  session_id: string;
  title: string;
  created_at: string;
  status: string;
  slide_count?: number;
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['presentations'],
    queryFn: fetchPresentations,
  });

  const presentations: Presentation[] = data?.presentations || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Your Presentations</h1>
          <p className="text-text-secondary mt-1">
            Create, manage, and export your AI-generated presentations
          </p>
        </div>
        <Link href="/new" className="btn btn-primary">
          <Plus className="w-4 h-4" aria-hidden="true" />
          New Presentation
        </Link>
      </div>

      {/* Presentations Grid */}
      {presentations.length > 0 ? (
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          role="list"
          aria-label="Presentations"
        >
          {presentations.map((presentation) => (
            <Link
              key={presentation.session_id}
              href={`/presentations/${presentation.session_id}`}
              className="card card-hover group"
              role="listitem"
            >
              {/* Thumbnail placeholder */}
              <div
                className="aspect-video bg-surface rounded-[12px] mb-4 flex items-center justify-center"
                aria-hidden="true"
              >
                <FileText className="w-12 h-12 text-text-secondary/40" />
              </div>

              <h3 className="font-semibold text-lg group-hover:text-accent transition-colors">
                {presentation.title || 'Untitled Presentation'}
              </h3>

              <div className="flex items-center gap-4 mt-2 text-sm text-text-secondary">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" aria-hidden="true" />
                  <time dateTime={presentation.created_at}>
                    {new Date(presentation.created_at).toLocaleDateString()}
                  </time>
                </span>
                {presentation.slide_count && (
                  <span>{presentation.slide_count} slides</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        /* Empty state */
        <div className="card text-center py-16">
          <div
            className="w-16 h-16 rounded-[20px] bg-surface mx-auto mb-6 flex items-center justify-center"
            aria-hidden="true"
          >
            <FileText className="w-8 h-8 text-text-secondary/40" />
          </div>
          <h3 className="text-xl font-semibold mb-2">No presentations yet</h3>
          <p className="text-text-secondary mb-6 max-w-md mx-auto">
            Create your first AI-powered presentation by describing your topic.
          </p>
          <Link href="/new" className="btn btn-primary">
            <Plus className="w-4 h-4" aria-hidden="true" />
            Create Presentation
          </Link>
        </div>
      )}
    </div>
  );
}
