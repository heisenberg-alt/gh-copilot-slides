'use client';

import { useQuery } from '@tanstack/react-query';
import { Check, Loader2 } from 'lucide-react';
import { cn } from '@/lib/cn';
import { api } from '@/lib/api';

interface StylePickerProps {
  selectedStyle: string;
  onSelect: (style: string) => void;
}

export function StylePicker({ selectedStyle, onSelect }: StylePickerProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['styles'],
    queryFn: api.getStyles,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-accent" />
      </div>
    );
  }

  const styles = data?.styles || [];

  // Group styles by category
  const darkStyles = styles.filter((s) => s.category === 'dark');
  const lightStyles = styles.filter((s) => s.category === 'light');

  return (
    <div className="space-y-6" role="radiogroup" aria-label="Style selection">
      {/* Auto option */}
      <button
        type="button"
        onClick={() => onSelect('')}
        role="radio"
        aria-checked={!selectedStyle}
        className={cn(
          'w-full p-4 rounded-apple-lg border-2 text-left',
          'transition-all duration-200 ease-apple',
          !selectedStyle
            ? 'border-accent bg-accent/5'
            : 'border-border hover:border-accent/50'
        )}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Auto (Recommended)</p>
            <p className="text-sm text-text-secondary mt-1">
              AI will choose the best style based on your content
            </p>
          </div>
          {!selectedStyle && (
            <div className="w-6 h-6 rounded-full bg-accent flex items-center justify-center" aria-hidden="true">
              <Check className="w-4 h-4 text-white" />
            </div>
          )}
        </div>
      </button>

      {/* Dark styles */}
      {darkStyles.length > 0 && (
        <div>
          <p className="text-sm font-medium text-text-secondary mb-3">Dark Themes</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {darkStyles.map((style) => (
              <StyleCard
                key={style.name}
                style={style}
                isSelected={selectedStyle === style.name}
                onSelect={onSelect}
              />
            ))}
          </div>
        </div>
      )}

      {/* Light styles */}
      {lightStyles.length > 0 && (
        <div>
          <p className="text-sm font-medium text-text-secondary mb-3">Light Themes</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {lightStyles.map((style) => (
              <StyleCard
                key={style.name}
                style={style}
                isSelected={selectedStyle === style.name}
                onSelect={onSelect}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface StyleCardProps {
  style: {
    name: string;
    display_name: string;
    colors: {
      background?: string;
      text?: string;
      accent?: string;
    };
  };
  isSelected: boolean;
  onSelect: (name: string) => void;
}

function StyleCard({ style, isSelected, onSelect }: StyleCardProps) {
  const bgColor = style.colors.background || '#1c1c1e';
  const textColor = style.colors.text || '#ffffff';
  const accentColor = style.colors.accent || '#007aff';

  return (
    <button
      type="button"
      onClick={() => onSelect(style.name)}
      role="radio"
      aria-checked={isSelected}
      aria-label={style.display_name}
      className={cn(
        'relative p-3 rounded-apple-lg border-2 text-left',
        'transition-all duration-200 ease-apple',
        isSelected
          ? 'border-accent ring-2 ring-accent/20'
          : 'border-border hover:border-accent/50'
      )}
    >
      {/* Color preview */}
      <div
        className="aspect-video rounded-apple mb-2 flex items-center justify-center"
        style={{ backgroundColor: bgColor }}
      >
        <div className="space-y-1 w-3/4">
          <div
            className="h-2 rounded-full"
            style={{ backgroundColor: textColor, opacity: 0.9 }}
          />
          <div
            className="h-1.5 rounded-full w-2/3"
            style={{ backgroundColor: textColor, opacity: 0.5 }}
          />
          <div
            className="h-1.5 rounded-full w-1/2 mt-2"
            style={{ backgroundColor: accentColor }}
          />
        </div>
      </div>

      <p className="text-sm font-medium truncate">{style.display_name}</p>

      {/* Selected indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-accent flex items-center justify-center" aria-hidden="true">
          <Check className="w-3 h-3 text-white" />
        </div>
      )}
    </button>
  );
}
