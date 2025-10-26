#!/usr/bin/env python3
"""
Update archive_available_dates.json based on existing payload directories.
This file is used by the main page to show which dates have archives available.
"""

import os
import json
import re
from pathlib import Path

def scan_payload_directories():
    """Scan website/main/ for payload directories and extract dates."""
    script_dir = Path(__file__).parent
    main_dir = script_dir.parent / 'website' / 'main'
    
    if not main_dir.exists():
        print(f"❌ Main directory not found: {main_dir}")
        return []
    
    # Pattern: payloads_YYYYMMDD_HHMMSS
    pattern = re.compile(r'^payloads_(\d{8})_(\d{6})$')
    
    dates_dict = {}  # {date: [list of timestamps]}
    
    for item in main_dir.iterdir():
        if item.is_dir():
            match = pattern.match(item.name)
            if match:
                date = match.group(1)
                timestamp = match.group(2)
                
                if date not in dates_dict:
                    dates_dict[date] = []
                dates_dict[date].append(timestamp)
    
    # Sort timestamps for each date to get the latest
    result = []
    for date in sorted(dates_dict.keys()):
        timestamps = sorted(dates_dict[date], reverse=True)
        latest_timestamp = timestamps[0]
        
        result.append({
            'date': date,
            'latest_timestamp': latest_timestamp,
            'directory': f'payloads_{date}_{latest_timestamp}',
            'count': len(timestamps)
        })
    
    return result

def write_archive_index(dates_data):
    """Write the archive index to website/main/archive_available_dates.json"""
    script_dir = Path(__file__).parent
    output_file = script_dir.parent / 'website' / 'main' / 'archive_available_dates.json'
    
    # Create output structure
    output = {
        'generated_at': __import__('datetime').datetime.now().isoformat(),
        'total_dates': len(dates_data),
        'dates': [d['date'] for d in dates_data],
        'details': dates_data
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Archive index written to: {output_file}")
    print(f"   Total dates with archives: {len(dates_data)}")
    
    return output_file

def main():
    print("🔍 Scanning for payload directories...")
    dates_data = scan_payload_directories()
    
    if not dates_data:
        print("⚠️  No payload directories found!")
        return
    
    print(f"\n📊 Found {len(dates_data)} dates with payloads:")
    for data in dates_data:
        print(f"   {data['date']} - {data['directory']} ({data['count']} version(s))")
    
    print("\n📝 Writing archive index...")
    output_file = write_archive_index(dates_data)
    
    print("\n✨ Done!")

if __name__ == '__main__':
    main()
