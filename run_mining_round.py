#!/usr/bin/env python3
"""
run_mining_round.py

Select 1-in-N unprocessed articles per source, save previews, and optionally insert.

Usage:
  python3 run_mining_round.py        # dry-run: save
    preview placeholders
  python3 run_mining_round.py --apply  # call Deepseek API and run inserter
"""

import os
import sys
import json
import sqlite3
import random
from datetime import datetime
import argparse

THRESHOLDS_PATH = os.path.join(os.getcwd(), 'config', 'thresholds.json')
DB_PATH = os.path.join(os.getcwd(), 'articles.db')
RESPONSES_DIR = os.path.join(os.getcwd(), 'responses')


def ensure_responses_dir():
    os.makedirs(RESPONSES_DIR, exist_ok=True)


def get_unprocessed_by_source(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, source FROM articles WHERE deepseek_processed = 0 AND (deepseek_failed IS NULL OR deepseek_failed < 4)")
    rows = cur.fetchall()
    by_source = {}
    for row in rows:
        aid, src = row[0], row[1]
        by_source.setdefault(src or 'unknown', []).append(aid)
    return by_source


def claim_article(conn, article_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE articles SET deepseek_in_progress = 1 WHERE id = ? AND (deepseek_in_progress IS NULL OR deepseek_in_progress = 0)",
        (article_id,)
    )
    conn.commit()
    return cur.rowcount == 1


def release_claim(conn, article_id):
    cur = conn.cursor()
    cur.execute("UPDATE articles SET deepseek_in_progress = 0 WHERE id = ?", (article_id,))
    conn.commit()


def fetch_article_row(conn, article_id):
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, content, category_id FROM articles WHERE id = ?", (article_id,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'content': row[3],
        'category_id': row[4]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Run API calls and inserter')
    args = parser.parse_args()

    # Load thresholds
    if not os.path.exists(THRESHOLDS_PATH):
        print(f"Missing thresholds file: {THRESHOLDS_PATH}")
        sys.exit(1)
    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)

    sample_rate = int(thresholds.get('sample_rate', 10))
    seed = int(thresholds.get('random_seed', 42)) if 'random_seed' in thresholds else 42

    ensure_responses_dir()

    rng = random.Random(seed)

    conn = sqlite3.connect(DB_PATH)
    try:
        by_source = get_unprocessed_by_source(conn)
        print(f"Found {len(by_source)} sources with unprocessed articles")

        to_process = []
        for src, ids in by_source.items():
            selected = [aid for aid in ids if rng.randrange(sample_rate) == 0]
            if selected:
                print(f"Source '{src}': selected {len(selected)} of {len(ids)} articles")
                to_process.extend(selected)

        print(f"Total articles selected: {len(to_process)}")

        process_with_api = None
        if args.apply:
            if not os.environ.get('DEEPSEEK_API_KEY'):
                print("ERROR: DEEPSEEK_API_KEY not set. Set it with: export DEEPSEEK_API_KEY=your_key_here")
                sys.exit(1)
            import process_one_article
            process_with_api = process_one_article.process_article_with_api

        for article_id in to_process:
            print(f"\n--- Processing article {article_id} ---")
            if not claim_article(conn, article_id):
                print(f"Could not claim article {article_id} (already in progress). Skipping.")
                continue

            article = fetch_article_row(conn, article_id)
            if not article:
                print(f"Article {article_id} disappeared. Releasing claim.")
                release_claim(conn, article_id)
                continue

            if args.apply and process_with_api:
                response = process_with_api(article, process_one_article.COMPACT_PROMPTS['default'])
                if response is None:
                    print(f"Processing failed for {article_id}. Incrementing failure counter and releasing claim")
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE articles SET deepseek_failed = COALESCE(deepseek_failed,0)+1, deepseek_last_error = ?, deepseek_in_progress = 0 WHERE id = ?",
                        ("process_failed", article_id)
                    )
                    conn.commit()
                    cur.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
                    r = cur.fetchone()
                    failed_count = r[0] if r else 0
                    if failed_count and failed_count > 3:
                        print(f"deepseek_failed > 3 for article {article_id}; deleting article")
                        cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                        conn.commit()
                    continue

                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{article_id}_{ts}.json'
                fpath = os.path.join(RESPONSES_DIR, fname)
                with open(fpath, 'w') as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)
                print(f"Saved preview to {fpath}")

                # Run inserter
                ret = os.system(f'python3 insert_from_response.py "{fpath}"')
                if ret != 0:
                    print(f"Inserter returned non-zero status for {article_id}: {ret}; releasing claim")
                    release_claim(conn, article_id)
                else:
                    print(f"Inserter succeeded for {article_id}")
            else:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{article_id}_{ts}.json'
                fpath = os.path.join(RESPONSES_DIR, fname)
                preview = {'meta': {'article_id': article_id, 'title': article.get('title'), 'dry_run': True, 'selected_at': ts}}
                with open(fpath, 'w') as f:
                    json.dump(preview, f, ensure_ascii=False, indent=2)
                print(f"Dry-run saved preview placeholder to {fpath}")
                release_claim(conn, article_id)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
