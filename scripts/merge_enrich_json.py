"""
Merge CSV fields into processed JSON by matching email.

Adds `full_name` and `linkedin` to each JSON object (matched by email).
Writes output to the same folder with suffix `_enriched.json`.

Usage:
  python scripts/merge_enrich_json.py --csv 1000-leads-2025-12-16.csv \
      --input data/processed_emails_rows_112_1000_20251220_094918-row112 - row1001.json

If paths contain spaces, wrap them in quotes when calling from PowerShell.
"""

import argparse
import csv
import json
from pathlib import Path


def normalize_email(e: str) -> str:
    return (e or "").strip().lower()


def load_csv_map(csv_path: Path) -> dict:
    """Return map email -> {full_name, linkedin}"""
    mapping = {}
    with csv_path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # normalize header keys for flexibility
        headers = {h.strip().lower(): h for h in reader.fieldnames or []}
        # detect useful headers explicitly
        has_full = 'full name' in headers
        has_first = 'first name' in headers
        has_last = 'last name' in headers
        email_keys = [k for k in headers.keys() if 'email' in k]
        linkedin_keys = [k for k in headers.keys() if 'linkedin' in k]

        for row in reader:
            # find email value
            email = ''
            for k in email_keys:
                email = row.get(headers[k], '')
                if email:
                    break
            if not email:
                continue

            # prefer Full name column, otherwise combine First + Last, otherwise fallback
            full_name = ''
            if has_full:
                full_name = row.get(headers['full name'], '')
            else:
                first = row.get(headers['first name'], '') if has_first else ''
                last = row.get(headers['last name'], '') if has_last else ''
                if first and last:
                    full_name = f"{first} {last}"
                elif first:
                    full_name = first
                elif last:
                    full_name = last
                else:
                    # fallback: try any header containing 'name'
                    for k in headers.keys():
                        if 'name' in k:
                            full_name = row.get(headers[k], '')
                            if full_name:
                                break

            linkedin = ''
            for k in linkedin_keys:
                linkedin = row.get(headers[k], '')
                if linkedin:
                    break

            mapping[normalize_email(email)] = {
                'full_name': full_name or '',
                'linkedin': linkedin or ''
            }
    return mapping


def enrich_json(input_json: Path, csv_map: dict, output_json: Path):
    with input_json.open('r', encoding='utf-8') as f:
        data = json.load(f)

    matched = 0
    for item in data:
        email = normalize_email(item.get('email', ''))
        info = csv_map.get(email)
        if info:
            item['full_name'] = info.get('full_name', '')
            item['linkedin'] = info.get('linkedin', '')
            matched += 1
        else:
            item['full_name'] = ''
            item['linkedin'] = ''

    with output_json.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return len(data), matched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, help='Path to leads CSV')
    parser.add_argument('--input', required=True, help='Path to processed JSON')
    parser.add_argument('--output', required=False, help='Output path (optional)')
    args = parser.parse_args()

    csv_path = Path(args.csv)
    input_json = Path(args.input)

    if not csv_path.exists():
        print(f'CSV not found: {csv_path}')
        return
    if not input_json.exists():
        print(f'Input JSON not found: {input_json}')
        return

    csv_map = load_csv_map(csv_path)
    print(f'Loaded {len(csv_map)} CSV entries')

    if args.output:
        output_json = Path(args.output)
    else:
        output_json = input_json.with_name(input_json.stem + '_enriched' + input_json.suffix)

    total, matched = enrich_json(input_json, csv_map, output_json)
    print(f'Wrote {total} records to {output_json} ({matched} matched by email)')


if __name__ == '__main__':
    main()
