"""
Replace greeting first name in `generated_email` with `full_name` from enriched JSON.

Usage:
  python scripts/replace_firstname_with_fullname.py --input <enriched.json> [--output <out.json>]

The script looks for a greeting line like "Hi First," or "Hello First," immediately after the subject
and replaces the First token with the `full_name` field from each JSON object.
"""

import argparse
import json
import re
from pathlib import Path


def replace_greeting(complete_email: str, full_name: str) -> str:
    if not complete_email or not full_name:
        return complete_email

    # Pattern: capture Subject block then greeting 'Hi' or 'Hello' and the first-name token, preserving comma
    pattern = re.compile(r'^(Subject:.*?\n\n)(?P<greet>(Hi|Hello)\s+)(?P<first>[^,\n]+)(,)', flags=re.IGNORECASE | re.DOTALL)

    def _repl(m):
        prefix = m.group(1)
        greet = m.group('greet')
        return f"{prefix}{greet}{full_name},"

    new_email, n = pattern.subn(_repl, complete_email, count=1)
    if n > 0:
        return new_email

    # Fallback: look for greeting near start of email body (after two newlines)
    # Split header and body
    parts = complete_email.split('\n\n', 2)
    if len(parts) >= 2:
        header = parts[0]
        body = parts[1]
        # Replace first 'Hi First,' or 'Hello First,' at start of body
        body_new, n2 = re.subn(r'^(?P<greet>(Hi|Hello)\s+)(?P<first>[^,\n]+)(,)', lambda m: f"{m.group('greet')}{full_name},", body, count=1, flags=re.IGNORECASE)
        if n2 > 0:
            # Reconstruct
            if len(parts) == 2:
                return header + '\n\n' + body_new
            else:
                return header + '\n\n' + body_new + '\n\n' + parts[2]

    # No replacement made
    return complete_email


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to enriched JSON file')
    parser.add_argument('--output', help='Output path (optional)')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        return

    with input_path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    updated = 0
    total = 0
    for item in data:
        total += 1
        full_name = item.get('full_name') or item.get('name') or ''
        email = item.get('generated_email', '')
        if full_name and email:
            new_email = replace_greeting(email, full_name)
            if new_email != email:
                item['generated_email'] = new_email
                updated += 1

    # Write output
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = input_path.with_name(input_path.stem + '_fullname' + input_path.suffix)

    with out_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'Processed {total} records, updated {updated} greetings. Output: {out_path}')


if __name__ == '__main__':
    main()
