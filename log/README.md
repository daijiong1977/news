# Log Directory

This directory contains intermediate pipeline results, temporary outputs, and logs that are **not synced to git**.

## Contents

### Pipeline Results
- `pipeline_results_*.json` - Output from pipeline.py runs (timestamps included)

### Logs & Reports
- `*.txt` - Text logs and status reports
- `*.log` - Application logs

### Temporary Files
- Intermediate processing results
- Checkpoint files
- Cache data

## Why Not Synced?

These files are:
- **Ephemeral**: Generated during runs, can be regenerated anytime
- **Large**: Accumulate over time (especially JSON results)
- **Noisy**: Would clutter git history with unimportant changes
- **Not reproducible**: Environment-specific, not part of source code

## Cleanup

Periodically clean up old logs:
```bash
# Remove logs older than 7 days
find log -type f -mtime +7 -delete

# Remove all logs (keep directory)
rm -f log/*.json log/*.txt log/*.log
```

## In .gitignore

The entire `log/` directory is ignored by git:
```
# Backups and temporary data
backups/
unused/
website/backup/
log/
```

This `.gitkeep` file ensures the directory exists in the repo for consistent project structure.
