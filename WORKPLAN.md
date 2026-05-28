# Hebrew Handwriting OCR Tagging Platform — V1 Backend Work Plan

USE UV FOR ENV MANAGEMENT
GIT for version control.
Follow clean conde concepts



A TDD, slice-by-slice build plan for the ivrit.ai handwritten-OCR crowdsourcing platform.
Written to be consumed by a coding agent (e.g. Claude Code): each slice is self-contained,
states its contract, lists the tests to write **first**, then the implementation that makes
them pass. Slices are in dependency order — never build on an untested slice.

---

## 0. Scope, stack, and ground rules

### What V1 is

A web platform where authenticated volunteers transcribe pre-segmented lines of Hebrew
handwriting, line-by-line, in the context of their source page. Each line is collected from
**3 distinct users**. All interpretation (consensus, flag reconciliation, quality weighting)
is deferred to an **offline post-processing step that is NOT part of this codebase**. This
plan covers the **backend core + the import and export scripts**. The frontend (transcription
UI) is a separate plan that consumes the API contract defined here.

### Stack

- Python 3.12+
- FastAPI (API), Pydantic v2 (schemas/validation)
- SQLAlchemy 2.0 (ORM, typed mapped-style), Alembic (migrations)
- PostgreSQL 15+
- pytest (+ pytest-asyncio), `httpx`/`TestClient` for endpoint tests
- Auth: Google OAuth (OIDC). For tests, auth is abstracted behind a dependency that is
  overridden — see Slice 7.
- Image storage: object storage in production; the code depends only on an `image_url`
  resolver function so filesystem-vs-object-storage is a one-function swap. Do NOT couple
  business logic to a storage backend.

### Non-negotiable design invariants (these are the spec — tests enforce them)

1. **`transcriptions` is append-truth.** One row per `(line, user)`. A user submitting again
   for the same line is an **edit** (upsert), never a new row.
2. **`transcription_count` on `lines` is a cached counter.** It increments only on the
   **first** response from a distinct user for that line. Edits never change it. It is always
   re-derivable from `transcriptions` (a test asserts this equality).
3. **A line stops being dispatched at `transcription_count >= 3`.** Over-collection is
   accepted (a 4th submit succeeds — accept-on-submit), so the count guard is a dispatch
   filter, not a write-time rejection.
4. **A line is never re-served to a user who already responded to it.** This is correctness,
   not optimization — the distinct-user guarantee depends on it.
5. **Flags are transcriptions too.** A transcription has a `kind`:
   `text | cant_read | bad_crop | not_hebrew | not_text`. Only `text` carries content.
   Flags count toward the 3. All flag interpretation is deferred to post-processing.
6. **Provenance flows down the hierarchy** batch → page → line → transcription and is never
   reconstructed. Source + license live on the **batch**.
7. **No consensus, no normalization, no anonymization in this codebase.** Those are
   post-processing concerns. The exporter is a faithful dump.

### Clean-code rules for the agent

- Keep pure logic (counting rules, dispatch eligibility, ID minting) in plain functions that
  take data and return data — no DB or framework imports inside them — so they're unit-testable
  without a database. The DB layer calls these functions.
- Endpoints are thin: parse → call a service function → serialize. No business logic in route
  handlers.
- Every slice: write the failing test(s) first, run them red, implement, run them green,
  refactor. Commit per slice.
- No premature abstraction. No repository pattern unless a test forces it. No caching beyond
  the one specified counter.

---

## Slice 1 — Project skeleton & test harness

**Goal:** a runnable, testable empty app. Nothing domain-specific yet.

**Tests first**
- `test_app_boots`: importing the FastAPI app object succeeds.
- `test_healthcheck`: `GET /health` returns 200 `{"status": "ok"}`.
- `test_db_fixture_connects`: a pytest fixture yields a working DB session against a
  **test database** (separate from dev), and a trivial `SELECT 1` succeeds.

