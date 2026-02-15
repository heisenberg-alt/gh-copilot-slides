'use client';

import { FileText, FileImage, Globe, Check } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ExportOptionsProps {
  selectedFormats: string[];
  onChange: (formats: string[]) => void;
}

const formats = [
  {
    id: 'html',
    label: 'HTML',
    description: 'Interactive web presentation',
    icon: Globe,
  },
  {
    id: 'pptx',
    label: 'PowerPoint',
    description: 'Editable .pptx file',
    icon: FileText,
  },
  {
    id: 'pdf',
    label: 'PDF',
    description: 'Print-ready document',
    icon: FileImage,
  },
];

export function ExportOptions({ selectedFormats, onChange }: ExportOptionsProps) {
  const toggleFormat = (formatId: string) => {
    if (selectedFormats.includes(formatId)) {
      // Don't allow deselecting all formats
      if (selectedFormats.length > 1) {
        onChange(selectedFormats.filter((f) => f !== formatId));
      }
    } else {
      onChange([...selectedFormats, formatId]);
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" role="group" aria-label="Export format selection">
      {formats.map((format) => {
        const isSelected = selectedFormats.includes(format.id);
        const Icon = format.icon;

        return (
          <button
            key={format.id}
            type="button"
            onClick={() => toggleFormat(format.id)}
            role="checkbox"
            aria-checked={isSelected}
            aria-label={`${format.label}: ${format.description}`}
            className={cn(
              'relative p-4 rounded-apple-lg border-2 text-left',
              'transition-all duration-200 ease-apple',
              isSelected
                ? 'border-accent bg-accent/5'
                : 'border-border hover:border-accent/50'
            )}
          >
            <div className="flex items-start gap-3">
              <div
                className={cn(
                  'w-10 h-10 rounded-apple flex items-center justify-center',
                  isSelected ? 'bg-accent' : 'bg-surface'
                )}
              >
                <Icon
                  className={cn(
                    'w-5 h-5',
                    isSelected ? 'text-white' : 'text-text-secondary'
                  )}
                />
              </div>
              <div className="flex-1">
                <p className="font-medium">{format.label}</p>
                <p className="text-sm text-text-secondary mt-0.5">
                  {format.description}
                </p>
              </div>
            </div>

            {/* Checkbox indicator */}
            <div
              className={cn(
                'absolute top-3 right-3 w-5 h-5 rounded-md border-2',
                'transition-all duration-200 ease-apple flex items-center justify-center',
                isSelected
                  ? 'bg-accent border-accent'
                  : 'border-border'
              )}
              aria-hidden="true"
            >
              {isSelected && <Check className="w-3 h-3 text-white" />}
            </div>
          </button>
        );
      })}
    </div>
  );
}
