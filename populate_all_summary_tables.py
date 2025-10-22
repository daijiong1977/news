#!/usr/bin/env python3
"""Migration helper (legacy): populate normalized tables from `deepseek_feedback`.

NOTE: `deepseek_feedback` is deprecated for runtime use. This script is retained
only as a migration helper. It exits with a message unless explicitly invoked for
migration purposes.
"""

import sys

def main():
    print("This script is migration-only. To run it, edit the file and remove this guard.")
    sys.exit(0)

if __name__ == '__main__':
    main()
