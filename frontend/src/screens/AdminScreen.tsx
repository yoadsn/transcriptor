import { useState, useEffect, useMemo } from 'react'
import { api } from '../api'
import type { AdminStatsDTO, AdminUserDTO, AdminCoverageDTO, AdminQueueDTO } from '../types'
import css from './AdminScreen.module.css'

const fmt = (n: number) => new Intl.NumberFormat('en-US').format(n)
const pct = (n: number) => `${n.toFixed(1)}%`
const dateStr = (iso: string | null) => iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'

type Tab = 'overview' | 'users' | 'coverage'
type SortDir = 'asc' | 'desc'

// ── Sub-components ────────────────────────────────────────────────────────────

function StatCard({ value, label, accent }: { value: string | number; label: string; accent?: string }) {
  return (
    <div className={css.statCard}>
      <div className={css.statValue} style={accent ? { color: accent } : undefined}>{value}</div>
      <div className={css.statLabel}>{label}</div>
    </div>
  )
}

function SortTh({
  col, label, sort, dir, onSort,
}: {
  col: string; label: string; sort: string; dir: SortDir; onSort: (c: string) => void
}) {
  const active = sort === col
  return (
    <th className={`${css.sortable}`} onClick={() => onSort(col)}>
      {label} {active ? (dir === 'desc' ? '↓' : '↑') : ''}
    </th>
  )
}

// ── Overview Tab ──────────────────────────────────────────────────────────────

function OverviewTab({ stats, queue }: { stats: AdminStatsDTO; queue: AdminQueueDTO }) {
  const total = queue.total_lines || 1
  const untouchedW = (queue.lines_untouched / total * 100).toFixed(1)
  const inProgressW = (queue.lines_in_progress / total * 100).toFixed(1)
  const completeW = (queue.lines_complete / total * 100).toFixed(1)

  return (
    <>
      <div>
        <div className={css.sectionTitle}>Annotation Progress</div>
        <div className={css.statRow}>
          <StatCard value={fmt(stats.total_users)} label="Total volunteers" />
          <StatCard value={fmt(stats.active_today)} label="Active today" />
          <StatCard value={fmt(stats.active_this_week)} label="Active this week" />
          <StatCard value={fmt(stats.text_transcriptions)} label="Text transcriptions" />
          <StatCard value={fmt(stats.total_transcriptions)} label="Total submissions" />
          <StatCard
            value={pct(stats.overall_completion_pct)}
            label="Lines complete"
            accent="oklch(0.58 0.1 150)"
          />
        </div>
      </div>

      <div>
        <div className={css.sectionTitle}>Queue Breakdown</div>
        <div className={css.queueBarWrap}>
          <div className={css.queueBar}>
            <div
              className={css.queueSegment}
              style={{ width: `${untouchedW}%`, background: 'var(--tl-muted-fill)' }}
            />
            <div
              className={css.queueSegment}
              style={{ width: `${inProgressW}%`, background: 'oklch(0.74 0.1 55)' }}
            />
            <div
              className={css.queueSegment}
              style={{ width: `${completeW}%`, background: 'oklch(0.58 0.1 150)' }}
            />
          </div>
          <div className={css.queueLegend}>
            <span>
              <span className={css.queueLegendDot} style={{ background: 'var(--tl-muted-fill)' }} />
              Untouched: {fmt(queue.lines_untouched)}
            </span>
            <span>
              <span className={css.queueLegendDot} style={{ background: 'oklch(0.74 0.1 55)' }} />
              In progress: {fmt(queue.lines_in_progress)}
            </span>
            <span>
              <span className={css.queueLegendDot} style={{ background: 'oklch(0.58 0.1 150)' }} />
              Complete: {fmt(queue.lines_complete)}
            </span>
          </div>
        </div>
      </div>

      <div className={css.statRow} style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
        <StatCard value={fmt(queue.total_lines)} label="Total lines" />
        <StatCard value={fmt(queue.pages_complete)} label="Pages fully complete" />
        <StatCard value={fmt(queue.batches_complete)} label="Manuscripts complete" />
      </div>
    </>
  )
}

// ── Users Tab ─────────────────────────────────────────────────────────────────