**Implement**
- Project layout:
  ```
  app/
    main.py            # FastAPI app, health route
    db.py              # engine, session factory, Base
    config.py          # settings via pydantic-settings (DB URL, etc.)
    models/            # SQLAlchemy models (later slices)
    schemas/           # Pydantic models (later slices)
    services/          # pure + DB-touching business logic (later slices)
    api/               # routers (later slices)
  scripts/             # import / export (later slices)
  tests/
    conftest.py        # db fixture, app/client fixtures, transaction rollback per test
  alembic/             # migrations
  pyproject.toml
  ```
- `conftest.py`: a session-scoped engine on the test DB, and a **function-scoped session
  that wraps each test in a transaction and rolls back** (fast, isolated tests). Provide a
  `client` fixture with dependency overrides wired (auth override added in Slice 7).

**Done when:** all three tests green; `pytest` runs clean from a fresh checkout + test DB.

---

## Slice 2 — Schema & migrations (the six tables)

**Goal:** the full data model exists as SQLAlchemy models with an Alembic migration. No
business logic yet — just structure, constraints, and the indexes the hot paths need.

**Tables** (fields are the minimum; types in parens)

- `batches`: `id` (uuid pk), `external_id` (str, unique — for idempotent import),
  `source` (str), `license` (str), `created_at` (ts).
- `pages`: `id` (uuid pk), `batch_id` (fk), `external_id` (str), `image_path` (str),
  `width_px` (int), `height_px` (int), `created_at` (ts).
  Unique on `(batch_id, external_id)`.
- `lines`: `id` (uuid pk), `page_id` (fk), `line_index` (int — Surya reading order),
  `bbox` (jsonb: `{x,y,w,h}`), `polygon` (jsonb, nullable — stored for the future),
  `detection_confidence` (float, nullable), `transcription_count` (int, default 0),
  `external_id` (str). Unique on `(page_id, external_id)`.
  **Indexes:** `(page_id)`, and a composite supporting the dispatch query
  (`transcription_count` filtering within a page).
- `users`: `id` (uuid pk), `google_sub` (str, unique — OIDC subject), `email` (str),
  `display_name` (str), `show_on_leaderboard` (bool, default true), `created_at` (ts).
- `transcriptions`: `id` (uuid pk), `line_id` (fk), `user_id` (fk),
  `kind` (enum: `text|cant_read|bad_crop|not_hebrew|not_text`), `text` (str, nullable),
  `created_at` (ts), `updated_at` (ts).
  **Unique constraint on `(line_id, user_id)`** — this enforces append-truth at the DB level.
- `consents`: `id` (uuid pk), `user_id` (fk), `consent_type` (enum:
  `contribution_license|telemetry`), `version` (str), `shown_text_ref` (str),
  `created_at` (ts). Append-only (no updates).
- `events`: `id` (uuid pk), `user_id` (fk), `line_id` (fk, nullable),
  `event_type` (str: `served|submitted|edited|flagged|session_start` …),
  `payload` (jsonb, nullable), `created_at` (ts).

**Tests first**
- `test_models_create_all`: `Base.metadata.create_all` against the test DB succeeds.
- `test_transcription_unique_line_user`: inserting two transcriptions with the same
  `(line_id, user_id)` raises an integrity error.
- `test_page_unique_batch_external_id` and `test_line_unique_page_external_id`: same idea.
- `test_check_text_kind_has_text` *(optional but recommended)*: a CHECK or service-level rule
  that `kind=text` requires non-null `text` and flag kinds require null `text`. If enforced in
  DB, test it here; if enforced in the service layer, test it in Slice 5.
- `test_alembic_migration_roundtrips`: `alembic upgrade head` then `downgrade base` runs clean.

**Implement**
- SQLAlchemy 2.0 typed models (`Mapped[...]`, `mapped_column`).
- Enums as Python `enum.Enum` mapped to PG enums (or string + CHECK — pick one and be
  consistent; PG enum is cleaner).
- Generate the initial Alembic migration and verify it matches the models.

**Done when:** tests green; migration upgrades and downgrades cleanly.

---

## Slice 3 — Pure counting & eligibility logic (no DB)

