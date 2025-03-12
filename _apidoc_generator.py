#!/usr/bin/env python3
"""
API Documentation Comment Extractor

Extracts apiDocJS comments from C++ source files, appends only new or modified
API versions to _apidoc.js, and updates the version in apidoc.json.
"""

import os
import re
import json
from pathlib import Path
import argparse
from collections import defaultdict
import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog="_apidoc_generator.py", description="Extract apiDocJS comments and update documentation files", epilog="For more information, see the apidoc documentation.")
    parser.add_argument('--src-dir', default='./src_versions', help='Source directory of the project')
    parser.add_argument('--apidoc-dir', default='.', help='Directory for apidoc files')
    parser.add_argument('--recursive', '-r', action='store_true', help='Search source files recursively')
    parser.add_argument('--output', default='_apidoc.js', help='Output file for version history')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    return parser.parse_args()

def normalize_comment(comment):
    """Normalize comment text for consistent comparison."""
    return '\n'.join(line.strip() for line in comment.splitlines()).strip()

def extract_api_comments(file_path):
    """Extract apiDocJS comments from a file."""
    api_comments = []
    current_comment = []
    in_comment = False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '/**' in line and not in_comment:
                in_comment = True
                current_comment = [line]
            elif '*/' in line and in_comment:
                current_comment.append(line)
                comment_text = ''.join(current_comment)
                if '@api ' in comment_text:
                    api_comments.append(normalize_comment(comment_text))
                current_comment = []
                in_comment = False
            elif in_comment:
                current_comment.append(line)
    
    return api_comments

def extract_api_details(comment):
    """Extract unique key and version from a comment block."""
    name_match = re.search(r'@apiName\s+([^\s]+)', comment)
    group_match = re.search(r'@apiGroup\s+([^\s]+)', comment)
    version_match = re.search(r'@apiVersion\s+([0-9.]+)', comment)
    
    name = name_match.group(1) if name_match else "Unnamed"
    group = group_match.group(1) if group_match else "Ungrouped"
    version = version_match.group(1) if version_match else None
    
    # Create a unique key based on name and group (not including version)
    unique_key = f"{name}__{group}"
    
    return unique_key, version

def get_current_api_info(api_comments):
    """Build a dictionary of current API versions and comments."""
    api_info = defaultdict(dict)
    for comment in api_comments:
        unique_key, version = extract_api_details(comment)
        if unique_key and version:
            api_info[unique_key][version] = comment
    return api_info

def load_existing_api_info(apidoc_js_path):
    """Load existing API versions and comments from _apidoc.js."""
    if not os.path.exists(apidoc_js_path):
        return {}
    
    existing_api_info = defaultdict(dict)
    with open(apidoc_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    comment_blocks = re.findall(r'/\*\*[\s\S]*?\*/', content)
    for comment in comment_blocks:
        normalized_comment = normalize_comment(comment)
        unique_key, version = extract_api_details(normalized_comment)
        if unique_key and version:
            existing_api_info[unique_key][version] = normalized_comment
    return existing_api_info

def generate_new_content(current_api_info, existing_api_info):
    """Generate new content for _apidoc.js based on current and existing API info."""
    merged_api_info = defaultdict(dict)
    
    # First, add all existing API info to merged info
    for unique_key, versions in existing_api_info.items():
        for version, comment in versions.items():
            merged_api_info[unique_key][version] = comment
    
    # Then, update or add current API info
    for unique_key, versions in current_api_info.items():
        for version, comment in versions.items():
            # If the same version exists, overwrite it
            merged_api_info[unique_key][version] = comment
    
    # Count changes
    updates = 0
    additions = 0
    
    for unique_key, versions in current_api_info.items():
        for version, comment in versions.items():
            if unique_key in existing_api_info and version in existing_api_info[unique_key]:
                if comment != existing_api_info[unique_key][version]:
                    updates += 1
            else:
                additions += 1
    
    # Sort all entries by key and version
    all_comments = []
    for unique_key in sorted(merged_api_info.keys()):
        for version in sorted(merged_api_info[unique_key].keys(), 
                             key=lambda v: tuple(map(int, v.split('.'))), 
                             reverse=True):  # Sort versions in descending order
            all_comments.append(merged_api_info[unique_key][version])
    
    return all_comments, updates, additions

def write_apidoc_js(apidoc_js_path, all_comments):
    """Write all comments to _apidoc.js."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"// API Documentation - Generated on {timestamp}\n\n"
    
    with open(apidoc_js_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for comment in all_comments:
            f.write(comment + "\n\n")

def update_apidoc_json(apidoc_dir, all_comments):
    """Update apidoc.json with the latest version from comments."""
    apidoc_json_path = Path(apidoc_dir) / 'apidoc.json'
    if not apidoc_json_path.exists():
        return
    
    latest_version = None
    versions = []
    
    for comment in all_comments:
        version_match = re.search(r'@apiVersion\s+([0-9.]+)', comment)
        if version_match:
            versions.append(version_match.group(1))
    
    if versions:
        latest_version = max(versions, key=lambda v: tuple(map(int, v.split('.'))))
    
    if latest_version:
        with open(apidoc_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data.get('version') != latest_version:
            data['version'] = latest_version
            with open(apidoc_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                f.write('\n')
            return True
    return False

def find_source_files(src_dir, recursive=False):
    """Find all C++ source files."""
    extensions = ['.cpp', '.c', '.h', '.hpp']
    source_files = []
    
    if recursive:
        for root, _, files in os.walk(src_dir):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    source_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(src_dir):
            if any(file.endswith(ext) for ext in extensions) and os.path.isfile(os.path.join(src_dir, file)):
                source_files.append(os.path.join(src_dir, file))
    
    return source_files

def main():
    """Main execution function."""
    args = parse_arguments()
    src_dir = Path(args.src_dir).resolve()
    apidoc_dir = Path(args.apidoc_dir).resolve()
    apidoc_js_path = apidoc_dir / args.output
    
    if not src_dir.exists():
        print(f"Error: Source directory {src_dir} not found.")
        return
    
    apidoc_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract comments from source files
    source_files = find_source_files(src_dir, args.recursive)
    all_api_comments = []
    for file_path in source_files:
        if args.verbose:
            print(f"Processing {file_path}")
        all_api_comments.extend(extract_api_comments(file_path))
    
    if not all_api_comments:
        print("No API comments found.")
        return
    
    # Process current and existing API info
    current_api_info = get_current_api_info(all_api_comments)
    existing_api_info = load_existing_api_info(apidoc_js_path)
    
    # Generate new content
    all_comments, updates, additions = generate_new_content(current_api_info, existing_api_info)
    
    # Write to _apidoc.js
    write_apidoc_js(apidoc_js_path, all_comments)
    
    # Update apidoc.json
    json_updated = update_apidoc_json(apidoc_dir, all_comments)
    
    # Print summary
    print(f"Updated {apidoc_js_path}:")
    print(f"  - {updates} API endpoints updated (same version with different content)")
    print(f"  - {additions} new API versions added")
    if json_updated:
        print("  - Updated version in apidoc.json")

if __name__ == "__main__":
    main()