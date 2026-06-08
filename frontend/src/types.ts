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