**Goal:** the rules that are easiest to get wrong, isolated as pure functions and tested
exhaustively without a database. The DB layer (Slice 5/6) will call these.

**Functions** (in `app/services/rules.py`, all pure)

- `should_increment_count(is_first_response_from_user: bool) -> bool`
  Returns `is_first_response_from_user`. (Trivial, but it documents the invariant and gives
  the increment one named home.)
- `is_line_eligible_for_user(transcription_count: int, user_already_responded: bool,
  target: int = 3) -> bool`
  `True` iff `transcription_count < target` **and** `not user_already_responded`.
- `mint_line_external_id(batch_external_id, page_external_id, line_index) -> str`
  Deterministic, stable across import re-runs. (e.g. a normalized join or hash.)
- `order_session_lines(lines)` — returns lines sorted by `line_index`, with eligible lines
  marked and `done_by_you` lines carrying the user's prior response. (Keep the sort + mark
  logic pure; feed it plain dicts/dataclasses.)

**Tests first** — table-driven, covering:
- count < 3 & not responded → eligible; count == 3 → not eligible; responded → not eligible
  even if count < 3; boundary at exactly `target`.
- increment only on first response (true → true, false → false).
- ID minting is stable: same inputs → same id; different line_index → different id.
- ordering: lines returned in `line_index` order; eligibility marks correct given a mix.

**Done when:** 100% of these pure functions are covered and green. These tests are fast and
will catch regressions in the trickiest invariants.

---

## Slice 4 — User resolution & consent service

**Goal:** turn an authenticated identity into a `users` row, and gate contribution behind a
recorded license consent. Still no transcription logic.

**Service functions** (`app/services/users.py`, `app/services/consent.py`)

- `get_or_create_user(session, google_sub, email, display_name) -> User`
  Idempotent on `google_sub`.
- `record_consent(session, user, consent_type, version, shown_text_ref) -> Consent`
  Append-only insert.
- `has_active_contribution_consent(session, user, current_version) -> bool`
  True iff the user has a `contribution_license` consent at `current_version`.

**Tests first**
- `get_or_create_user` creates once, returns same row on second call (no duplicate).
- `record_consent` appends; two consents of same type different version both persist.
- `has_active_contribution_consent` false before consent, true after consent at current
  version, **false again** when `current_version` is bumped past the recorded one (this is the
  license-versioning re-consent guarantee — test it explicitly).

**Done when:** green. Note: the *content* of consent text and the notice-vs-opt-in call for
telemetry are product/legal decisions out of scope here; the code only records what it's told.

---

## Slice 5 — Submit a transcription (the write path)

**Goal:** the core write operation, enforcing every write-side invariant. This is the most
important slice — get the counter and upsert exactly right.

**Service function** (`app/services/transcriptions.py`)

