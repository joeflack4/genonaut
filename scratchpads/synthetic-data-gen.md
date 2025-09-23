# Agent Prompt: Synthetic Data Generator Plan and Implementation

**Goal:** Propose libraries and design, then implement a fast, FK-aware synthetic data generator for our Postgres schema (SQLAlchemy models exist). Produce an **action plan first** in `scratchpads/synthetic-data-gen.md`, then implement code under `genonaut/db/demo/seed_data_gen/` with a CLI (`python -m genonaut.db.demo.seed_data_gen ...`) that reads `config.json` and supports overriding any key via CLI flags.

---

## Inputs & Context for You (the Agent)

1) **SQLAlchemy models** define all tables and relationships; you can introspect them to honor FKs.
2) **Seed TSVs (examples to study):**
   - `/mnt/data/users.tsv`
   - `/mnt/data/content_items.tsv`
   - `/mnt/data/content_items_auto.tsv`
   - `/mnt/data/generation_jobs.tsv`
   - `/mnt/data/recommendations.tsv` (ignore for now)
   - `/mnt/data/user_interactions.tsv` (ignore for now)
3) **Environment:** `.env` contains `DEMO_ADMIN_UUID`. If missing/invalid, the generator must raise `RuntimeError` explaining it must be present; also **print** a pre-generated UUID that the user may copy into `.env`.
4) **Images directory:** Read the base path for images from `config.json` key `images_dir`. Do **not** create files; only write paths like `{images_dir}/{uuid}.png` into DB columns.

---

## Your First Deliverable

Create **`scratchpads/synthetic-data-gen.md`** with:
- A short **library landscape** and **recommendation** for each concern (ORM-aware FK-safe generation, ultra-fast bulk insertion, field-level faker, large-scale prompt templating/grammar). Include trade-offs.
- A **high-level architecture** diagram/outline (modules, data flow, concurrency model).
- A concrete **implementation plan** with tasks, acceptance criteria, and test strategy.
- Performance targets & observability plan (see below).

When you’ve drafted this, proceed to implementation.

---

## Libraries to Evaluate and Consider (pick what fits best, justify choices)

- **FK-aware / ORM factories:** Factory Boy, Polyfactory (with SQLAlchemy), direct SQLAlchemy model reflection.
- **Field generators:** Faker, mimesis.
- **Prompt generation:** Jinja2 (templating), tracery (CFR grammar) for variety and speed.
- **Bulk loading:** SQLAlchemy `bulk_insert_mappings`, psycopg `COPY FROM STDIN` (via `psycopg` copy functions); consider temporary CSV/NDJSON streaming; also consider `asyncpg` for high-throughput inserts if justified.
- **Concurrency:** `multiprocessing` or `concurrent.futures.ProcessPoolExecutor` for prompt generation and batch preparation; DB inserts should be sized to avoid lock contention.
- **Config & CLI:** `argparse` or `typer` for CLI; `pydantic` for config schema/validation.

Document trade-offs and the final picks in the plan.

---

## Functional Requirements (by table)

### A) users
- `id`: UUID v4. **Admin** user identified by `DEMO_ADMIN_UUID` in `.env` (must exist or raise as above).
- `username`: random; on **unique conflict** within batch, **filter out** conflicting rows and retry batch insert; **log warning** listing the conflicting usernames and count removed.
- `email`: random.
- `created_at`, `updated_at`: random datetimes between **2025-05-01 00:00:00** and **2025-09-21 23:59:59** (use ET for generation; store UTC in DB).
- `is_active`: 99% `true`.
- `preferences` (JSONB): only include `favorite_tags` key for now; choose 0–10 tags from global tag pool (see tags list below).

### B) content_items & content_items_auto
- `content_type`: always `"image"`.
- `title`: first **20 characters** of the prompt for that row.
- `content_data`: path formed as `"{images_dir}/{uuid}.png"` where `images_dir` comes from `config.json`.
- `item_metadata`: include:
  - `style`: one of `["anime", "illustration", "photorealistic"]`.
  - `resolution`: choose from common sizes (e.g., `1024x768`, `1920x1080`, `2560x1440`, etc.).
  - `tags`: select **0–200** items from the global tag list below; make it a list (no duplicates per item).
- `quality_score`: random float in `[0, 1]` with two decimal places.
- `is_private`: random boolean, **90% false**, 10% true. **Do not mention or touch `is_public`.**
- `creator_id` (FK to users): ensure **exactly 50** rows **in each of the two tables** are attributed to the **Admin UUID**. The rest may be any other users, arbitrary distribution is fine.

