import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import type { SessionDTO, SessionLine, SubmitKind, FlagKind } from '../types'
import { WorkHeader } from '../components/WorkHeader'
import { LineStrip } from '../components/LineStrip'
import { TranscriptionInput } from '../components/TranscriptionInput'
import { ActionBar } from '../components/ActionBar'
import { FlagPopover } from '../components/FlagPopover'
import { Toast } from '../components/Toast'
import { WorkSkeleton } from '../components/Skeleton'
import styles from './WorkScreen.module.css'

interface FailedSubmit {
  lineId: string
  body: { kind: SubmitKind; text?: string }
  retries: number
}

export function WorkScreen() {
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionDTO | null>(null)
  const [loading, setLoading] = useState(true)
  const [cursorIdx, setCursorIdx] = useState(0)
  const [inputValue, setInputValue] = useState('')
  const [flagOpen, setFlagOpen] = useState(false)
  const [toastMsg, setToastMsg] = useState<string | null>(null)
  const [imageError, setImageError] = useState(false)
  const [todayCount, setTodayCount] = useState(0)
  const retryQueueRef = useRef<FailedSubmit[]>([])
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const submitLineRef = useRef<((lineId: string, body: { kind: SubmitKind; text?: string }, retriesLeft?: number) => Promise<void>) | null>(null)

  useEffect(() => {
    let cancelled = false
    api.nextSession().then((dto) => {
      if (cancelled) return
      if (!dto) {
        navigate('/done')
        return
      }
      setSession(dto)
      const firstEligible = dto.lines.findIndex(
        (l) => l.status === 'eligible' || l.status === 'done_by_you'
      )
      setCursorIdx(firstEligible >= 0 ? firstEligible : 0)
      setLoading(false)
      // Preload page image to detect failures
      const img = new Image()
      img.src = dto.image_url
      img.onerror = () => { if (!cancelled) setImageError(true) }
    }).catch(() => {
      if (!cancelled) setLoading(false)
    })
    return () => { cancelled = true }
  }, [navigate])

  function getActiveLine(lines: SessionLine[], idx: number): SessionLine | null {
    return lines[idx] ?? null
  }

  function processRetryQueue() {
    const queue = retryQueueRef.current.splice(0)
    queue.forEach(({ lineId, body, retries }) => {
      if (submitLineRef.current) {
        void submitLineRef.current(lineId, body, retries)
      }
    })
  }

  const submitLine = useCallback(
    async (lineId: string, body: { kind: SubmitKind; text?: string }, retriesLeft = 3) => {
      try {
        await api.submitResponse(lineId, body)
        setTodayCount((c) => c + 1)
      } catch {
        if (retriesLeft > 0) {
          const delay = Math.pow(2, 3 - retriesLeft) * 1000
          retryQueueRef.current.push({ lineId, body, retries: retriesLeft - 1 })
          if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
          retryTimerRef.current = setTimeout(() => processRetryQueue(), delay)
        } else {
          setToastMsg('שמירה נכשלה — מנסה שוב')
        }
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  )

  submitLineRef.current = submitLine

  function advance(line: SessionLine, kind: SubmitKind, text?: string) {
    if (!session) return
    const body: { kind: SubmitKind; text?: string } = { kind }
    if (text) body.text = text

    const nextIdx = cursorIdx + 1
    setInputValue('')
    setFlagOpen(false)

    if (nextIdx >= session.lines.length) {
      void submitLine(line.id, body)
      navigate('/done')
      return
    }

    setCursorIdx(nextIdx)
    const nextLine = session.lines[nextIdx]
    setInputValue(
      nextLine.status === 'done_by_you' ? (nextLine.your_text ?? '') : ''
    )
    void submitLine(line.id, body)
  }

  function handleSubmit(val: string) {
    if (!session) return
    const line = getActiveLine(session.lines, cursorIdx)
    if (!line) return
    advance(line, 'text', val)
  }

  function handleFlag(kind: FlagKind) {
    if (!session) return
    const line = getActiveLine(session.lines, cursorIdx)
    if (!line) return
    advance(line, kind)
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.content}>
          <WorkSkeleton />
        </div>
      </div>
    )
  }

  if (!session) return null

  const { lines, image_url, width_px, height_px, page_id } = session
  const pageDims = { width_px, height_px }
  const activeLine = getActiveLine(lines, cursorIdx)
  const prevLine = cursorIdx > 0 ? lines[cursorIdx - 1] : null
  const nextLine = cursorIdx < lines.length - 1 ? lines[cursorIdx + 1] : null
  const progress = lines.length > 0 ? (cursorIdx / lines.length) * 100 : 0

  return (
    <div className={styles.page}>
      <WorkHeader
        pageNum={parseInt(page_id, 10) || 1}
        lineNum={cursorIdx + 1}
        total={lines.length}
        todayCount={todayCount}
        progress={progress}
      />

      <div className={styles.content}>
        {imageError ? (
          <div className={styles.imageError}>
            <p className={styles.imageErrorText}>תמונת העמוד לא נטענה</p>
            <button className={styles.retryBtn} onClick={() => setImageError(false)}>
              נסה שוב
            </button>
          </div>
        ) : (
          <>
            {prevLine && (
              <div className={styles.contextStrip}>
                <LineStrip
                  line={prevLine}
                  pageDims={pageDims}
                  imageUrl={image_url}
                  role="previous"
                />
              </div>
            )}

            {activeLine && (
              <div className={styles.activeStrip}>
                <LineStrip
                  line={activeLine}
                  pageDims={pageDims}
                  imageUrl={image_url}
                  role="active"
                />
              </div>
            )}

            {nextLine && (
              <div className={styles.contextStrip}>
                <LineStrip
                  line={nextLine}
                  pageDims={pageDims}
                  imageUrl={image_url}
                  role="next"
                />
              </div>
            )}
          </>
        )}

        {activeLine && (
          <TranscriptionInput
            lineId={activeLine.id}
            value={inputValue}
            onChange={setInputValue}
            onSubmit={handleSubmit}
            onFKeyEmpty={() => setFlagOpen(true)}
          />
        )}

        <div className={styles.bottomPad} />
      </div>

      {activeLine && (
        <>
          <ActionBar
            onSubmit={() => handleSubmit(inputValue)}
            onFlagOpen={() => setFlagOpen(true)}
            canSubmit={inputValue.trim().length > 0}
          />

          <FlagPopover
            isOpen={flagOpen}
            onClose={() => setFlagOpen(false)}
            onSelect={handleFlag}
          />
        </>
      )}

      {toastMsg && (
        <Toast message={toastMsg} onDismiss={() => setToastMsg(null)} />
      )}
    </div>
  )
}
