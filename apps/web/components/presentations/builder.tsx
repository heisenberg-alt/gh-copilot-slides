'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { UploadZone } from './upload-zone';
import { StylePicker } from './style-picker';
import { ExportOptions } from './export-options';
import { api } from '@/lib/api';

interface PresentationBuilderProps {
  onStart: (sessionId: string) => void;
}

export function PresentationBuilder({ onStart }: PresentationBuilderProps) {
  const [topic, setTopic] = useState('');
  const [urls, setUrls] = useState('');
  const [slideCount, setSlideCount] = useState(10);
  const [selectedStyle, setSelectedStyle] = useState('');
  const [exportFormats, setExportFormats] = useState<string[]>(['html']);
  const [templateUrl, setTemplateUrl] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [mood, setMood] = useState('');
  const [audience, setAudience] = useState('');

  const createMutation = useMutation({
    mutationFn: api.createPresentation,
    onSuccess: (data) => {
      onStart(data.session_id);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    createMutation.mutate({
      topic,
      urls: urls.split('\n').filter((u) => u.trim()),
      slide_count: slideCount,
      style_name: selectedStyle,
      output_formats: exportFormats,
      template_blob_url: templateUrl,
      mood,
      audience,
      purpose: 'presentation',
    });
  };

  const isValid = topic.trim().length > 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Topic Input - Main focus */}
      <div className="card">
        <label className="label">
          What should your presentation be about?
        </label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="textarea min-h-[120px]"
          placeholder="e.g., The future of renewable energy and its impact on global economies. Include statistics, market trends, and key players in the industry."
          autoFocus
        />
        <div className="flex justify-between items-center mt-2 text-sm text-text-secondary">
          <span>Be specific for better results</span>
          <span>{topic.length} / 2000</span>
        </div>
      </div>

      {/* Template Upload */}
      <div className="card">
        <label className="label">
          Upload a template (optional)
        </label>
        <p className="text-sm text-text-secondary mb-4">
          Upload a PowerPoint file to use as a design reference
        </p>
        <UploadZone onUpload={setTemplateUrl} uploadedUrl={templateUrl} />
      </div>

      {/* Style Selection */}
      <div className="card">
        <label className="label">
          Choose a style
        </label>
        <StylePicker
          selectedStyle={selectedStyle}
          onSelect={setSelectedStyle}
        />
      </div>

      {/* Export Formats */}
      <div className="card">
        <label className="label">
          Export formats
        </label>
        <ExportOptions
          selectedFormats={exportFormats}
          onChange={setExportFormats}
        />
      </div>

      {/* Advanced Options */}
      <div className="card">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full text-left"
        >
          <span className="font-medium">Advanced options</span>
          {showAdvanced ? (
            <ChevronUp className="w-5 h-5 text-text-secondary" />
          ) : (
            <ChevronDown className="w-5 h-5 text-text-secondary" />
          )}
        </button>

        {showAdvanced && (
          <div className="mt-6 space-y-6 pt-6 border-t border-border">
            {/* URLs */}
            <div>
              <label className="label">Reference URLs (one per line)</label>
              <textarea
                value={urls}
                onChange={(e) => setUrls(e.target.value)}
                className="textarea min-h-[80px]"
                placeholder="https://example.com/article-1&#10;https://example.com/article-2"
              />
            </div>

            {/* Slide count */}
            <div>
              <label className="label">Number of slides: {slideCount}</label>
              <input
                type="range"
                min="3"
                max="30"
                value={slideCount}
                onChange={(e) => setSlideCount(Number(e.target.value))}
                className="w-full h-2 bg-surface rounded-full appearance-none cursor-pointer accent-accent"
              />
              <div className="flex justify-between text-xs text-text-secondary mt-1">
                <span>3</span>
                <span>30</span>
              </div>
            </div>

            {/* Mood */}
            <div>
              <label className="label">Mood / Tone</label>
              <input
                type="text"
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                className="input"
                placeholder="e.g., professional, casual, inspirational"
              />
            </div>

            {/* Audience */}
            <div>
              <label className="label">Target Audience</label>
              <input
                type="text"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                className="input"
                placeholder="e.g., executives, students, general public"
              />
            </div>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!isValid || createMutation.isPending}
        className="btn btn-primary w-full py-4 text-lg"
      >
        {createMutation.isPending ? (
          <>
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Creating...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Generate Presentation
          </>
        )}
      </button>

      {createMutation.error && (
        <div className="p-4 rounded-apple bg-error/10 text-error text-sm">
          {(createMutation.error as Error).message || 'An error occurred'}
        </div>
      )}
    </form>
  );
}
