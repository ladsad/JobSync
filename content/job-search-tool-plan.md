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

**Pattern: MCP-server architecture** driven by interactive IDE conversation.

```
Phone (hosted page) → Hosted DB (Supabase) ← Laptop MCP Server ← Antigravity IDE (LLM)
```

* The laptop runs an MCP server (Python, using the `mcp` SDK, stdio transport) that is launched by and connected to Antigravity IDE.
* Antigravity's own chat model does the reasoning (scoring job fit, drafting outreach messages) interactively in conversation.
* The MCP server only exposes mechanical tools for fetching job postings and reading/writing Supabase. 
* No separate Gemini API key or cost is needed for this part, since Antigravity's existing model access is reused.

**Stack**

| Piece           | Choice                                                                   | Why                                                                          |
| --------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| Hosted DB + API | Supabase (Postgres, free tier)                                           | Auto REST API + realtime + auth, no custom backend needed                    |
| Hosted frontend | Static page on Vercel/Netlify                                            | Talks to Supabase directly from the browser, free tier                       |
| Laptop server   | Python script (`mcp` SDK)                                                | You're a dev, full control, integrates directly with Antigravity             |
| LLM             | Antigravity (already set up)                                             | Reasoning and drafting happens interactively, zero additional LLM API costs  |
| Job sources     | Greenhouse + Lever public job-board APIs, Adzuna API, Wellfound listings | Public/legitimate access, no scraping risk                                   |

## 3. Data model (Supabase tables)

### `tasks` (Optional)

Queue table — only needed if the phone page should be able to queue something for the MCP server/Antigravity to pick up later, rather than for routine operation.

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
├── .env.example                 # SUPABASE_URL, SUPABASE_KEY — never commit real .env
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
├── mcp-server/                   # runs locally on your laptop, launched by Antigravity
│   ├── main.py                   # MCP server entrypoint
│   ├── config.py                 # loads .env
│   ├── supabase_client.py
│   ├── tools.py                  # exposes MCP tool functions
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
    ├── setup.md                   # step-by-step: create Supabase project, deploy frontend, setup MCP
    └── company_sources.md         # your running list of companies + their ATS (greenhouse/lever/etc) and board tokens
```

*Note: Register the server in Antigravity's `mcp_config.json` to enable the IDE to launch and communicate with it.*

## 5. Build order (phased)

**Phase 0 — Foundation (~1 evening)**

1. Create Supabase project, run `schema.sql`
2. Get API keys (Supabase) into `.env`
3. Write `mcp-server/supabase_client.py`, confirm you can insert/read a row from a script

**Phase 1 — Job fetch + score (MCP Tools)**

1. `sources/greenhouse.py` + `sources/lever.py`: hit public board APIs for a hand-picked list of ~15–20 companies relevant to you (`docs/company_sources.md`), normalize into `postings` rows
2. `tools.py`: Implement MCP tool functions: `fetch_greenhouse_postings`, `fetch_lever_postings`, `get_pending_postings`, `save_posting_score`.
3. Test the tools by invoking them conversationally from Antigravity. Ask Antigravity to fetch jobs and score them based on your resume.

**Phase 2 — Minimal frontend (Read-mostly dashboard)**

1. Vite + plain React (or plain HTML if you want zero build step) page deployed to Vercel
2. Dashboard view: table of postings sorted by `fit_score`. 
3. *Note: The frontend becomes a read-mostly dashboard rather than a trigger mechanism, since work is now driven by chatting in Antigravity rather than by the phone queuing tasks.*

**Phase 3 — Outreach support**

1. `contacts` table UI: manually add a name/company/LinkedIn URL after you find them via LinkedIn's Alumni tool
2. `tools.py`: Implement `add_contact` and `save_message_draft`.
3. Outreach view: shows draft, a "mark as sent" checkbox, follow-up date field
4. Test drafting personalized messages by invoking the tool conversationally from Antigravity.

**Phase 4 — Tracker**

1. `tools.py`: Implement `list_followups_due` and `update_application`.
2. Simple table/kanban for `applications`, manually updated as things progress
3. Daily view: "follow-ups due today" pulled from `contacts.follow_up_due`

## 6. Tradeoffs of the MCP approach

* **Pros**: No separate LLM API cost is required since reasoning occurs interactively in Antigravity. It results in better interactive quality for tasks like drafting outreach messages and drastically reduces the amount of backend logic needed.
* **Cons**: Loses unattended or scheduled automation capabilities. Because nothing runs unless Antigravity is open and actively chatting, you cannot trigger background jobs remotely. 

*If scheduled/unattended automation (e.g., a daily 7am auto-shortlist) is wanted later, that would need a small separate script calling an LLM API directly, outside the MCP/Antigravity flow.*

## 7. Open decisions to confirm before building

* Plain HTML/JS frontend vs React — React only worth it if you want to reuse component patterns; plain HTML+Supabase JS client is fine for 3 simple views
* Whether to also add USAJobs/government portals, or keep scope to private-sector SWE/Data roles for now
* Whether to keep the `tasks` queue table at all, given the move to an interactive MCP architecture.
* Whether unattended daily scheduling is a priority for v1 or a later addition.
