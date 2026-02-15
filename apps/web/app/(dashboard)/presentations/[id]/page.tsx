'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Download, FileText, Globe, FileImage, Loader2, Trash2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api, PresentationStatus } from '@/lib/api';
import { cn } from '@/lib/cn';

export default function PresentationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const { data: presentation, isLoading, error } = useQuery({
    queryKey: ['presentation', sessionId],
    queryFn: () => api.getPresentation(sessionId),
    refetchInterval: (query) => {
      const data = query.state.data;
      // Keep polling if still processing
      return data?.status === 'processing' ? 2000 : false;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (error || !presentation) {
    return (
      <div className="card text-center py-12">
        <h2 className="text-xl font-semibold mb-2">Presentation not found</h2>
        <p className="text-text-secondary mb-6">
          The presentation you&apos;re looking for doesn&apos;t exist or has been deleted.
        </p>
        <Link href="/" className="btn btn-primary">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const formatIcons: Record<string, React.ElementType> = {
    html: Globe,
    pptx: FileText,
    pdf: FileImage,
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link href="/" className="btn btn-ghost p-2">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">
              {presentation.title || 'Untitled Presentation'}
            </h1>
            <p className="text-text-secondary mt-1">
              {presentation.slide_count
                ? `${presentation.slide_count} slides`
                : 'Processing...'}
              {' • '}
              Created {new Date(presentation.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Status badge */}
        <div
          className={cn(
            'px-3 py-1 rounded-full text-sm font-medium',
            presentation.status === 'completed' && 'bg-success/10 text-success',
            presentation.status === 'processing' && 'bg-accent/10 text-accent',
            presentation.status === 'error' && 'bg-error/10 text-error'
          )}
        >
          {presentation.status === 'processing' && (
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing
            </span>
          )}
          {presentation.status === 'completed' && 'Completed'}
          {presentation.status === 'error' && 'Error'}
        </div>
      </div>

      {/* Processing state */}
      {presentation.status === 'processing' && (
        <div className="card text-center py-12">
          <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
          </div>
          <h3 className="text-xl font-semibold mb-2">Creating your presentation</h3>
          <p className="text-text-secondary">
            {presentation.stage || 'Processing...'}
          </p>
          {presentation.progress !== undefined && (
            <div className="mt-4 max-w-xs mx-auto">
              <div className="h-2 bg-surface rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all duration-300"
                  style={{ width: `${presentation.progress}%` }}
                />
              </div>
              <p className="text-sm text-text-secondary mt-2">
                {presentation.progress}% complete
              </p>
            </div>
          )}
        </div>
      )}

      {/* Error state */}
      {presentation.status === 'error' && (
        <div className="card bg-error/5 border border-error/20">
          <h3 className="text-lg font-semibold text-error mb-2">Error</h3>
          <p className="text-text-secondary">
            {presentation.error || 'An unknown error occurred'}
          </p>
        </div>
      )}

      {/* Completed state - Downloads */}
      {presentation.status === 'completed' && presentation.output_urls && (
        <>
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Download</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {Object.entries(presentation.output_urls).map(([format, url]) => {
                const Icon = formatIcons[format] || FileText;
                return (
                  <a
                    key={format}
                    href={url}
                    download
                    className="flex items-center gap-3 p-4 rounded-apple-lg bg-surface hover:bg-surface-elevated border border-border hover:border-accent/50 transition-all duration-200"
                  >
                    <div className="w-10 h-10 rounded-apple bg-accent/10 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="font-medium">{format.toUpperCase()}</p>
                      <p className="text-sm text-text-secondary">
                        {format === 'html' && 'Interactive web'}
                        {format === 'pptx' && 'PowerPoint file'}
                        {format === 'pdf' && 'PDF document'}
                      </p>
                    </div>
                    <Download className="w-5 h-5 ml-auto text-text-secondary" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Preview iframe for HTML */}
          {presentation.output_urls.html && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Preview</h2>
              <div className="aspect-video rounded-apple overflow-hidden border border-border">
                <iframe
                  src={presentation.output_urls.html}
                  className="w-full h-full"
                  title="Presentation Preview"
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
