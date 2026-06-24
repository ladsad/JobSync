# Job search automation tool — project plan

Personal tool for an India-based fresh graduate job search (SWE + Data/ML lanes), built around: phone-triggered actions, laptop does the heavy lifting, decoupled queue so nothing depends on the laptop being online at the same time as the phone.

## 1. Goals and non-goals

**Goals**

* Pull fresh job postings daily from sources that allow it (no scraping ToS-protected sites)
* Score each posting against resume fit (SWE vs Data/ML variant), surface a daily shortlist
* Speed up the alumni/near-peer outreach workflow: draft personalized messages, track who's been contacted and follow-up status
* Track every application end-to-end (applied → contacted → interview → offer/reject)
* Usable from phone (read shortlist, trigger fetch/draft jobs, update tracker) while actual scraping/API/LLM work runs on the laptop

**Non-goals (deliberately out of scope)**

* No scraping or automating LinkedIn, Naukri, or Internshala — ToS risk to your account during an active job search is not worth it
* No fully autonomous "auto-submit application" agent — review-before-send stays manual, at least for v1
* No 24/7 uptime requirement — laptop-offline periods are expected and fine

## 2. Architecture

 **Pattern: decoupled task queue** , not direct phone→laptop calls.

```
Phone (hosted page) → Hosted DB (queue + data) ← Laptop worker (polls/executes) → External APIs
```

* Phone page never talks to the laptop directly. It reads/writes rows in a hosted database.
* Laptop worker polls (or subscribes via realtime) for pending tasks, executes them using local network access, writes results back into the same database.
* This means the laptop can be asleep/offline for hours — tasks just wait. No public port exposed on the laptop. No tunnel-uptime dependency.

**Stack**

| Piece           | Choice                                                                   | Why                                                                          |
| --------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| Hosted DB + API | Supabase (Postgres, free tier)                                           | Auto REST API + realtime + auth, no custom backend needed                    |
| Hosted frontend | Static page on Vercel/Netlify                                            | Talks to Supabase directly from the browser, free tier                       |
| Laptop worker   | Python script (`supabase-py`client)                                    | You're a dev, full control, reuses your existing Gemini/antigravity pipeline |
| LLM             | Gemini (already set up with ATS skills)                                  | Reuse existing resume-tailoring pipeline                                     |
| Job sources     | Greenhouse + Lever public job-board APIs, Adzuna API, Wellfound listings | Public/legitimate access, no scraping risk                                   |

## 3. Data model (Supabase tables)

### `tasks`

Queue table — phone inserts rows, worker polls and updates status.

| column       | type      | notes                                                                |
| ------------ | --------- | -------------------------------------------------------------------- |
| id           | uuid (pk) |                                                                      |
| type         | text      | `fetch_jobs`,`score_postings`,`draft_outreach`                 |
| payload      | jsonb     | task-specific input (e.g. contact name + company for draft_outreach) |
| status       | text      | `pending`,`in_progress`,`done`,`failed`                      |
| created_at   | timestamp |                                                                      |
| completed_at | timestamp | nullable                                                             |

### `postings`

| column          | type      | notes                                                    |
| --------------- | --------- | -------------------------------------------------------- |
| id              | uuid (pk) |                                                          |
| source          | text      | `greenhouse`,`lever`,`adzuna`,`manual`           |
| company         | text      |                                                          |
| role_title      | text      |                                                          |
| location        | text      |                                                          |
| url             | text      |                                                          |
| raw_description | text      |                                                          |
| fit_score       | int       | 1–10, set by scoring task                               |
| fit_reasoning   | text      | LLM's explanation                                        |
| resume_variant  | text      | `swe`or`data_ml`                                     |
| fetched_at      | timestamp |                                                          |
| status          | text      | `new`,`shortlisted`,`applied`,`rejected_by_user` |

### `contacts`

| column          | type      | notes                                                 |
| --------------- | --------- | ----------------------------------------------------- |
| id              | uuid (pk) |                                                       |
| name            | text      |                                                       |
| company         | text      |                                                       |
| linkedin_url    | text      |                                                       |
| relation        | text      | `alumni`,`near_peer`,`other`                    |
| message_draft   | text      | generated by draft_outreach task                      |
| message_sent    | boolean   | you mark this manually after sending on LinkedIn      |
| sent_at         | timestamp | nullable                                              |
| response_status | text      | `no_response`,`replied`,`referred`,`declined` |
| follow_up_due   | date      | nullable                                              |

### `applications`

| column           | type                  | notes                                                                                  |
| ---------------- | --------------------- | -------------------------------------------------------------------------------------- |
| id               | uuid (pk)             |                                                                                        |
| posting_id       | uuid (fk → postings) |                                                                                        |
| applied_at       | timestamp             |                                                                                        |
| resume_version   | text                  | which tailored resume was used                                                         |
| contact_id       | uuid (fk → contacts) | nullable, if referred                                                                  |
| status           | text                  | `applied`,`interview_scheduled`,`interviewed`,`offer`,`rejected`,`ghosted` |
| next_action      | text                  | free text                                                                              |
| next_action_date | date                  | nullable                                                                               |

