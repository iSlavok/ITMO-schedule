# ITMO Schedule Bot

**Telegram:** [@scheduleITMO_bot](https://t.me/scheduleITMO_bot)

An asynchronous Telegram bot that delivers the class schedule for ITMO University's Physics and CT faculties, enriched with a peer-driven lecturer rating system.

The faculties' schedules never landed properly in the official ITMO app, so students were left reading raw Google Sheets. This bot sits on top of those sheets: it parses and normalizes it, serves each group its own schedule with awareness of odd/even academic weeks, resolves free-form date queries through an LLM, and prompts students to rate lecturers right after each lesson.

## Features

- **Two faculties** — Physics and CT, each with its own sheet, parser, updater and schedule file. Group names carry a faculty prefix (`Z3142`, `M3132`), so registration asks for the faculty first, then the course and the group.
- **Daily schedule** — today / tomorrow / arbitrary date, rendered per user's group with lesson time, type, room, lecturer, and live status markers (finished / in-progress / upcoming).
- **Odd/even week logic** — the correct weekly variant is selected from the ISO week number.
- **Dated overrides** — one-off and relative (`before`/`after` a date) lesson changes layered on top of the recurring schedule.
- **Natural-language dates** — free text like "завтра" or "next Monday" is parsed into a concrete date by Google Gemini with a structured JSON schema.
- **Lecturer ratings** — lecturers belong to a faculty and are created from the parsed schedules; users rate them on a 1–10 scale; the schedule shows each lecturer's average rating with tiered emoji. A user may rate a given lecturer once per day, and only for lessons that have already taken place today.
- **Rating notifications** — cron jobs fire at each lesson's end time and prompt opted-in users to rate that lesson's lecturer, skipping anyone who already rated them today.
- **Leaderboard** — paginated ranking of top (and bottom) lecturers of the user's own faculty by average rating.
- **Registration & roles** — guests pick faculty → course → group to register; role-gated handlers (`GUEST`, `USER`, `ADMIN`).
- **Clean chat UX** — a message manager tracks bot/user message IDs in FSM state and deletes stale messages so the chat stays a single live view.

## Tech Stack

| Concern | Technology |
|---|---|
| Language | Python 3.13 |
| Bot framework | aiogram 3.18 (async, Router-based) |
| FSM storage | Redis |
| Database | PostgreSQL 17 via SQLAlchemy 2.0 (async) + asyncpg |
| Migrations | Alembic |
| Schedule source | Google Sheets (`gspread` + service account) |
| LLM | Google Gemini (`google-genai`, `gemini-2.5-flash-lite`) |
| Scheduling | APScheduler |
| Config / schemas | Pydantic v2, pydantic-settings |
| Rate limiting | aiolimiter |
| Logging | loguru |
| Packaging | Docker, docker-compose, GHCR |

## Architecture

The codebase is split into a framework-agnostic core (`app/`) and the Telegram presentation layer (`bot/`).

```
app/                         Core domain
├── config/                  Env-backed settings (pydantic-settings)
├── database/                Async engine, session factory, declarative Base
├── models/                  SQLAlchemy ORM: User, Faculty, Course, Group, Lecturer, Rating
├── repositories/            Data access; ScheduleRepository is JSON-file backed
├── schemas/                 Pydantic models: Schedule tree, Lesson, DTOs, AI response
├── services/                Business logic: Schedule, Rating, User, Guest, Ai
├── schedule/                Per-faculty sheet parsers + background updaters
└── enums/                   Weekday, Week, DatedAction, FacultyCode, UserRole, RatingType

bot/                         Telegram layer (aiogram)
├── handlers/                Routers: registration, schedule, rating, rating_list,
│                            settings, admin; plus rating-notification cron jobs
├── keyboards/               Inline / reply keyboard builders
├── callback_data/           Typed callback payloads
├── filters/                 RoleFilter (role-gated access)
├── middlewares/             User, Services (per-flag DI), MessageManager
├── services/                MessageManager (chat message lifecycle)
├── config/                  messages.yaml loader
└── utils/                   Schedule formatter, rate-limit patch
```

### Request flow

Every update passes through a middleware pipeline before reaching a handler:

1. **`UserMiddleware`** (outer) — opens an async DB session, gets-or-creates the `User`, and injects both into handler data.
2. **`ServicesMiddleware`** — instantiates only the services a handler declares via `flags={"services": [...]}`, wiring them to the current session.
3. **`MessageManagerMiddleware`** — attaches a per-chat `MessageManager` that tracks and cleans up messages.

Handlers are gated by `RoleFilter`, so guests, registered users, and admins see disjoint command sets.

### Schedule pipeline

Each faculty is parsed by its own `ScheduleUpdater`, running on startup and every 10 minutes after that, so a sheet that fails to parse only freezes its own faculty.

**Physics** — `ScheduleParser` reads the sheet through the Sheets API, resolves merged cells, applies extensive normalization (weekday/week-type/group maps, subject and lecturer spelling fixes, room and lesson-type extraction via regex), transposes the grid, splits track columns into per-subgroup groups, and collects the footnotes written next to lessons. `DatedScheduleBuilder` sends each distinct footnote to Gemini and turns the answer into dated cancellations, overrides and additions, cached by footnote text.

**CT** — the sheet is published to the web and has no document id behind the link, so `CtScheduleParser` reads its rendered HTML: unlike the CSV export it keeps merges, style classes and the sheet's own row and column indices, and it leaves out rows and columns hidden in the sheet. It carries no footnotes, so it produces a recurring schedule only.

Both write a `Schedule` model keyed by course → group → week → weekday, persisted per faculty (`data/schedule.json`, `data/schedule_ct.json`), and both feed newly seen lecturer names into the lecturers table. `ScheduleService` resolves a group inside its faculty's schedule, layers the dated entries on top, and computes lesson status against the Europe/Moscow clock.
