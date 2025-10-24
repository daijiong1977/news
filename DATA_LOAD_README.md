# Data load & mining workflow

This document explains how to run the data collection, mining (sampling), AI preview, and canonical insert flows separately and safely.

Files of interest
- `data_collector.py` — collects articles from RSS feeds and inserts into `articles` table.
- `run_mining_cycle.py` — samples unprocessed articles, calls AI preview (Deepseek) and optionally runs the canonical inserter.
- `process_one_article.py` — single-article AI preview (used by the runner).
- `insert_from_response.py` — canonical inserter: takes a preview JSON file and writes normalized rows (summaries, keywords, questions, choices, background_read, article_analysis, comments) into the DB.
- `config/thresholds.json` — thresholds and run parameters (num_per_source, sample_rate, max_fetch_per_feed).
- `articles.db` — local SQLite database (not checked into git by default).

Safety first
- Always backup `articles.db` before running any operation that may modify or delete rows. For convenience you can create a backup under `backups/`:
```
mkdir -p backups
cp articles.db backups/articles.db.backup_$(date +%Y%m%d_%H%M%S).sqlite
```
- `insert_from_response.py` may perform destructive replaces for repeated inserts; ensure you have a backup before running the inserter.

1) Run data collection (mining)

This step populates the `articles` table from the RSS feeds configured in the DB.

- Review `config/thresholds.json` and set:
  - `num_per_source`: how many *clean* articles to store per feed (the collector stops after this many per feed).
  - `max_fetch_per_feed`: how many raw RSS items to fetch from each feed (defaults to 10).

Run the collector (safe — it writes the DB):
```
python3 data_collector.py
```

2) Run sampling + AI preview (dry-run)

This step samples stored unprocessed articles and generates preview JSON files for later verification. By default `run_mining_cycle.py` runs in dry-run (no API calls), producing placeholder previews in `./responses/`.

Adjust sampling in `config/thresholds.json`:
- `sample_rate`: integer N for 1-in-N sampling (default 10). Set `sample_rate = 1` to process all collected articles.
- `num_per_source` is used by the collector; sampling runs on the stored records.

Run dry-run (no API calls):
```
python3 run_mining_cycle.py
```

Dry-run behavior:
- Collector runs (reads `num_per_source`), sampler selects 1-in-N candidates, and a placeholder preview JSON is written to `./responses/` for each selected article.
- No AI calls, no database modifications to normalized tables.

3) Run sampling + AI preview + canonical insert (apply)

When you're ready to call the AI and insert normalized rows, export your Deepseek API key and run with `--apply`:

```
export DEEPSEEK_API_KEY=sk-...
python3 run_mining_cycle.py --apply
```

What happens:
- The runner collects new articles (using `num_per_source`), samples stored articles (1-in-N), calls the Deepseek API for each sampled article, saves preview JSON in `./responses/`, and runs `insert_from_response.py` with each preview file.
- `insert_from_response.py` does canonical insertion and updates `articles` flags (`deepseek_processed`, clears `deepseek_in_progress`) and inserts into normalized tables.

4) Manual preview + insert (one article)

If you prefer manual verification per article:

- Generate a preview for a single article (the script will save a preview JSON in the repo root):
```
export DEEPSEEK_API_KEY=sk-...
python3 process_one_article.py
```
- This creates a `response_article_<id>_<timestamp>.json` file. Inspect and verify the file.
- Then run the canonical inserter on the approved JSON:
```
python3 insert_from_response.py response_article_<id>_<timestamp>.json
```

5) Troubleshooting & tips
- If the collector is processing feeds you thought were disabled, check the `feeds` table `enable` column — the collector reads feeds from the DB (`WHERE f.enable = 1`). You can reconcile `config.json` and the DB if you manage feeds from `config.json`.
- To disable a feed quickly in the DB:
```
sqlite3 articles.db "UPDATE feeds SET enable = 0 WHERE feed_name = 'BBC Science';"
```
- To re-run a specific article (force re-process) you'll need to reset its `deepseek_processed` and `deepseek_failed` flags in the DB (or we can add a `--force` runner option).

6) Useful quick commands
- List feeds and enable status:
```
sqlite3 articles.db "SELECT feed_id, feed_name, enable FROM feeds ORDER BY feed_name;"
```
- Show selected responses:
```
ls -1 responses/response_article_*.json
```

7) Development notes
- `run_mining_cycle.py` performs claims with `deepseek_in_progress` to avoid parallel runs conflicting.
- Backups are created automatically by some inserter flows; however, create an explicit backup before any destructive operation.

If you'd like, I can add a `--force` option to `run_mining_cycle.py`, implement an automatic `config.json` -> DB reconciliation for feeds, or add a small script to revert `deepseek_processed` for selected articles. Tell me which helper you'd like next.