## 4. Repo structure

```
job-hunt-tool/
├── README.md
├── .env.example                 # SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY — never commit real .env
├── .gitignore
│
├── frontend/                    # hosted page, deployed to Vercel/Netlify
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx              (or plain JS if you skip React)
│   │   ├── lib/supabaseClient.js
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # shortlist of postings, sorted by fit_score
│   │   │   ├── Outreach.jsx      # contacts list, draft/send status, follow-ups due
│   │   │   └── Tracker.jsx       # applications kanban/table
│   │   └── components/
│   ├── package.json
│   └── vite.config.js
│
├── worker/                       # runs locally on your laptop
│   ├── main.py                   # poll loop entrypoint
│   ├── config.py                 # loads .env
│   ├── supabase_client.py
│   ├── tasks/
│   │   ├── fetch_jobs.py         # hits Greenhouse/Lever/Adzuna APIs, inserts into postings
│   │   ├── score_postings.py     # calls Gemini, fills fit_score/fit_reasoning/resume_variant
│   │   └── draft_outreach.py     # calls Gemini, fills contacts.message_draft
│   ├── sources/
│   │   ├── greenhouse.py
│   │   ├── lever.py
│   │   └── adzuna.py
│   └── requirements.txt
│
├── supabase/
│   ├── schema.sql                 # full table definitions, run once on a fresh project
│   └── seed.sql                   # optional: a few example companies for greenhouse/lever
│
└── docs/
    ├── setup.md                   # step-by-step: create Supabase project, deploy frontend, run worker
    └── company_sources.md         # your running list of companies + their ATS (greenhouse/lever/etc) and board tokens
```

## 5. Build order (phased)

**Phase 0 — Foundation (~1 evening)**

1. Create Supabase project, run `schema.sql`
2. Get API keys (Supabase, Gemini) into `.env`
3. Write `worker/supabase_client.py`, confirm you can insert/read a row from a script

**Phase 1 — Job fetch + score (highest leverage, build first)**

1. `sources/greenhouse.py` + `sources/lever.py`: hit public board APIs for a hand-picked list of ~15–20 companies relevant to you (`docs/company_sources.md`), normalize into `postings` rows
2. `tasks/fetch_jobs.py`: orchestrates the above, dedupes by URL before inserting
3. `tasks/score_postings.py`: for each new posting, call Gemini with your resume + posting description, get back `fit_score`, `fit_reasoning`, `resume_variant`
4. Test end-to-end with a manually-inserted `fetch_jobs` task row, confirm scored postings appear

**Phase 2 — Minimal frontend**

1. Vite + plain React (or plain HTML if you want zero build step) page deployed to Vercel
2. Dashboard view: table of postings sorted by `fit_score`, a button that inserts a `fetch_jobs` task
3. Confirm phone browser → Supabase → laptop worker → back to phone round-trip works

**Phase 3 — Outreach support**

1. `contacts` table UI: manually add a name/company/LinkedIn URL after you find them via LinkedIn's Alumni tool
2. `tasks/draft_outreach.py`: given a contact + target posting, generate a short personalized message
3. Outreach view: shows draft, a "mark as sent" checkbox, follow-up date field

**Phase 4 — Tracker**

1. Simple table/kanban for `applications`, manually updated as things progress
2. Daily view: "follow-ups due today" pulled from `contacts.follow_up_due`

**Phase 5 — polish (optional, only after the above is in daily use)**

* Realtime subscriptions instead of polling, so the worker reacts within seconds of a task being queued
* Daily auto-run of `fetch_jobs` + `score_postings` via a scheduled local cron, so the shortlist is fresh every morning without manually triggering it

## 6. Operational notes

* **Worker run mode** : simplest is a loop with `time.sleep(60)` between polls. If you want lower latency, use Supabase's realtime channel to get pushed new task rows instantly — only worth doing after Phase 2 works with plain polling.
* **Cost** : Supabase free tier and Vercel free tier comfortably cover this scale. Gemini API calls are the only real cost, and you're already using that for resumes — same budget.
* **Safety** : nothing here automates LinkedIn, Naukri, or Internshala actions. You still click connect/send/apply yourself for anything that touches those platforms' UI — keeps your accounts safe during an active search.
* **Source list maintenance** : `docs/company_sources.md` is just a manually curated list (company name → ATS type → board token/slug). Add to it as you find companies worth tracking; this is low effort and keeps the fetch step honest instead of trying to auto-discover every company.

## 7. Open decisions to confirm before building

* Plain HTML/JS frontend vs React — React only worth it if you want to reuse component patterns; plain HTML+Supabase JS client is fine for 3 simple views
* Polling interval for the worker (start at 60s, tune later)
* Whether to also add USAJobs/government portals, or keep scope to private-sector SWE/Data roles for now
