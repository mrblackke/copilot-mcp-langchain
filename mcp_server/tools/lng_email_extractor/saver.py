"""
Saving module for serializing and writing extracted emails to JSON.
"""
import json
import os

def save_emails_to_json(emails, output_dir, filename):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'emails': emails}, f, ensure_ascii=False, indent=2)
    return path
