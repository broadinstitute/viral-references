#!/usr/bin/env python3
"""
Validate assembly/reference_genomes.tsv structure.

This file has no header row and expects exactly 4 tab-separated columns:
1. tax_id (integer)
2. short_name (string, may be empty)
3. description (string)
4. accessions (colon-separated list of accession IDs)
"""

import sys
import csv
from pathlib import Path


def validate_reference_genomes_tsv(tsv_file: Path) -> bool:
    """
    Validate that the reference_genomes.tsv file has proper structure:
    - Tab-separated values (not spaces)
    - Exactly 4 columns in every row
    - tax_id is a valid integer
    - accessions field is not empty
    """
    EXPECTED_COLUMNS = 4
    errors = []

    print(f"Validating reference genomes TSV: {tsv_file}")

    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')

        for row_num, row in enumerate(reader, start=1):
            # Skip empty rows
            if not row or all(cell.strip() == '' for cell in row):
                continue

            # Check column count
            if len(row) != EXPECTED_COLUMNS:
                errors.append(
                    f"Line {row_num}: Expected {EXPECTED_COLUMNS} columns, found {len(row)}. "
                    f"This may indicate spaces were used instead of tabs."
                )
                # Show a preview of what was parsed
                if len(row) == 1 and '  ' in row[0]:
                    errors.append(
                        f"  Hint: Line appears to use spaces instead of tabs as delimiters."
                    )
                continue

            tax_id, short_name, description, accessions = row

            # Validate tax_id is an integer
            tax_id = tax_id.strip()
            if not tax_id:
                errors.append(f"Line {row_num}: tax_id (column 1) is empty")
            else:
                try:
                    int(tax_id)
                except ValueError:
                    errors.append(f"Line {row_num}: tax_id '{tax_id}' is not a valid integer")

            # Validate accessions is not empty
            accessions = accessions.strip()
            if not accessions:
                errors.append(f"Line {row_num}: accessions (column 4) is empty")

    if errors:
        print(f"\nERROR: Found {len(errors)} validation issue(s):\n")
        for error in errors:
            print(f"  {error}")
        return False

    print(f"Validation passed: All rows have {EXPECTED_COLUMNS} tab-separated columns")
    return True


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_reference_genomes_tsv.py <tsv_file>")
        sys.exit(1)

    tsv_file = Path(sys.argv[1])
    if not tsv_file.exists():
        print(f"ERROR: File not found: {tsv_file}")
        sys.exit(1)

    if not validate_reference_genomes_tsv(tsv_file):
        sys.exit(1)


if __name__ == "__main__":
    main()