function UsersTab({ users }: { users: AdminUserDTO[] }) {
  const [sort, setSort] = useState('text_count')
  const [dir, setDir] = useState<SortDir>('desc')

  const sorted = useMemo(() => {
    const key = sort as keyof AdminUserDTO
    return [...users].sort((a, b) => {
      const av = a[key] ?? ''
      const bv = b[key] ?? ''
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return dir === 'desc' ? -cmp : cmp
    })
  }, [users, sort, dir])

  const onSort = (col: string) => {
    if (sort === col) setDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSort(col); setDir('desc') }
  }

  return (
    <div className={css.tableWrap}>
      <table className={css.table}>
        <thead>
          <tr>
            <SortTh col="display_name" label="Name" sort={sort} dir={dir} onSort={onSort} />
            <th>Email</th>
            <SortTh col="text_count" label="Text ↓" sort={sort} dir={dir} onSort={onSort} />
            <SortTh col="total_submissions" label="Total" sort={sort} dir={dir} onSort={onSort} />
            <SortTh col="cant_read_count" label="Can't read" sort={sort} dir={dir} onSort={onSort} />
            <SortTh col="flag_count" label="Flags" sort={sort} dir={dir} onSort={onSort} />
            <SortTh col="joined_at" label="Joined" sort={sort} dir={dir} onSort={onSort} />
            <SortTh col="last_active" label="Last active" sort={sort} dir={dir} onSort={onSort} />
          </tr>
        </thead>
        <tbody>
          {sorted.map(u => (
            <tr key={u.user_id}>
              <td style={{ fontWeight: 500 }}>{u.display_name}</td>
              <td className={css.muted}>{u.email}</td>
              <td style={{ fontWeight: 600, color: 'oklch(0.58 0.1 150)' }}>{fmt(u.text_count)}</td>
              <td>{fmt(u.total_submissions)}</td>
              <td className={css.muted}>{fmt(u.cant_read_count)}</td>
              <td className={css.muted}>{fmt(u.flag_count)}</td>
              <td className={css.muted}>{dateStr(u.joined_at)}</td>
              <td className={css.muted}>{dateStr(u.last_active)}</td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--tl-muted)', padding: 32 }}>No users yet</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

// ── Coverage & Queue Tab ──────────────────────────────────────────────────────

function CoverageTab({ coverage, queue }: { coverage: AdminCoverageDTO[]; queue: AdminQueueDTO }) {
  const total = queue.total_lines || 1
  const untouchedW = (queue.lines_untouched / total * 100).toFixed(1)
  const inProgressW = (queue.lines_in_progress / total * 100).toFixed(1)
  const completeW = (queue.lines_complete / total * 100).toFixed(1)

  return (
    <>
      <div>
        <div className={css.sectionTitle}>Queue Health</div>
        <div className={css.queueBarWrap}>
          <div className={css.queueBar}>
            <div className={css.queueSegment} style={{ width: `${untouchedW}%`, background: 'var(--tl-muted-fill)' }} />
            <div className={css.queueSegment} style={{ width: `${inProgressW}%`, background: 'oklch(0.74 0.1 55)' }} />
            <div className={css.queueSegment} style={{ width: `${completeW}%`, background: 'oklch(0.58 0.1 150)' }} />
          </div>
          <div className={css.queueLegend}>
            <span><span className={css.queueLegendDot} style={{ background: 'var(--tl-muted-fill)' }} />Untouched: {fmt(queue.lines_untouched)}</span>
            <span><span className={css.queueLegendDot} style={{ background: 'oklch(0.74 0.1 55)' }} />In progress: {fmt(queue.lines_in_progress)}</span>
            <span><span className={css.queueLegendDot} style={{ background: 'oklch(0.58 0.1 150)' }} />Complete: {fmt(queue.lines_complete)}</span>
            <span style={{ marginLeft: 'auto' }}>Pages done: {fmt(queue.pages_complete)} · Manuscripts done: {fmt(queue.batches_complete)}</span>
          </div>
        </div>
      </div>

      <div>
        <div className={css.sectionTitle}>Coverage by Manuscript</div>
        <div className={css.tableWrap}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>Manuscript ID</th>
                <th>Source</th>
                <th style={{ textAlign: 'right' }}>Pages</th>
                <th style={{ textAlign: 'right' }}>Lines</th>
                <th>Completion</th>
                <th style={{ textAlign: 'right' }}>Done</th>
              </tr>
            </thead>
            <tbody>
              {coverage.map(b => {
                const done = b.completion_pct >= 100
                return (
                  <tr key={b.batch_id}>
                    <td style={{ fontWeight: 500 }}>{b.external_id}</td>
                    <td className={css.muted}>{b.source}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{fmt(b.total_pages)}</td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{fmt(b.total_lines)}</td>
                    <td>
                      <span className={css.progressBar}>
                        <span
                          className={`${css.progressFill} ${done ? css.progressFillComplete : ''}`}
                          style={{ width: `${Math.min(100, b.completion_pct)}%` }}
                        />
                      </span>
                      {pct(b.completion_pct)}
                    </td>
                    <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                      {fmt(b.lines_complete)} / {fmt(b.total_lines)}
                    </td>
                  </tr>
                )
              })}
              {coverage.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--tl-muted)', padding: 32 }}>No manuscripts loaded</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}

// ── Main screen ───────────────────────────────────────────────────────────────

export function AdminScreen() {
  const [tab, setTab] = useState<Tab>('overview')
  const [stats, setStats] = useState<AdminStatsDTO | null>(null)
  const [users, setUsers] = useState<AdminUserDTO[]>([])
  const [coverage, setCoverage] = useState<AdminCoverageDTO[]>([])
  const [queue, setQueue] = useState<AdminQueueDTO | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.getAdminStats(),
      api.getAdminUsers(),
      api.getAdminCoverage(),
      api.getAdminQueue(),
    ]).then(([s, u, c, q]) => {
      if (s) setStats(s)
      if (u) setUsers(u)
      if (c) setCoverage(c)
      if (q) setQueue(q)
    }).finally(() => setLoading(false))
  }, [])

  const TABS: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'users', label: `Users${users.length ? ` (${users.length})` : ''}` },
    { id: 'coverage', label: 'Coverage & Queue' },
  ]

  return (
    <div className={css.root}>
      <div className={css.header}>
        <div className={css.title}>Admin Dashboard</div>
        <div className={css.tabs}>
          {TABS.map(t => (
            <button
              key={t.id}
              className={`${css.tab} ${tab === t.id ? css.tabActive : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className={css.body}>
        {loading && (
          <div style={{ color: 'var(--tl-muted)', fontSize: 14 }}>Loading…</div>
        )}
        {!loading && tab === 'overview' && stats && queue && (
          <OverviewTab stats={stats} queue={queue} />
        )}
        {!loading && tab === 'users' && (
          <UsersTab users={users} />
        )}
        {!loading && tab === 'coverage' && queue && (
          <CoverageTab coverage={coverage} queue={queue} />
        )}
      </div>
    </div>
  )
}
