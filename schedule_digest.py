#!/usr/bin/env python3
"""Helper script to set up cron jobs for daily digest."""

import os
import pathlib
import subprocess
import sys


def get_current_crontab() -> list[str]:
    """Get current crontab entries."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        return []
    except Exception:
        return []


def add_to_crontab(entry: str) -> bool:
    """Add a new crontab entry."""
    try:
        current = get_current_crontab()
        if entry in current:
            print("✗ Entry already exists in crontab")
            return False

        current.append(entry)
        current_text = "\n".join(current) + "\n"

        result = subprocess.run(
            ["crontab", "-"],
            input=current_text,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print("✓ Added to crontab")
            return True
        else:
            print(f"✗ Failed to add to crontab: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def list_crontab() -> None:
    """List current crontab entries."""
    entries = get_current_crontab()
    if not entries:
        print("No crontab entries found")
        return

    print("\nCurrent crontab entries:")
    for idx, entry in enumerate(entries, 1):
        if entry.strip():
            print(f"{idx}. {entry}")


def main() -> None:
    """Main menu."""
    work_dir = pathlib.Path(__file__).parent

    print("\n" + "=" * 60)
    print("CRON JOB SCHEDULER - Daily News Digest")
    print("=" * 60)

    while True:
        print("\n1. Schedule digest generation at 9:00 AM daily")
        print("2. Schedule digest generation + email at 9:00 AM daily")
        print("3. View current crontab")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            entry = f"0 9 * * * cd {work_dir} && python3 generate_daily_digest.py >> digest.log 2>&1"
            add_to_crontab(entry)

        elif choice == "2":
            entry = f"0 9 * * * cd {work_dir} && python3 generate_daily_digest.py --send-email >> digest.log 2>&1"
            add_to_crontab(entry)

        elif choice == "3":
            list_crontab()

        elif choice == "4":
            print("\nGoodbye!")
            break

        else:
            print("✗ Invalid option")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
