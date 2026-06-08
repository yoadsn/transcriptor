export type LineStatus = 'eligible' | 'full' | 'done_by_you'

export interface BBox {
  x: number
  y: number
  w: number
  h: number
}

export interface SessionLine {
  id: string
  line_index: number
  bbox: BBox
  status: LineStatus
  transcription_count: number
  your_text?: string
}

export interface SessionDTO {
  page_id: string
  image_url: string
  width_px: number
  height_px: number
  lines: SessionLine[]
  page_label?: number
}

export type FlagKind = 'cant_read' | 'bad_crop' | 'not_hebrew' | 'not_text'
export type SubmitKind = 'text' | FlagKind

export interface LineStatusDTO {
  line_id: string
  status: LineStatus
  transcription_count: number
}

export interface PageDims {
  width_px: number
  height_px: number
}

// ── Admin DTOs ────────────────────────────────────────────────────────────────

export interface AdminStatsDTO {
  total_users: number
  active_today: number
  active_this_week: number
  total_transcriptions: number
  text_transcriptions: number
  overall_completion_pct: number
}

export interface AdminUserDTO {
  user_id: string
  display_name: string
  email: string
  joined_at: string | null
  last_active: string | null
  total_submissions: number
  text_count: number
  cant_read_count: number
  flag_count: number
}

export interface AdminCoverageDTO {
  batch_id: string
  external_id: string
  source: string
  total_pages: number
  total_lines: number
  lines_with_any: number
  lines_complete: number
  completion_pct: number
}

export interface AdminQueueDTO {
  total_lines: number
  lines_untouched: number
  lines_in_progress: number
  lines_complete: number
  pages_complete: number
  batches_complete: number
}
