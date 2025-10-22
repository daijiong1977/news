# Deepseek Testing & QA

This document describes how to run local Deepseek testing flows and helper utilities included in this workspace.

Files added
- `deepseek_testing_cleanup.py` — create DB backups, ensure schema columns exist, and reset deepseek flags for testing.
- `deepseek_test_runner.py` — run a simulated end-to-end processing loop for unprocessed articles, optionally using prepared response JSON files and generating HTML pages.
- `generate_four_blocks.py` — (existing) generates a 4-block HTML page (Hard / Mid / Easy / ZH) for a given article id.

Quick start (safe):

1. Create a DB backup and show current counts:

```bash
python3 deepseek_testing_cleanup.py --backup --show
```

2. Reset all deepseek flags (optional):

```bash
python3 deepseek_testing_cleanup.py --backup --reset-all
```

3. Prepare response JSON files for articles you want to test. Name them with the pattern:

```
response_article_<id>_YYYYMMDD_HHMMSS.json
```

Place them in a folder (e.g. `./responses`) or copy them into the local `responses/` directory.

4. Run the test runner in dry-run to verify which articles would be processed:

```bash
python3 deepseek_test_runner.py --per-feed 10 --response-dir ./responses --dry-run
```

5. Apply the run (will call `insert_from_response.py` and generate HTML):

```bash
python3 deepseek_test_runner.py --per-feed 10 --response-dir ./responses --apply
```

Notes:
- The runner expects `insert_from_response.py` and `generate_four_blocks.py` to be present in the workspace (they are).
- The runner currently processes only `deepseek_processed=0 AND deepseek_failed<3` articles and respects `deepseek_in_progress`.
- For safety, prefer the `--dry-run` option first.

If you want me to commit these new files to git now, I'll create a commit message `ds_testing: add testing helpers and runner` and stage & commit the three files.
