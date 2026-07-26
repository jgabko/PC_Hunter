<div align="center">

  <h1>OLX PC Hunter (local)</h1>

  <p>
    A scraper that collects pre-built PC listings from OLX, extracts specs
    (regex + AI fallback), stores everything in a local SQLite database, and
    ranks buy/resell ("flip") opportunities through a Streamlit dashboard —
    all running entirely on your own machine.
  </p>

</div>

<br />

> **Branch note:** this is the **`local`** branch — the original, fully
> self-contained version of the project. Everything runs on your own
> machine: SQLite for storage, Streamlit for the dashboard, no cloud
> accounts required beyond an optional Groq API key. If you're looking for
> the cloud-hosted version (Postgres/Supabase, FastAPI on Render, React on
> Vercel, scheduled scraping via GitHub Actions), check out the **`main`**
> branch instead.

<!-- Table of Contents -->
## Table of Contents

- [About the Project](#about-the-project)
  * [Tech Stack](#tech-stack)
  * [Features](#features)
- [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
  * [Environment Variables](#environment-variables)
- [Usage](#usage)
  * [Running the full pipeline](#running-the-full-pipeline)
  * [Running the Streamlit dashboard](#running-the-streamlit-dashboard)
  * [Running the FastAPI + React version (optional)](#running-the-fastapi--react-version-optional)
- [Project Structure](#project-structure)
- [Known Gaps](#known-gaps)
- [How this differs from the `main` branch](#how-this-differs-from-the-main-branch)
- [Roadmap](#roadmap)
- [License](#license)

<!-- About the Project -->
## About the Project

**OLX PC Hunter** scrapes pre-built desktop PC listings from OLX, extracts
their specs (CPU, GPU, RAM, storage) using regex with an AI fallback
(Groq/Ollama), scores each listing against a benchmark database, and
surfaces the best buy/resell opportunities.

This branch (`local`) is the original version of the project: everything —
scraping, storage, and the dashboard — runs locally on your machine, with no
cloud infrastructure to set up. It's the simplest way to try the project or
develop new features without touching Supabase, Render, or Vercel.

### Tech Stack

<details>
  <summary>Collection & Processing</summary>
  <ul>
    <li><a href="https://www.python.org/">Python</a></li>
    <li>Regex-based spec extraction</li>
    <li><a href="https://groq.com/">Groq</a> / <a href="https://ollama.com/">Ollama</a> (AI fallback for spec extraction)</li>
    <li><a href="https://docs.pydantic.dev/">Pydantic</a> (schema validation)</li>
    <li><a href="https://curl-cffi.readthedocs.io/">curl_cffi</a> (browser-impersonating HTTP client)</li>
  </ul>
</details>

<details>
  <summary>Persistence & Visualization</summary>
  <ul>
    <li><a href="https://www.sqlite.org/">SQLite</a></li>
    <li><a href="https://streamlit.io/">Streamlit</a> (dashboard)</li>
  </ul>
</details>

### Features

- Scrapes OLX listing and detail pages for pre-built PCs
- Extracts specs (CPU/GPU/RAM/Storage) via regex, with AI (Groq/Ollama) as fallback
- Validates listings with Pydantic (drops items missing price/link)
- Persists everything locally in SQLite (`olx.db`)
- Automatically archives sold/expired listings
- Scores/ranks PCs against a CPU/GPU/RAM/Storage benchmark database
- Streamlit dashboard to browse flip opportunities

## Getting Started

### Prerequisites

This project uses Python.

```bash
python --version
```

### Installation

Clone the `local` branch specifically:

```bash
git clone -b local https://github.com/jgabko/PC_Hunter.git
cd PC_Hunter
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set up environment variables:

```bash
cp .env.example .env
```

### Environment Variables

Fill in `.env` with:

| Variable | Required | Description |
|----------|----------|--------------|
| `GROQ_API_KEY` | Yes (for AI fallback) | From [console.groq.com/keys](https://console.groq.com/keys). |
| `USE_GROQ` | No (default `true`) | `true` uses Groq (cloud), `false` uses a local Ollama instance instead — fully offline if you go this route. |
| `OLX_BASE_URL` | No | Overrides the default OLX search URL. |
| `DB_NAME` | No (default `olx.db`) | SQLite database filename. |

## Usage

### Running the full pipeline

```bash
python pipeline.py
```

This scrapes new listings, extracts specs (regex first, AI for whatever
regex can't resolve), and cleans up expired listings — all in one pass.

### Running the Streamlit dashboard

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501` by default. Use it to filter by score and
price range, and browse flip/fusion opportunities.

### Running the FastAPI + React version (optional)

This branch also includes the newer API + React dashboard (`api.py` and
`pc-hunter-frontend/`), if you'd rather use that instead of the Streamlit
one:

```bash
# ⚠️ requirements.txt on this branch doesn't include fastapi/uvicorn yet —
# install them manually first:
pip install fastapi uvicorn

uvicorn api:app --reload
```

```bash
cd pc-hunter-frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000` for the API, which matches
`uvicorn api:app --reload`'s default — no extra configuration needed for
local use.

## Project Structure

```
config.py              # Central configuration (.env) — URLs, DB name, API keys
pipeline.py             # Orchestrator: scraping -> cleanup -> ready for the dashboard
dashboard.py            # Streamlit dashboard (flips and PC "fusions")
api.py                   # FastAPI app (optional alternative to the Streamlit dashboard)
flipper.py                # PC score/ranking calculation (uses benchmarks.py)
benchmarks.py              # CPU/GPU/RAM/Storage benchmark database
cleaner.py                  # Detects and removes sold/expired listings
clean_db.py                  # Fixes corrupted records

scraping/                # OLX listing/detail page collection
  olx.py                     # Main scraper loop
  olx_detail_page.py           # Detail-page spec extraction

processing/               # Raw data transformation
  specs.py                     # Regex-based spec extraction
  specs_AI.py                    # Hybrid pipeline: regex first, AI (Groq/Ollama) for the rest

schema/                    # Validation
  schema.py                      # Pydantic model that drops items missing price/link

persistence/                # Data access
  persist.py                      # SQLite access layer (olx.db)

pc-hunter-frontend/          # React + Vite dashboard (optional, alternative to Streamlit)
```

## Known Gaps

- `requirements.txt` on this branch doesn't list `fastapi` or `uvicorn`,
  even though `api.py` exists and depends on both — install them manually
  (`pip install fastapi uvicorn`) if you want to run the API/React version.
  The `main` branch's `requirements.txt` has this fixed.
- The database file (`olx.db`) is created automatically the first time you
  run `pipeline.py` — you don't need to create it yourself.

## How this differs from the `main` branch

| | `local` (this branch) | `main` |
|---|---|---|
| Database | SQLite (`olx.db`, local file) | Postgres (Supabase) |
| Dashboard | Streamlit (`dashboard.py`) | React (`pc-hunter-frontend/`) |
| Scraping | Manual (`python pipeline.py`) | Scheduled (GitHub Actions, every 6h) |
| Hosting | None — runs on your machine | Render (API) + Vercel (frontend) |
| Setup cost | Minimal — just Python + a Groq key | Requires Supabase/Render/Vercel accounts |

If you just want to try the project quickly or hack on the scraping/spec
extraction logic, this branch is the simplest starting point. For the
production, always-on version, see the `main` branch's README.

## Roadmap

* [x] OLX scraping (listing + detail pages)
* [x] Regex + AI spec extraction
* [x] SQLite persistence with automated cleanup
* [x] Streamlit dashboard with flip ranking
<!--* [ ] Automatic notifications for new opportunities
* [ ] Support for platforms beyond OLX-->

## License

Distributed with no defined license. See `LICENSE.txt` for more information.
