#!/usr/bin/env python3
"""
Validate TSV file structure and format.
"""

import sys
import csv
from pathlib import Path

def validate_tsv_structure(tsv_file):
    """
    Validate that the TSV file has consistent structure:
    - Tab-separated values
    - Same number of columns in every row
    - Required columns exist: tax_id, vadr_opts, vadr_model_tar_url, vadr_model_tar_subdir
    """
    required_columns = ['tax_id', 'vadr_opts', 'vadr_model_tar_url', 'vadr_model_tar_subdir']
    
    print(f"Validating TSV structure: {tsv_file}")
    
    with open(tsv_file, 'r', encoding='utf-8') as f:
        # Read as TSV
        reader = csv.reader(f, delimiter='\t')
        
        # Check header
        headers = next(reader)
        print(f"Found headers: {headers}")
        
        # Check for duplicates
        if len(headers) != len(set(headers)):
            print(f"ERROR: Duplicate column headers found")
            return False
        
        # Check required columns exist
        missing_columns = []
        for col in required_columns:
            if col not in headers:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return False
        
        expected_columns = len(headers)
        print(f"Expected {expected_columns} columns per row")
        
        # Get column indices for required fields
        tax_id_idx = headers.index('tax_id')
        url_idx = headers.index('vadr_model_tar_url')
        
        # Check each row
        for row_num, row in enumerate(reader, start=2):  # Start at 2 since header is row 1
            if len(row) != expected_columns:
                print(f"ERROR: Row {row_num} has {len(row)} columns, expected {expected_columns}")
                print(f"Row content: {row}")
                return False
            
            # Check if this is an empty row (last row might be empty)
            if all(cell.strip() == '' for cell in row):
                print(f"INFO: Skipping empty row {row_num}")
                continue
                
            # Basic validation of required fields
            tax_id = row[tax_id_idx].strip()
            if not tax_id:
                print(f"ERROR: Row {row_num} has empty tax_id")
                return False
            
            # Validate tax_id is a valid integer
            try:
                int(tax_id)
            except ValueError:
                print(f"ERROR: Row {row_num} has invalid tax_id (not an integer): {tax_id}")
                return False
            
            if not row[url_idx].strip():  # vadr_model_tar_url
                print(f"ERROR: Row {row_num} has empty vadr_model_tar_url")
                return False
    
    print("TSV structure validation passed")
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_tsv_structure.py <tsv_file>")
        sys.exit(1)
    
    tsv_file = Path(sys.argv[1])
    if not tsv_file.exists():
        print(f"ERROR: File not found: {tsv_file}")
        sys.exit(1)
    
    if not validate_tsv_structure(tsv_file):
        sys.exit(1)

if __name__ == "__main__":
    main()