### C) generation_jobs
- For **every** row in `content_items` **and** `content_items_auto`, create **one** corresponding `generation_jobs` row with **status = "completed"`**.
- `prompts`: generated text (see Prompt Generation rules below).
- `parameters`: may be empty for now.
- `status` distribution **over all generation jobs** (including the above “completed per item” rows):
  - 98% `completed`
  - 0.9% `pending`
  - 0.1% `canceled`
  - 1% `error`
- `error_message`: blank.
- `created_at`, `started_at`: blank.
- `completed_at`: random datetime **between 2025-05-01 and 2025-09-21** (ET for generation, store UTC).

---

## Prompt Generation

- Introduce a **virtual “prompt type”** (not a DB field) with values like: `fashion, portraits, landscapes, fantasy art, sci-fi art, animals, food photography, architecture, interior design, concept art, anime characters, cartoons, product mockups, posters, logos, book covers, album covers, video game art, abstract art, surreal art, film stills, comic panels, 3D renders, medical illustration, educational diagrams, historical scenes, celebrity lookalikes, memes, children’s illustrations, gothic/horror art`.
- Each prompt randomly includes **0–10** phrases from a **general** list (provided below) and **4–30** phrases from a **domain-specific** list (you will paste the 30-category domain-specific list separately later; **do not** include it in the plan doc).
- **General phrases** (sample pool to use): `highly detailed, ultra realistic, cinematic lighting, soft lighting, dramatic shadows, HDR, 8k, 4k, trending on artstation, hyper-realistic, surreal, dreamy, fantasy-inspired, science fiction, vivid colors, muted tones, monochrome, sepia, wide shot, close-up, portrait shot, landscape format, symmetrical, asymmetrical, painterly, photorealistic, digital painting, illustration, anime style, stylized`.

Use Jinja2 templates or tracery grammars to compose diverse prompts quickly; ensure combinatorial variety and reproducibility **is not required**.

---

## Global Tag Pool (for item_metadata.tags and users.preferences.favorite_tags)

`realistic, stylized, abstract, surreal, cinematic, minimalism, vintage, modern, futuristic, fantasy, sci-fi, horror, gothic, whimsical, colorful, monochrome, high-detail, low-poly, hand-drawn, photorealistic, 3D, 2D, illustration, digital-painting, anime, editorial, concept-art, experimental, moody, vibrant, HDR, 8k, 4k, trending, painterly, expressive, atmospheric, dreamy, ethereal, mystical, elegant, gritty, dark, moody, bright, neon, pastel, warm, cool, soft-light, hard-light, dynamic, action, still-life, panoramic, close-up, macro, wide-angle, fisheye, tilt-shift, isometric, top-down, overhead, bird’s-eye, worm’s-eye, cinematic-framing, editorial-style, magazine-cover, poster-style, thumbnail, logo-ready, minimalist-typography, ornate, decorative, symmetrical, asymmetrical, textured, flat, glossy, matte, vector, raster, pixel-art, voxel, cel-shaded, line-art, inked, watercolor, oil-painting, acrylic, charcoal, chalk, pastel, marker, crayon, collage, photobash, 3D-render, sculpture, installation, mixed-media, surreal-collage, glitch`

---

## Performance, Batching, and Progress

- **Batch sizes (defaults via `config.json`):**
  - `batch_size_content_items`: **2000**
  - `batch_size_content_items_auto`: **2000**
  - `target_rows_content_items`: **20000**
  - `target_rows_content_items_auto`: **100000**
- **CLI must allow overriding any `config.json` key** (e.g., `--batch_size_content_items 5000`).
- Use the **fastest feasible insertion path** (COPY or equivalent). Respect FKs (generate in dependency order).
- **Concurrency** is allowed for prompt generation and batch preparation; keep DB inserts serialized enough to avoid deadlocks.
- **Logging / progress:**
  - Print **progress per batch**: how many inserted so far and **percent complete** for each target.
  - On exit (success or error), print **total records created per table** and **total wall time**.
  - On username conflicts, log **warning** with the conflict details and removed row count.
- **Timing:** Measure and print **elapsed time**. If the run errors, still print **partial counts** completed and elapsed time.

---

## Config and CLI

- Provide a `config.json` in repo root with (at least):
  ```json
  {
    "images_dir": "data/images",
    "batch_size_content_items": 2000,
    "batch_size_content_items_auto": 2000,
    "target_rows_content_items": 20000,
    "target_rows_content_items_auto": 100000
  }
  ```
- CLI (module entrypoint already at `genonaut/db/demo/seed_data_gen/__main__.py`):
  - `python -m genonaut.db.demo.seed_data_gen generate --prompt-types <list?> --max-workers <int?> ...`
  - Any CLI flag should override the corresponding `config.json` key.
  - Include `--dry-run` (validate + preview counts without writing).

---

## Acceptance Criteria

- Action plan written to `scratchpads/synthetic-data-gen.md` covering the sections above.
- Code implements FK-safe generation, adheres to field rules, status distributions, and date ranges.
- Exactly **50 admin-owned rows** exist in **each** of `content_items` and `content_items_auto`.
- For every item, a corresponding **completed** `generation_jobs` row exists.
- Progress printed every batch; final summary includes counts and total elapsed time; partial stats print on error.
- Fast-path insertion used; retries handle username uniqueness with warnings.
- Config file present; CLI overrides work for **any** config key.

---

## Notes

- You will **paste** the 30 domain-specific phrase lists later into the plan or code (do **not** include them now).
- Keep things ET for generation, store UTC in DB.
- Do not create real images; only write paths using `images_dir`.
