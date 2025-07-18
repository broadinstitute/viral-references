#!/usr/bin/env python3
"""
Validate VADR model files by downloading, unpacking, and checking for required files.
"""

import sys
import csv
import re
import os
import tempfile
import tarfile
import zipfile
import requests
from urllib.parse import urlparse

def extract_mkey_value(vadr_opts):
    """Extract the mkey value from vadr_opts string."""
    if not vadr_opts:
        return None
    
    # Look for --mkey followed by a value
    match = re.search(r'--mkey\s+(\S+)', vadr_opts)
    if match:
        return match.group(1)
    return None

def download_file(url, dest_path):
    """Download a file from URL to destination path."""
    print(f"Downloading: {url}")
    
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"Downloaded to: {dest_path}")

def extract_archive(archive_path, extract_dir):
    """Extract tar.gz or zip archive to directory."""
    print(f"Extracting: {archive_path}")
    
    if archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(extract_dir)
    elif archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")
    
    print(f"Extracted to: {extract_dir}")

def check_mkey_files(extract_dir, mkey_value, subdir=None):
    """Check if required mkey files exist in the extracted directory."""
    if not mkey_value:
        return  # No mkey specified, nothing to check
    
    # Find the first (and likely only) subdirectory of extract_dir
    subdirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
    if not subdirs:
        raise FileNotFoundError(f"No subdirectories found in extracted archive")
    
    # Start with the first subdirectory
    base_dir = os.path.join(extract_dir, subdirs[0])
    
    # If subdir is specified, go one level deeper
    if subdir:
        search_dir = os.path.join(base_dir, subdir)
        print(f"Checking for mkey files in: {search_dir}")
    else:
        search_dir = base_dir
        print(f"Checking for mkey files in: {search_dir}")
    
    for ext in ['.fa', '.minfo']:
        file_path = os.path.join(search_dir, mkey_value + ext)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing required file: {file_path}")
        print(f"Found required file: {file_path}")

def validate_vadr_models(tsv_file):
    """Validate VADR model files for each row in the TSV."""
    print(f"Validating VADR models: {tsv_file}")
    
    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row_num, row in enumerate(reader, start=2):
            # Skip empty rows
            if all(cell.strip() == '' for cell in row.values()):
                continue
            
            tax_id = row['tax_id'].strip()
            taxon_name = row.get('taxon_name', '').strip()
            vadr_opts = row['vadr_opts'].strip()
            tar_url = row['vadr_model_tar_url'].strip()
            tar_subdir = row.get('vadr_model_tar_subdir', '').strip()
            
            print(f"\n--- Validating row {row_num}: {tax_id} ({taxon_name}) ---")
            
            if not tar_url:
                raise ValueError(f"Empty tar_url for row {row_num}")
            
            # Extract mkey value
            mkey_value = extract_mkey_value(vadr_opts)
            if mkey_value:
                print(f"Found mkey value: {mkey_value}")
            else:
                print("No mkey value found in vadr_opts")
            
            # Create temporary directory for download and extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Determine file extension from URL
                parsed_url = urlparse(tar_url)
                archive_path = os.path.join(temp_dir, os.path.basename(parsed_url.path))
                
                # Download the file
                download_file(tar_url, archive_path)
                
                # Extract the archive
                extract_dir = os.path.join(temp_dir, 'extracted')
                os.makedirs(extract_dir)
                
                extract_archive(archive_path, extract_dir)
                
                # Check for required mkey files
                check_mkey_files(extract_dir, mkey_value, tar_subdir)
            
            # Temporary directory is automatically cleaned up here
            print(f"Row {row_num} validation passed")
    
    print("\nAll VADR model validations passed")

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_vadr_models.py <tsv_file>")
        sys.exit(1)
    
    tsv_file = sys.argv[1]
    if not os.path.exists(tsv_file):
        raise FileNotFoundError(f"File not found: {tsv_file}")
    
    validate_vadr_models(tsv_file)

if __name__ == "__main__":
    main()