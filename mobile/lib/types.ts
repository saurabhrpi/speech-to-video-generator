export interface JobStatus {
  status: 'running' | 'completed' | 'failed';
  phase: string | null;
  step: number;
  total_steps: number;
  message: string;
  result: Record<string, any> | null;
  partial_result: Record<string, any> | null;
  error: string | null;
}

export interface PipelineState {
  scene_bible?: string;
  elements?: string[];
  renovated_elements?: string[];
  stages?: Record<string, any>[];
  seed?: number;
  keyframe_images?: string[];
  transition_videos?: string[];
  stitched_url?: string;
  video_url?: string;
}

export interface Clip {
  ts: number;
  url: string;
  note?: string;
  has_response?: boolean;
}

export interface TimelapsePayload {
  room_type: string;
  style: string;
  features: string[];
  materials: string[];
  lighting: string;
  camera_motion: string;
  progression: string;
  freeform_description: string;
  video_model: 'cheap' | 'expensive';
  stop_after?: string | null;
  resume_state?: Record<string, any> | null;
}

export interface TimelapseOptions {
  room_types: { value: string; label: string }[];
  styles: { value: string; label: string }[];
  lighting_options: { value: string; label: string }[];
  camera_options: { value: string; label: string }[];
  progression_types: { value: string; label: string }[];
  suggested_features: string[];
  suggested_materials: string[];
}

export interface CustomVideoPayload {
  image_urls: string[];
  model: 'cheap' | 'expensive';
  stop_after?: string | null;
  resume_state?: Record<string, any> | null;
}
