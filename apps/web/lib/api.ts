import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
  withCredentials: true,
});

// Add auth token to requests
apiClient.interceptors.request.use(async (config) => {
  // In production, get token from NextAuth session
  // For now, we'll let the cookies handle auth
  return config;
});

export interface CreatePresentationRequest {
  topic: string;
  urls?: string[];
  slide_count?: number;
  purpose?: string;
  mood?: string;
  audience?: string;
  style_name?: string;
  output_formats?: string[];
  template_blob_url?: string | null;
}

export interface PresentationStatus {
  session_id: string;
  status: 'processing' | 'completed' | 'error';
  stage?: string;
  progress?: number;
  title?: string;
  slide_count?: number;
  output_urls?: Record<string, string>;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface StylePreset {
  name: string;
  display_name: string;
  description: string;
  category: string;
  colors: Record<string, string>;
  fonts: Record<string, string>;
}

export interface UploadUrlRequest {
  filename: string;
  content_type?: string;
}

export interface UploadUrlResponse {
  upload_url: string;
  blob_url: string;
}

export const api = {
  // Presentations
  createPresentation: async (
    data: CreatePresentationRequest
  ): Promise<PresentationStatus> => {
    const response = await apiClient.post('/api/v1/presentations', data);
    return response.data;
  },

  getPresentation: async (sessionId: string): Promise<PresentationStatus> => {
    const response = await apiClient.get(`/api/v1/presentations/${sessionId}`);
    return response.data;
  },

  deletePresentation: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/presentations/${sessionId}`);
  },

  // Templates
  getUploadUrl: async (data: UploadUrlRequest): Promise<UploadUrlResponse> => {
    const response = await apiClient.post('/api/v1/templates/upload-url', data);
    return response.data;
  },

  // Styles
  getStyles: async (): Promise<{ styles: StylePreset[] }> => {
    const response = await apiClient.get('/api/v1/styles');
    return response.data;
  },

  getStyle: async (name: string): Promise<StylePreset> => {
    const response = await apiClient.get(`/api/v1/styles/${name}`);
    return response.data;
  },
};