run_mining_round.py

Select 1-in-N unprocessed articles per source, save previews, and optionally insert.

Usage:
  python3 run_mining_round.py        # dry-run: save preview placeholders
  python3 run_mining_round.py --apply  # call Deepseek API and run inserter
"""

import os
import sys
import json
import sqlite3
import random
from datetime import datetime
import argparse

THRESHOLDS_PATH = os.path.join(os.getcwd(), 'config', 'thresholds.json')
DB_PATH = os.path.join(os.getcwd(), 'articles.db')
RESPONSES_DIR = os.path.join(os.getcwd(), 'responses')


def ensure_responses_dir():
    os.makedirs(RESPONSES_DIR, exist_ok=True)


def get_unprocessed_by_source(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, source FROM articles WHERE deepseek_processed = 0 AND (deepseek_failed IS NULL OR deepseek_failed < 4)")
    rows = cur.fetchall()
    by_source = {}
    for row in rows:
        aid, src = row[0], row[1]
        by_source.setdefault(src or 'unknown', []).append(aid)
    return by_source


def claim_article(conn, article_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE articles SET deepseek_in_progress = 1 WHERE id = ? AND (deepseek_in_progress IS NULL OR deepseek_in_progress = 0)",
        (article_id,)
    )
    conn.commit()
    return cur.rowcount == 1


def release_claim(conn, article_id):
    cur = conn.cursor()
    cur.execute("UPDATE articles SET deepseek_in_progress = 0 WHERE id = ?", (article_id,))
    conn.commit()


def fetch_article_row(conn, article_id):
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, content, category_id FROM articles WHERE id = ?", (article_id,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'content': row[3],
        'category_id': row[4]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Run API calls and inserter')
    args = parser.parse_args()

    # Load thresholds
    if not os.path.exists(THRESHOLDS_PATH):
        print(f"Missing thresholds file: {THRESHOLDS_PATH}")
        sys.exit(1)
    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)

    sample_rate = int(thresholds.get('sample_rate', 10))
    seed = int(thresholds.get('random_seed', 42)) if 'random_seed' in thresholds else 42

    ensure_responses_dir()

    rng = random.Random(seed)

    conn = sqlite3.connect(DB_PATH)
    try:
        by_source = get_unprocessed_by_source(conn)
        print(f"Found {len(by_source)} sources with unprocessed articles")

        to_process = []
        for src, ids in by_source.items():
            selected = [aid for aid in ids if rng.randrange(sample_rate) == 0]
            if selected:
                print(f"Source '{src}': selected {len(selected)} of {len(ids)} articles")
                to_process.extend(selected)

        print(f"Total articles selected: {len(to_process)}")

        # Only import networked function when running with --apply
        process_with_api = None
        if args.apply:
            if not os.environ.get('DEEPSEEK_API_KEY'):
                print("ERROR: DEEPSEEK_API_KEY not set. Set it with: export DEEPSEEK_API_KEY=your_key_here")
                sys.exit(1)
            import process_one_article
            process_with_api = process_one_article.process_article_with_api

        for article_id in to_process:
            print(f"\n--- Processing article {article_id} ---")
            if not claim_article(conn, article_id):
                print(f"Could not claim article {article_id} (already in progress). Skipping.")
                continue

            article = fetch_article_row(conn, article_id)
            if not article:
                print(f"Article {article_id} disappeared. Releasing claim.")
                release_claim(conn, article_id)
                continue

            if args.apply and process_with_api:
                response = process_with_api(article, process_one_article.COMPACT_PROMPTS['default'])
                if response is None:
                    print(f"Processing failed for {article_id}. Incrementing failure counter and releasing claim")
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE articles SET deepseek_failed = COALESCE(deepseek_failed,0)+1, deepseek_last_error = ?, deepseek_in_progress = 0 WHERE id = ?",
                        ("process_failed", article_id)
                    )
                    conn.commit()
                    # delete if too many failures
                    cur.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
                    r = cur.fetchone()
                    failed_count = r[0] if r else 0
                    if failed_count and failed_count > 3:
                        print(f"deepseek_failed > 3 for article {article_id}; deleting article")
                        cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                        conn.commit()
                    continue

                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{article_id}_{ts}.json'
                fpath = os.path.join(RESPONSES_DIR, fname)
                with open(fpath, 'w') as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)
                print(f"Saved preview to {fpath}")

                # Run canonical inserter as subprocess to isolate DB changes
                ret = os.system(f'python3 insert_from_response.py "{fpath}"')
                if ret != 0:
                    print(f"Inserter returned non-zero status for {article_id}: {ret}; releasing claim")
                    release_claim(conn, article_id)
                else:
                    print(f"Inserter succeeded for {article_id}")
            else:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{article_id}_{ts}.json'
                fpath = os.path.join(RESPONSES_DIR, fname)
                preview = {'meta': {'article_id': article_id, 'title': article.get('title'), 'dry_run': True, 'selected_at': ts}}
                with open(fpath, 'w') as f:
                    json.dump(preview, f, ensure_ascii=False, indent=2)
                print(f"Dry-run saved preview placeholder to {fpath}")
                # clear claim so it can be processed later
                release_claim(conn, article_id)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
run_mining_round.py

Select 1-in-N unprocessed articles per source, save previews, and optionally insert.

Usage:
  python3 run_mining_round.py        # dry-run: save preview placeholders
  python3 run_mining_round.py --apply  # call Deepseek API and run inserter
"""

