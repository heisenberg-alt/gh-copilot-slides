'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, Loader2, Check } from 'lucide-react';
import { cn } from '@/lib/cn';
import { api } from '@/lib/api';

interface UploadZoneProps {
  onUpload: (blobUrl: string | null) => void;
  uploadedUrl: string | null;
}

export function UploadZone({ onUpload, uploadedUrl }: UploadZoneProps) {
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      // Validate file type
      if (!file.name.toLowerCase().endsWith('.pptx')) {
        setError('Only .pptx files are allowed');
        return;
      }

      // Validate file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        setError('File size must be less than 50MB');
        return;
      }

      setUploading(true);
      setError(null);

      try {
        // Get presigned upload URL
        const { upload_url, blob_url } = await api.getUploadUrl({
          filename: file.name,
          content_type: file.type,
        });

        // Upload directly to Azure Blob Storage
        await fetch(upload_url, {
          method: 'PUT',
          body: file,
          headers: {
            'x-ms-blob-type': 'BlockBlob',
            'Content-Type': file.type,
          },
        });

        setFileName(file.name);
        onUpload(blob_url);
      } catch {
        setError('Upload failed. Please try again.');
      } finally {
        setUploading(false);
      }
    },
    [onUpload]
  );

  const handleRemove = () => {
    setFileName(null);
    onUpload(null);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        ['.pptx'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  // Show uploaded state
  if (uploadedUrl && fileName) {
    return (
      <div className="flex items-center gap-4 p-4 rounded-apple bg-success/10 border border-success/20">
        <div className="w-10 h-10 rounded-apple bg-success/20 flex items-center justify-center">
          <Check className="w-5 h-5 text-success" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{fileName}</p>
          <p className="text-sm text-text-secondary">Template uploaded successfully</p>
        </div>
        <button
          type="button"
          onClick={handleRemove}
          className="btn btn-ghost p-2 text-text-secondary hover:text-error"
          aria-label="Remove uploaded file"
        >
          <X className="w-5 h-5" aria-hidden="true" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-apple-lg p-8 text-center cursor-pointer',
          'transition-all duration-200 ease-apple',
          isDragActive
            ? 'border-accent bg-accent/5'
            : 'border-border hover:border-accent/50 hover:bg-surface',
          uploading && 'pointer-events-none opacity-50'
        )}
      >
        <input {...getInputProps()} />

        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 text-accent animate-spin" />
            <p className="font-medium">Uploading...</p>
          </div>
        ) : isDragActive ? (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-10 h-10 text-accent animate-bounce" />
            <p className="font-medium text-accent">Drop your file here</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-apple-lg bg-surface flex items-center justify-center">
              <File className="w-7 h-7 text-text-secondary" />
            </div>
            <div>
              <p className="font-medium">
                Drag and drop a PowerPoint file
              </p>
              <p className="text-sm text-text-secondary mt-1">
                or click to browse (.pptx, max 50MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-2 text-sm text-error">{error}</p>
      )}
    </div>
  );
}
