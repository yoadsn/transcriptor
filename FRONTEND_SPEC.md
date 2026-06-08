# Hebrew Handwriting OCR Tagging Platform — V1 Frontend Spec

Companion to `WORKPLAN.md` (backend). The backend API is built and green; this spec is the
frontend that consumes it. Written for a coding agent.

**Depth convention:** the **transcription loop** (§4) is specified to build-ready depth. The
surrounding screens (§5–§9) are specified to scaffold-ready depth — enough to build without
guessing, less exhaustive than the loop.

---

## 1. Stack & conventions

- **React 18 + Vite + TypeScript.** Keep dependencies minimal.
- **State:** React state + one `SessionContext`. No Redux/Zustand unless a need forces it.
- **Server state / fetching:** a thin `api.ts` wrapper over `fetch`. (TanStack Query is
  optional and fine, but not required — the data flows are simple.)
- **Styling:** your choice of CSS Modules or Tailwind; the spec gives tokens, not a framework.
- **Direction: the entire app is RTL.** Set `<html dir="rtl" lang="he">`. RTL is layout logic,
  not just text — see §3. All user-facing copy is **Hebrew**; this spec gives Hebrew strings
  with English glosses in (parentheses) for your reference. Do not ship the English.
- **Auth:** Google OAuth (OIDC). After login the app holds a session token sent on every API
  call. Unauthenticated → redirect to login (§5).

### API contract (from the built backend)

```
GET  /api/next-session         → SessionDTO | 204 (nothing left)        [needs consent]
POST /api/lines/{id}/response  body {kind, text?} → LineStatusDTO        [needs consent]
POST /api/consent              body {consent_type, version}             → 200
GET  /api/me/progress          → { text_count: number }
GET  /api/leaderboard          → [{ display_name, text_count }]
```

`SessionDTO` (shape to rely on):
```ts
type LineStatus = "eligible" | "full" | "done_by_you";
interface SessionLine {
  id: string;
  line_index: number;            // reading order (top→bottom on page)
  bbox: { x: number; y: number; w: number; h: number };  // px on the page image
  status: LineStatus;
  transcription_count: number;   // 0..N  (we DO show this — see §4.6)
  your_text?: string;            // present when status === "done_by_you"
}
interface SessionDTO {
  page_id: string;
  image_url: string;             // the full page image
  width_px: number;
  height_px: number;
  lines: SessionLine[];          // already ordered by line_index
}
```

`POST .../response` body: `{ kind: "text"|"cant_read"|"bad_crop"|"not_hebrew"|"not_text",
text?: string }`. `text` required & non-empty iff `kind === "text"`. Returns the line's new
status (`transcription_count`, etc.). **Accept-on-submit:** the backend never rejects for
"already full" — a 4th submit succeeds. The frontend must treat that as success, not error.

---

## 2. App shape & routes

```
/login            → Google sign-in (§5)
/consent          → license gate + telemetry notice (§5)   [blocks /work until satisfied]
/work             → the transcription loop (§4)  ← the product
/done             → between-pages / nothing-left states (§7)
/me               → progress + leaderboard (§6)
```

Route guard order on entering `/work`: authenticated? → has current consent? → else redirect
to `/login` or `/consent`. The consent version is a build-time constant compared against what
the backend reports; mismatch → re-consent (the backend already enforces this — the UI just
reacts to a 403/"needs consent" signal).

---

## 3. RTL & visual tokens (applies everywhere)

**RTL is layout, not translation.** Concretely:
- `dir="rtl"` on root; the main flow mirrors automatically, but verify each screen.
- Reading/advance direction is **right-to-left**: the "next" affordance and its arrow point
  **left** (`ti-arrow-left` = forward in Hebrew). "Previous" points right.
- Progress that fills as you advance fills **right→left**.
- Popovers/menus anchor from the right edge.
- The only LTR island is numeric/metric chrome in the header (counts, page numbers) — keep
  numerals LTR inside an RTL bar; don't flip digits.