import os
import sys
import json
import sqlite3
import random
from datetime import datetime
import argparse

THRESHOLDS_PATH = os.path.join(os.getcwd(), 'config', 'thresholds.json')
DB_PATH = os.path.join(os.getcwd(), 'articles.db')
RESPONSES_DIR = os.path.join(os.getcwd(), 'responses')


def ensure_responses_dir():
    os.makedirs(RESPONSES_DIR, exist_ok=True)


def get_unprocessed_by_source(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, source FROM articles WHERE deepseek_processed = 0 AND (deepseek_failed IS NULL OR deepseek_failed < 4)")
    rows = cur.fetchall()
    by_source = {}
    for row in rows:
        aid, src = row[0], row[1]
        by_source.setdefault(src or 'unknown', []).append(aid)
    return by_source


def claim_article(conn, article_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE articles SET deepseek_in_progress = 1 WHERE id = ? AND (deepseek_in_progress IS NULL OR deepseek_in_progress = 0)",
        (article_id,)
    )
    conn.commit()
    return cur.rowcount == 1


def release_claim(conn, article_id):
    cur = conn.cursor()
    cur.execute("UPDATE articles SET deepseek_in_progress = 0 WHERE id = ?", (article_id,))
    conn.commit()


def fetch_article_row(conn, article_id):
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, content, category_id FROM articles WHERE id = ?", (article_id,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        'id': row[0],
        'title': row[1],
        'description': row[2],
        'content': row[3],
        'category_id': row[4]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Run API calls and inserter')
    args = parser.parse_args()

    # Load thresholds
    if not os.path.exists(THRESHOLDS_PATH):
        print(f"Missing thresholds file: {THRESHOLDS_PATH}")
        sys.exit(1)
    with open(THRESHOLDS_PATH) as f:
        thresholds = json.load(f)

    sample_rate = int(thresholds.get('sample_rate', 10))
    seed = int(thresholds.get('random_seed', 42)) if 'random_seed' in thresholds else 42

    ensure_responses_dir()

    rng = random.Random(seed)

    conn = sqlite3.connect(DB_PATH)
    try:
        by_source = get_unprocessed_by_source(conn)
        print(f"Found {len(by_source)} sources with unprocessed articles")

        to_process = []
        for src, ids in by_source.items():
            selected = [aid for aid in ids if rng.randrange(sample_rate) == 0]
            if selected:
                print(f"Source '{src}': selected {len(selected)} of {len(ids)} articles")
                to_process.extend(selected)

        print(f"Total articles selected: {len(to_process)}")

        # Only import networked function when running with --apply
        process_with_api = None
        if args.apply:
            if not os.environ.get('DEEPSEEK_API_KEY'):
                print("ERROR: DEEPSEEK_API_KEY not set. Set it with: export DEEPSEEK_API_KEY=your_key_here")
                sys.exit(1)
            import process_one_article
            process_with_api = process_one_article.process_article_with_api

        for article_id in to_process:
            print(f"\n--- Processing article {article_id} ---")
            if not claim_article(conn, article_id):
                print(f"Could not claim article {article_id} (already in progress). Skipping.")
                continue

            article = fetch_article_row(conn, article_id)
            if not article:
                print(f"Article {article_id} disappeared. Releasing claim.")
                release_claim(conn, article_id)
                continue

            if args.apply and process_with_api:
                response = process_with_api(article, process_one_article.COMPACT_PROMPTS['default'])
                if response is None:
                    print(f"Processing failed for {article_id}. Incrementing failure counter and releasing claim")
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE articles SET deepseek_failed = COALESCE(deepseek_failed,0)+1, deepseek_last_error = ?, deepseek_in_progress = 0 WHERE id = ?",
                        ("process_failed", article_id)
                    )
                    conn.commit()
                    # delete if too many failures
                    cur.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
                    r = cur.fetchone()
                    failed_count = r[0] if r else 0
                    if failed_count and failed_count > 3:
                        print(f"deepseek_failed > 3 for article {article_id}; deleting article")
                        cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                        conn.commit()
                    continue

                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{article_id}_{ts}.json'
                fpath = os.path.join(RESPONSES_DIR, fname)
                with open(fpath, 'w') as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)
                print(f"Saved preview to {fpath}")

                # Run canonical inserter as subprocess to isolate DB changes
                ret = os.system(f'python3 insert_from_response.py "{fpath}"')
                if ret != 0:
                    print(f"Inserter returned non-zero status for {article_id}: {ret}; releasing claim")
                    release_claim(conn, article_id)
                else:
                    print(f"Inserter succeeded for {article_id}")
            else:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = f'response_article_{article_id}_{ts}.json'
                fpath = os.path.join(RESPONSES_DIR, fname)
                preview = {'meta': {'article_id': article_id, 'title': article.get('title'), 'dry_run': True, 'selected_at': ts}}
                with open(fpath, 'w') as f:
                    json.dump(preview, f, ensure_ascii=False, indent=2)
                print(f"Dry-run saved preview placeholder to {fpath}")
                # clear claim so it can be processed later
                release_claim(conn, article_id)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
            args = parser.parse_args()

            # Load thresholds
            if not os.path.exists(THRESHOLDS_PATH):
                print(f"Missing thresholds file: {THRESHOLDS_PATH}")
                sys.exit(1)
            with open(THRESHOLDS_PATH) as f:
                thresholds = json.load(f)

            sample_rate = int(thresholds.get('sample_rate', 10))
            seed = int(thresholds.get('random_seed', 42)) if 'random_seed' in thresholds else 42

            ensure_responses_dir()

            rng = random.Random(seed)

            conn = sqlite3.connect(DB_PATH)
            try:
                by_source = get_unprocessed_by_source(conn)
                print(f"Found {len(by_source)} sources with unprocessed articles")

                to_process = []
                for src, ids in by_source.items():
                    selected = [aid for aid in ids if rng.randrange(sample_rate) == 0]
                    if selected:
                        print(f"Source '{src}': selected {len(selected)} of {len(ids)} articles")
                        to_process.extend(selected)

                print(f"Total articles selected: {len(to_process)}")

                # Only import the networked function when needed
                process_with_api = None
                if args.apply:
                    if not os.environ.get('DEEPSEEK_API_KEY'):
                        print("ERROR: DEEPSEEK_API_KEY not set. Set it with: export DEEPSEEK_API_KEY=your_key_here")
                        sys.exit(1)
                    import process_one_article
                    process_with_api = process_one_article.process_article_with_api

                for article_id in to_process:
                    print(f"\n--- Processing article {article_id} ---")
                    if not claim_article(conn, article_id):
                        print(f"Could not claim article {article_id} (already in progress). Skipping.")
                        continue

                    article = fetch_article_row(conn, article_id)
                    if not article:
                        print(f"Article {article_id} disappeared. Releasing claim.")
                        release_claim(conn, article_id)
                        continue

                    if args.apply and process_with_api:
                        response = process_with_api(article, process_one_article.COMPACT_PROMPTS['default'])
                        if response is None:
                            print(f"Processing failed for {article_id}. Incrementing failure counter and releasing claim")
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE articles SET deepseek_failed = COALESCE(deepseek_failed,0)+1, deepseek_last_error = ?, deepseek_in_progress = 0 WHERE id = ?",
                                ("process_failed", article_id)
                            )
                            conn.commit()
                            # delete if too many failures
                            cur.execute("SELECT deepseek_failed FROM articles WHERE id = ?", (article_id,))
                            r = cur.fetchone()
                            failed_count = r[0] if r else 0
                            if failed_count and failed_count > 3:
                                print(f"deepseek_failed > 3 for article {article_id}; deleting article")
                                cur.execute("DELETE FROM articles WHERE id = ?", (article_id,))
                                conn.commit()
                            continue

                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        fname = f'response_article_{article_id}_{ts}.json'
                        fpath = os.path.join(RESPONSES_DIR, fname)
                        with open(fpath, 'w') as f:
                            json.dump(response, f, ensure_ascii=False, indent=2)
                        print(f"Saved preview to {fpath}")

                        # Run canonical inserter as subprocess to isolate DB changes
                        ret = os.system(f'python3 insert_from_response.py "{fpath}"')
                        if ret != 0:
                            print(f"Inserter returned non-zero status for {article_id}: {ret}; releasing claim")
                            release_claim(conn, article_id)
                        else:
                            print(f"Inserter succeeded for {article_id}")
                    else:
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        fname = f'response_article_{article_id}_{ts}.json'
                        fpath = os.path.join(RESPONSES_DIR, fname)
                        preview = {'meta': {'article_id': article_id, 'title': article.get('title'), 'dry_run': True, 'selected_at': ts}}
                        with open(fpath, 'w') as f:
                            json.dump(preview, f, ensure_ascii=False, indent=2)
                        print(f"Dry-run saved preview placeholder to {fpath}")
                        # clear claim so it can be processed later
                        release_claim(conn, article_id)

            finally:
                conn.close()


        if __name__ == '__main__':
            main()