- `submit_response(session, user, line_id, kind, text) -> SubmitResult`
  Steps:
  1. Validate kind/text pairing (`text` kind ⇒ text required & non-empty; flag kinds ⇒ text
     must be empty/null). Reject otherwise.
  2. Look up existing `(line_id, user_id)` transcription.
  3. **Upsert:** if none, insert and (via `should_increment_count(True)`) increment the line's
     `transcription_count`. If one exists, update its `kind`/`text`/`updated_at` and **do not**
     touch the counter (it's an edit).
  4. Write an `events` row (`submitted` or `edited`) with timestamps.
  5. Return the line's new `transcription_count` and the stored response.
  - Accept-on-submit: do **not** reject when count is already ≥ 3.

**Tests first**
- first submit inserts a row and bumps count 0→1.
- same user submits again (different text) → updates in place, count stays 1, `updated_at`
  changes, still exactly one row for that pair.
- three distinct users → count 1→2→3, three rows.
- fourth distinct user still succeeds (accept-on-submit), count → 4, four rows.
- `kind=text` with empty text → rejected. `kind=bad_crop` with text → rejected.
- **invariant test:** after a mix of inserts/edits, `line.transcription_count` equals
  `COUNT(*)` of transcriptions for that line. (Guards the cache against drift.)
- an `events` row is written per submit and per edit.

**Done when:** green. The unique constraint from Slice 2 is the backstop; the service is the
intended path.

---

## Slice 6 — Dispatch a session (the read path)

**Goal:** assemble a page-based session for a user: all lines of a chosen page, in reading
order, each marked eligible / full / done_by_you, preferring under-collected work.

**Service function** (`app/services/dispatch.py`)

- `get_next_session(session, user, target=3) -> SessionDTO | None`
  1. Choose a page that has at least one line eligible **for this user**
     (`transcription_count < target` AND user has no transcription for it). Prefer pages with
     the most eligible lines (or simplest: any such page) — document the choice.
  2. Load **all** lines of that page (not just eligible ones — context needs neighbors).
  3. For each line compute its status for this user: `eligible`, `full` (count ≥ target and
     user hasn't done it), or `done_by_you` (carry the user's prior text so the UI can show it
     editable).
  4. Order by `line_index`. Within dispatch preference, order eligible candidates by
     `transcription_count ASC` so over-collection stays rare.
  5. Return page image URL (via the storage resolver), page dimensions, and the line list with
     bbox + status. Returns `None` when nothing is left for this user.
  6. Optionally write a `session_start` / `served` event.

**Tests first** (seed pages/lines/transcriptions directly, then assert)
- a fresh page → all lines `eligible`, returned in `line_index` order.
- a line the user already did → that line is `done_by_you` with their text; others `eligible`.
- a line with count ≥ 3 (by others) → `full`, still present in the session for context.
- a page fully done by this user (every line done_by_you or full) is **not** chosen; dispatch
  moves to another page or returns `None`.
- two pages, one more under-collected → the more under-collected one is preferred (if you
  implement the preference; otherwise assert "a page with eligible lines is returned").
- the page image URL comes from the resolver (assert the resolver is called / value matches).

**Done when:** green. Keep the SQL filtering (`count < target`, `NOT EXISTS user transcription`)
in one well-named query; keep status-marking via the pure `order_session_lines` from Slice 3.

---

## Slice 7 — Auth dependency & wiring it for tests

**Goal:** a FastAPI dependency that yields the current `User` from a Google OIDC token in
production, and is trivially overridable in tests.

**Implement**
- `app/api/deps.py`: `get_current_user(...) -> User` — verifies the OIDC token, calls
  `get_or_create_user`. Factor token verification behind a small seam so tests don't need real
  Google tokens.
- A second dependency `require_contribution_consent` that 403s (or returns a sentinel the
  endpoint turns into a "needs consent" response) when `has_active_contribution_consent` is
  false. This is what gates the transcription endpoints.

**Tests first**
- with the override supplying a user, a protected dummy route returns 200.
- without auth, it returns 401.
- with a user lacking current consent, `require_contribution_consent` blocks (403 / needs-consent).

**Done when:** green. The `client` fixture from Slice 1 now overrides `get_current_user`.

---

## Slice 8 — The HTTP API (thin endpoints over the services)

**Goal:** expose the two core operations + consent + progress as HTTP, doing nothing but
parse → service → serialize.

**Endpoints**
- `GET  /api/next-session` → `get_next_session`. 200 with session DTO, or 204/empty when none.
  Gated by `require_contribution_consent`.
- `POST /api/lines/{line_id}/response` body `{kind, text?}` → `submit_response`. Gated by consent.
  Returns the new status of the line.
- `POST /api/consent` body `{consent_type, version}` → `record_consent`.
- `GET  /api/me/progress` → count of this user's `kind=text` transcriptions (flags excluded).
- `GET  /api/leaderboard` → top users by `kind=text` count, respecting `show_on_leaderboard`,
  refreshed on an interval (cache in memory or a short TTL — keep simple; a test asserts flags
  are excluded and hidden users are absent).

**Tests first** (endpoint/integration level, via the test client)
- happy path: consent → next-session → submit a line → progress reflects +1 (text only).
- submitting a flag does **not** increase progress count.
- next-session without consent → blocked.
- leaderboard excludes flag-only contributors and users with `show_on_leaderboard=false`.
- submit with bad kind/text pairing → 422/400.

**Done when:** green. Confirm route handlers contain no business logic (they call services).

---

## Slice 9 — Import script (Surya → DB)

**Goal:** a CLI that ingests Surya line-segmentation output for a batch of pages, idempotently.

**Contract**
- Input: a batch identifier + source + license (supplied by the operator), and Surya output
  per page (image reference + line list, each line carrying `bbox`, `polygon`, reading-order
  index, `confidence`).
- For each page: upsert the `pages` row (on `batch_id, external_id`), then for each detected
  line upsert a `lines` row keyed by a **minted stable external_id**
  (`mint_line_external_id`), storing `bbox`, `polygon`, `line_index` (reading order),
  `detection_confidence`. Provenance (source/license) is set on the batch.
- **Idempotent:** re-running the same import updates rows, never duplicates. Re-segmentation
  with a newer Surya run updates bbox/polygon/confidence for the same minted ids.

**Tests first**
- importing a small fixture (1 batch, 2 pages, N lines) creates the expected row counts.
- re-running the **same** import produces **no** new rows (counts unchanged) and updates fields.
- a line's `line_index` matches Surya reading order; `polygon` and `confidence` are persisted.
- minted `external_id` is stable across runs (Slice 3 already unit-tests the function; here
  assert end-to-end no duplication).

**Implement**
- `scripts/import_batch.py` reading a Surya-format fixture. Keep parsing of Surya's exact JSON
  shape in one adapter function so a Surya version change touches one place.

**Done when:** green, including the idempotency test (the most important one).

---

## Slice 10 — Export scripts (faithful dumps)

**Goal:** two dumb, faithful dumps. No consensus, no anonymization, no HuggingFace formatting
— all of that lives in the separate post-processing step.

**Contract**
- `scripts/export_dataset.py` → JSONL, one record per **line**, each carrying: provenance
  (batch source + license), Surya metadata (bbox, polygon, confidence, line_index, page image
  ref), and **all** its transcriptions (raw `text`, `kind`, real `user_id`, timestamps). Maximal
  fidelity — the consumer is your own post-processing.
- `scripts/export_telemetry.py` → dump of `events` (JSONL or CSV), internal only.

**Tests first**
- dataset export of a seeded line includes every transcription (text + flags), provenance,
  and Surya metadata; record count == line count.
- a line with mixed kinds (text + a flag) exports both, unmodified.
- telemetry export row count == events row count.
- (guard) dataset export and telemetry export are produced by **separate** code paths — assert
  the dataset record schema contains no event/behavioral fields.

**Done when:** green. Resist adding any interpretation here.

---

## Slice 11 — End-to-end smoke test

**Goal:** one test that walks the whole backend lifecycle to prove the slices compose.

**Test**
- import a fixture batch → a user consents → fetches a session → submits text for some lines,
  flags one, edits one → a second and third user each complete the page → assert the
  transcribed lines reach count 3 and drop out of new sessions → run the dataset export →
  assert the exported JSONL contains the lines with all three transcriptions and intact
  provenance.

**Done when:** green. This is the regression anchor for the whole backend.

---

## Phase boundary — frontend is a separate plan

The above delivers a tested backend + import/export. The transcription UI (React or htmx),
including the **neighbors-context view** (current line crop large + previous/next crops,
derived from the page image via bbox; same on desktop and mobile for V1, with full-page
desktop highlight deferred), RTL Hebrew input, the single flag button with reason options,
in-session edit, and the progress/leaderboard views, is built against the now-concrete API
contract (`/api/next-session`, `/api/lines/{id}/response`, `/api/consent`, `/api/me/progress`,
`/api/leaderboard`). Plan that as its own TDD slice set once this backend is green.

---

## Suggested commit / PR cadence for the agent

One PR per slice, each red→green→refactor, each leaving `pytest` fully green. Do not start a
slice until the prior slice's tests pass. If a slice reveals a needed schema change, amend the
Slice 2 migration story explicitly (new migration), never edit a shipped migration in place.
