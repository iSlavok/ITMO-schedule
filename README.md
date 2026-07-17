# ITMO Schedule Bot

**Telegram:** [@scheduleITMO_bot](https://t.me/scheduleITMO_bot)

An asynchronous Telegram bot that delivers the class schedule for ITMO University's Physics faculty, enriched with a peer-driven lecturer rating system.

The faculty's schedule never landed properly in the official ITMO app, so students were left reading a raw Google Sheet. This bot sits on top of that sheet: it parses and normalizes it, serves each group its own schedule with awareness of odd/even academic weeks, resolves free-form date queries through an LLM, and prompts students to rate lecturers right after each lesson.

## Features

- **Daily schedule** — today / tomorrow / arbitrary date, rendered per user's group with lesson time, type, room, lecturer, and live status markers (finished / in-progress / upcoming).
- **Odd/even week logic** — the correct weekly variant is selected from the ISO week number.
- **Dated overrides** — one-off and relative (`before`/`after` a date) lesson changes layered on top of the recurring schedule.
- **Natural-language dates** — free text like "завтра" or "next Monday" is parsed into a concrete date by Google Gemini with a structured JSON schema.
- **Lecturer ratings** — users rate lecturers on a 1–10 scale; the schedule shows each lecturer's average rating with tiered emoji. A user may rate a given lecturer once per day, and only for lessons that have already taken place today.
- **Rating notifications** — cron jobs fire at each lesson's end time and prompt opted-in users to rate that lesson's lecturer, skipping anyone who already rated them today.
- **Leaderboard** — paginated ranking of top (and bottom) lecturers by average rating.
- **Registration & roles** — guests pick course → group to register; role-gated handlers (`GUEST`, `USER`, `ADMIN`).
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
├── models/                  SQLAlchemy ORM: User, Course, Group, Lecturer, Rating
├── repositories/            Data access; ScheduleRepository is JSON-file backed
├── schemas/                 Pydantic models: Schedule tree, Lesson, DTOs, AI response
├── services/                Business logic: Schedule, Rating, User, Guest, Ai
├── schedule/                Google Sheets parser + background updater
└── enums/                   Weekday, Week, DateType, UserRole, RatingType

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

`ScheduleParser` reads the source Google Sheet, resolves merged cells, applies extensive normalization (weekday/week-type/group maps, subject and lecturer spelling fixes, room and lesson-type extraction via regex), transposes the grid, and produces a nested `Schedule` model keyed by course → group → week → weekday. `ScheduleUpdater` runs this on startup and then on a background thread every 10 minutes. The parsed result is persisted as `data/schedule.json`; `data/dated_schedule.json` holds manual date-specific overrides. `ScheduleService` merges the recurring and dated schedules at query time and computes lesson status against the Europe/Moscow clock.