- Line **images** are not mirrored — they're scans; only the UI chrome is RTL.

**Tokens** (map to your CSS system):
- Surfaces: page bg = secondary; cards/inputs = primary; muted fills = tertiary.
- Active line accent: a 2px info-colored ring (the one place 2px is allowed).
- Neighbor dimming: `opacity: 0.4`.
- Handwriting-adjacent text (the typed transcription) uses a **serif** face at large size for
  legibility against handwriting; UI chrome uses sans.
- Success = the progress/affirmation color; danger = errors only; flags are **neutral**, never
  red (flagging is normal, not an error — see §4.5).
- Radius md for inputs/controls, lg for cards. Borders 0.5px except the active-line 2px ring.

---

## 4. THE TRANSCRIPTION LOOP (`/work`) — build-ready

This is the product. A volunteer stares at it for an hour. Optimize for **calm focus first,
speed second, reward third** (priority order is intentional).

### 4.1 Data lifecycle of a session

1. On entering `/work`, `GET /api/next-session`.
   - `204` → go to `/done` (nothing left for this user; §7).
   - `SessionDTO` → load `image_url` **once**. All line strips are CSS-clipped views of this
     one image (see §4.3) — **no per-line image requests.** This is what makes advancing
     instant and gives neighbor-context for free.
2. The session is a **client-side cursor** over `lines` (already in `line_index` order). The
   cursor starts at the **first line whose status is `eligible`** (skip leading `full` lines
   for the active position, but still render them as context).
3. The volunteer acts on the active line (submit text / flag). On action:
   - **Optimistic advance (§4.4):** immediately move the cursor to the next line and render it;
     fire `POST .../response` in the background.
   - Update local `transcription_count` for the just-submitted line optimistically (+1 if this
     was the user's first response to it; unchanged if it was an edit of their own prior text).
4. When the cursor passes the last line, the page is done **for this volunteer** → go to
   `/done` (between-pages, §7), which fetches the next session.

### 4.2 Layout (desktop)

Top→bottom, mirroring reading order, minimizing eye travel between handwriting and input:

```
┌───────────────────────────────────────────────┐
│ HEADER: brand · "עמוד 14 · שורה 7 מתוך 23"      │  ← page/line orientation (LTR numerals)
│         progress: "142 היום" + page-fill bar    │  ← reward lives here, at the edge
├───────────────────────────────────────────────┤
│  [previous line]   dimmed 0.4, smaller          │  ← context (image strip)
│                                                 │
│  ┌─ current line ──────────────────────────┐   │  ← active image strip, large, 2px ring
│  │  (handwriting image, cropped via bbox)   │   │
│  └──────────────────────────────────────────┘   │
│     "תעתוק 2 מתוך 3"  (transcription 2 of 3)     │  ← per-line progress (see §4.6)
│                                                 │
│  ┌─ input ───────────────────────────────────┐  │  ← RTL textarea, serif, DIRECTLY below
│  │  הקלד את הטקסט כאן…                         │  │     the current image (least eye travel)
│  └──────────────────────────────────────────┘   │
│                                                 │
│  [⚑ לא קריא / דיווח]        [Enter] [שלח והמשך ←]│  ← flag (quiet, right) · submit (warm, left)
│                                                 │
│  [next line]       dimmed 0.4, smaller          │  ← context (image strip)
└───────────────────────────────────────────────┘
```

Component tree:
```
<WorkScreen>
  <WorkHeader progress pageInfo pageFill />
  <ContextStrip role="previous" line={prev} />     // hidden if no previous
  <ActiveLine line={current} count={..} />
  <TranscriptionInput value onChange onSubmit onFlag />
  <ActionBar onSubmit onFlag enterHint />
  <ContextStrip role="next" line={next} />          // hidden if no next
  <FlagPopover open reasons onPick onClose />        // §4.5
</WorkScreen>
```

### 4.3 Rendering a line image from bbox (the key technique)

Every line strip (previous, current, next) shows a **clipped region of the one page image**.
Given the page image at natural `width_px × height_px` and a line `bbox {x,y,w,h}`:

- Use a fixed-height strip container; scale so the bbox height fills it (active line taller
  than neighbors). Implementation: a wrapper `div` sized to the displayed strip, containing an
  `<img>` of the full page positioned with negative offset and scaled so only the bbox region
  is visible (object-fit/position or background-image with background-position + background-size
  computed from bbox and a chosen scale factor). The active line uses a larger scale than the
  dimmed neighbors.
- Add small horizontal padding around the bbox so glyphs at the crop edge aren't clipped.
- The image element is shared/cached by the browser (same `image_url`), so neighbor + active +
  next are three cheap clipped views, not three downloads.

Spec a small pure helper `cropStyle(bbox, pageDims, displayScale)` returning the CSS needed —
unit-test it on a few bbox/scale combos (the math is the kind of thing that's wrong by an
off-by-one until tested).

### 4.4 Optimistic advance & reconciliation (felt speed)

On submit (Enter or button) or flag pick:
1. Capture `{lineId, kind, text}`.
2. **Immediately** advance the cursor and clear the input, render next line. The volunteer is
   already reading the next line while the network call is in flight.
3. Fire `POST .../response` in the background.
   - **Success** (incl. accept-on-submit 4th response): reconcile the line's
     `transcription_count` from the response; no UI interruption.
   - **Failure** (network/500): do **not** yank the volunteer back. Show a quiet, non-blocking
     toast at the edge ("שמירה נכשלה — מנסה שוב", save failed, retrying) and retry with backoff.
     Queue failed submits so a transient drop doesn't lose work. Only if retries exhaust, mark
     that line for re-submission and surface a gentle persistent indicator — never a modal.
4. **Navigating away / closing mid-line:** an in-progress (typed but unsubmitted) line is the
   only thing at risk. Warn on unload only if the input has unsaved text. Submitted lines are
   already POSTed (or queued), so they survive.

Edits: if the active line's status is `done_by_you`, prefill the input with `your_text`; a
submit is an edit (backend upserts; count unchanged). Same optimistic pattern.

### 4.5 The flag control & popover

Flagging is **normal, not an error** — neutral styling, never red. Quiet by default so it
doesn't compete with submit and doesn't invite lazy flagging, but instantly reachable.

- Trigger: a low-weight button bottom-**right** (RTL leading edge), labeled
  "⚑ לא קריא / דיווח" (can't read / report).
- On click (or keyboard shortcut, e.g. `F`): open `FlagPopover` anchored to the trigger with
  the four reasons as a short list:
  - "תמונה חתוכה" (bad crop)
  - "לא עברית" (not Hebrew)
  - "לא טקסט" (not text)
  - "לא מצליח לקרוא" (can't read)
- Picking a reason = a submit with that `kind` and no `text` → optimistic advance (§4.4),
  same as a text submit. The popover closes and the loop continues.
- The four reasons map exactly to backend `kind` values; do not invent others.
- Escape / outside-click closes the popover without action.

### 4.6 Per-line transcription count (decision: SHOW, framed for motivation)

Show "תעתוק N מתוך 3" (transcription N of 3) on the active line as **forward progress**.
Rules that protect transcription independence (do not violate):
- Never reveal *what* anyone else typed. Only the count.
- Never visually de-emphasize a near-complete line or imply "someone else will handle it" — a
  line at 2/3 looks exactly as important to transcribe as one at 0/3.
- `full` lines (count ≥ 3, encountered as context because someone else completed them while
  this user worked the page) render as context only; the cursor skips them for the *active*
  position but they still appear dimmed in their reading-order place. If the volunteer chooses
  to type one anyway (it's still rendered), accept-on-submit applies.

### 4.7 Keyboard rhythm (desktop power users — most of your volume)

- Input is **always focused** on entering a line.
- `Enter` = submit & advance. `Shift+Enter` = newline within the textarea (rare, but Hebrew
  lines occasionally wrap — allow it).
- `F` (when input is empty or via a modifier) opens the flag popover; arrow keys + Enter pick a
  reason. Decide one non-conflicting trigger and document it in-app via the visible hint.
- Every keyboard action has a visible control (button, popover) so newcomers and touch users
  are never stranded. Keyboard is an accelerator, not the only path.

### 4.8 States the loop must handle

- **Loading session:** calm skeleton of the layout (strips as muted placeholders), not a
  spinner-on-blank.
- **First line / last line:** hide the missing neighbor strip (no empty box).
- **Submit in flight:** no blocking; the optimistic next line is already shown.
- **Submit failed (retrying / exhausted):** edge toast / gentle persistent marker (§4.4).
- **Image failed to load:** show a clear "תמונת העמוד לא נטענה" (page image failed) with a
  retry; without the page image nothing can be cropped, so this one *does* block the page.
- **Empty input + Enter:** do nothing (don't submit an empty text response; nudge focus). To
  skip a line the volunteer must flag it (can't read), not submit blank.

---

## 5. Onboarding & consent (scaffold-ready)

**`/login`:** centered card, brand, one "התחבר עם Google" (sign in with Google) button. On
success → consent check → `/work` or `/consent`.

**`/consent`:** the **mandatory license gate** + **telemetry notice** + **skippable primer
entry**. Layout: a single calm card.
- License section: plain-language summary of the contribution license + link to full text;
  one required checkbox/affirm + "אני מסכים/ה ותורם/ת" (I agree and contribute) →
  `POST /api/consent {consent_type:"contribution_license", version}`.
- Telemetry: a short **notice** (not a separate gate) — "אנו רושמים נתוני שימוש כדי לשפר את
  איכות הנתונים" (we record usage to improve data quality) — recorded via
  `POST /api/consent {consent_type:"telemetry", version}` when they proceed. (Built so it can
  flip to an explicit opt-in toggle later if legal requires — keep it its own call.)
- A "איך מתמללים" (how to transcribe) link opens the **skippable primer** (a short overlay:
  what the flag reasons mean + the few transcription conventions). Skippable; not a gate.
- Block `/work` until the contribution-license consent is recorded. The backend enforces this;
  the UI reacts to the needs-consent signal by routing here.

Re-consent: if the backend reports the recorded version is behind the current one, route to
`/consent` before the next session (same screen, framed as "התנאים עודכנו", terms updated).

---

## 6. Progress & leaderboard (`/me`, scaffold-ready)

Calm, edge-of-product — never interrupts the loop. Two pieces:
- **Personal:** `GET /api/me/progress` → a metric card "X שורות תומללו" (X lines transcribed).
  **Text responses only** (backend already excludes flags — don't recompute client-side).
- **Leaderboard:** `GET /api/leaderboard` → a simple ranked list of `display_name` + count,
  raw text-count ranking. Respect that the backend already excludes opted-out users; just
  render what's returned. A row for "you" highlighted if present.
- A privacy line: "השם שלך מופיע בלוח המובילים" (your name appears on the leaderboard) with a
  link to settings to opt out (`show_on_leaderboard` — a small toggle; if no settings screen in
  V1, link is a stub). Keep numerals LTR.

Reachable from the header (a quiet link/icon), not surfaced mid-loop.

---

## 7. Between-pages & nothing-left (`/done`, scaffold-ready)

This is the **one place reward may surface more fully** without breaking flow — the loop is
already paused.
- **Page complete (you finished every eligible line on the page):** a brief, calm affirmation —
  "סיימת את העמוד" (you finished the page) + the day's count ticking up + a primary "המשך
  לעמוד הבא" (continue to next page) that fetches the next session and returns to `/work`. Keep
  it quick; a dedicated volunteer wants to keep going, not admire a confetti screen. One small
  affirmation, then onward.
- **Nothing left (`204` from next-session):** "אין כרגע שורות לתעתוק — תודה!" (no lines to
  transcribe right now — thank you!) with a link to `/me`. This is success, not an error.

### Auto-advance vs. pause — DECISION NEEDED
Between pages, two options: (a) **auto-fetch the next session and drop straight back into
`/work`** with only a momentary affirmation toast (maximizes flow for power users), or
(b) **pause on the `/done` affirmation** and require a click to continue (a natural breath,
less likely to cause burnout, clearer sense of accomplishment). The priority ordering
(calm-focus first) slightly favors (b); raw volume favors (a). **Build (b) with the affirmation
auto-dismissing after a short delay into a ready "continue" state** unless you tell me
otherwise — it's the calm-first compromise. Flagged here because it changes the `/done` ↔
`/work` control flow.

---

## 8. Error & empty states (scaffold-ready, applies app-wide)

Principle: **the loop never hard-blocks except when it truly cannot proceed.** Map:
- Session fetch network error → calm retry card on `/work` ("טעינת השורות נכשלה", failed to load
  lines) + retry button. Not the loop skeleton (that implies progress).
- `204` no session → `/done` nothing-left (not an error).
- Submit failure → §4.4 (non-blocking, retry, never a modal).
- Page image load failure → §4.8 (blocks the page, offers retry).
- Auth expired mid-session → quiet re-auth; preserve any unsubmitted input across it if
  feasible, else warn before redirect.
- Needs-consent signal anywhere → route to `/consent`.
- Generic 500 on non-critical calls (progress, leaderboard) → fail quietly, show the rest.

---

## 9. Mobile (scaffold-ready; full depth deferred)

V1 mobile is the **same neighbors-context loop**, adapted to vertical-space pressure (we
deferred the desktop full-page-highlight enhancement entirely). Adaptations:
- Same top→bottom order; the active line dominates more, neighbor strips thinner (or just the
  immediate previous/next, even shorter). Context stays *visible*, not hover-gated (no hover on
  touch).
- **Tap-first by nature:** the "שלח והמשך" (submit & next) button is primary and thumb-reachable;
  there's no Enter-to-advance flow to rely on. Keep the button **above** the device keyboard —
  test that it isn't occluded when the keyboard is open (a classic failure). The flag control
  must also stay reachable with the keyboard open.
- RTL Hebrew input relies on the device keyboard; mark the field `dir="rtl" lang="he"` so
  prediction/autocorrect behave. Do **not** build a custom on-screen Hebrew keyboard for V1.
- Everything else (optimistic advance, flag popover as a bottom sheet, states) carries over.

Build the loop responsively from one component set; diverge only the context-strip sizing and
the action bar placement by viewport. Defer pixel-level mobile polish to a later pass.

---

## 10. Build order for the agent (suggested)

1. App shell, routing, RTL root, `api.ts`, auth guard, token handling.
2. `cropStyle(bbox, pageDims, scale)` pure helper **+ its unit tests** (the math is the risky
   bit — TDD it first, like the backend's pure functions).
3. The transcription loop (§4): static layout with a mocked `SessionDTO`, then wire
   `next-session`, then optimistic submit/advance, then the flag popover, then states.
4. Consent gate + login (§5) — gate `/work`.
5. `/done` between-pages + nothing-left (§7).
6. Progress + leaderboard (§6).
7. Error/empty states pass (§8) across all screens.
8. Mobile adaptation pass (§9).

Each step leaves the app runnable. Mock the API behind `api.ts` so the loop can be built and
demoed before every endpoint is wired.

---

## Open decision carried into build
- §7 auto-advance vs. pause between pages — building (b) calm-pause-with-auto-ready unless
  told otherwise.

(Everything else in this spec is decided. Out of frontend scope, per earlier design: consent
*copy* and the telemetry notice-vs-opt-in legal call → project counsel; transcription
*conventions* in the primer → project linguists.)
