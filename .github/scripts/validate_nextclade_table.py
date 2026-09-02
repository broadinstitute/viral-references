#!/usr/bin/env python3
"""
Validate the nextclade-by-taxid lookup table.

Three checks:
  1. TSV structure (offline).
  2. Every nextclade_dataset name resolves against the upstream Nextclade dataset
     index. The index is fetched ONCE per run, not once per row.
  3. No row is shadowed by an earlier, more general row. Requires NCBI Taxonomy;
     this check is advisory -- if NCBI is unreachable it is skipped with a warning
     and the exit status is unaffected. A shadowed row that the check actually
     finds is a hard failure.

All failures are collected and reported together, so one run shows the full picture.
"""

import csv
import os
import sys
import time
import xml.etree.ElementTree as ET

import requests

NEXTCLADE_INDEX_URL = 'https://data.clades.nextstrain.org/v3/index.json'
NCBI_EFETCH_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
EXPECTED_HEADER = ['tax_id', 'nextclade_dataset']
RETRIES = 3


def warn(msg):
    print(msg, file=sys.stderr, flush=True)


def fetch_with_retries(description, do_request):
    """Run do_request() up to RETRIES times with backoff. Returns the response or raises."""
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            response = do_request()
            response.raise_for_status()
            return response
        except Exception as err:  # noqa: BLE001 - any transport/HTTP problem is retryable
            last_err = err
            warn(f'  {description}: attempt {attempt}/{RETRIES} failed: {err}')
            if attempt < RETRIES:
                time.sleep(2 * attempt)
    raise RuntimeError(f'{description} failed after {RETRIES} attempts: {last_err}')


# --------------------------------------------------------------------------
# check 1: structure
# --------------------------------------------------------------------------

def check_structure(tsv_file):
    """Parse and structurally validate the TSV. Returns (rows, errors).

    rows is a list of (line_number, tax_id_str, dataset_name).
    """
    errors = []
    rows = []

    with open(tsv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        try:
            header = next(reader)
        except StopIteration:
            return [], ['[check 1] file is empty']

        if header != EXPECTED_HEADER:
            errors.append(
                f'[check 1] line 1: header is {header}, expected {EXPECTED_HEADER}')

        for line_num, fields in enumerate(reader, start=2):
            if all(cell.strip() == '' for cell in fields):
                continue

            if len(fields) != len(EXPECTED_HEADER):
                errors.append(
                    f'[check 1] line {line_num}: has {len(fields)} fields, '
                    f'expected {len(EXPECTED_HEADER)} (tabs, not spaces?): {fields}')
                continue

            tax_id, dataset = (field.strip() for field in fields)

            if not tax_id:
                errors.append(f'[check 1] line {line_num}: empty tax_id')
                continue
            try:
                int(tax_id)
            except ValueError:
                errors.append(
                    f'[check 1] line {line_num}: tax_id {tax_id!r} is not an integer')
                continue

            if not dataset:
                errors.append(
                    f'[check 1] line {line_num}: empty nextclade_dataset for tax_id {tax_id}')
                continue

            rows.append((line_num, tax_id, dataset))

    seen = {}
    for line_num, tax_id, _ in rows:
        if tax_id in seen:
            errors.append(
                f'[check 1] line {line_num}: duplicate tax_id {tax_id} '
                f'(first seen on line {seen[tax_id]})')
        else:
            seen[tax_id] = line_num

    print(f'[check 1] structure: {len(rows)} data rows, {len(errors)} problem(s)')
    return rows, errors


# --------------------------------------------------------------------------
# check 2: dataset names resolve upstream
# --------------------------------------------------------------------------

def check_dataset_names(rows):
    """Verify every dataset name is a known upstream path or shortcut."""
    response = fetch_with_retries(
        'nextclade index',
        lambda: requests.get(NEXTCLADE_INDEX_URL, timeout=60))
    index = response.json()

    known = set()
    n_datasets = 0
    for collection in index.get('collections', []):
        for dataset in collection.get('datasets', []):
            n_datasets += 1
            known.add(dataset['path'])
            known.update(dataset.get('shortcuts', []))

    if not n_datasets:
        raise RuntimeError('nextclade index contained no datasets')

    errors = []
    for line_num, tax_id, dataset in rows:
        if dataset not in known:
            errors.append(
                f'[check 2] line {line_num}: dataset {dataset!r} (tax_id {tax_id}) '
                f'is not a known upstream dataset path or shortcut')

    print(f'[check 2] dataset names: checked {len(rows)} rows against '
          f'{n_datasets} upstream datasets ({len(known)} names/shortcuts), '
          f'{len(errors)} unresolvable')
    return errors


# --------------------------------------------------------------------------
# check 3: ordering / shadowing (advisory)
# --------------------------------------------------------------------------

def fetch_lineages(tax_ids):
    """Return {tax_id: set(ancestor tax_ids)} from NCBI. Raises on network/parse trouble."""
    response = fetch_with_retries(
        'NCBI efetch',
        lambda: requests.post(
            NCBI_EFETCH_URL,
            data={
                'db': 'taxonomy',
                'id': ','.join(tax_ids),
                'retmode': 'xml',
                # identify the caller per NCBI guidance; deliberately no email address
                'tool': 'viral-references-ci',
            },
            timeout=60))

    root = ET.fromstring(response.content)
    lineages = {}
    for taxon in root.findall('Taxon'):
        ancestors = {
            node.findtext('TaxId')
            for node in taxon.findall('./LineageEx/Taxon')
        }
        ancestors.discard(None)
        ids = {taxon.findtext('TaxId')}
        # a taxid merged into another still needs to answer to the id we asked for
        ids.update(node.text for node in taxon.findall('./AkaTaxIds/TaxId'))
        for tax_id in ids:
            if tax_id:
                lineages[tax_id] = ancestors

    if not lineages:
        raise RuntimeError('NCBI returned no taxonomy records')
    return lineages


def check_ordering(rows):
    """Verify no row is shadowed by an earlier ancestor row.

    Returns (ran, errors). Only the fetch/parse is guarded -- once we have data,
    a shadowed row is a hard failure.
    """
    tax_ids = [tax_id for _, tax_id, _ in rows]
    try:
        lineages = fetch_lineages(tax_ids)
    except Exception as err:  # noqa: BLE001 - network trouble must not fail the build
        warn(f'[check 3] SKIPPED - NCBI taxonomy unavailable ({err}); '
             f'row ordering NOT verified')
        return False, []

    errors = []
    missing = [tax_id for tax_id in tax_ids if tax_id not in lineages]
    for tax_id in missing:
        line_num = next(ln for ln, tid, _ in rows if tid == tax_id)
        errors.append(
            f'[check 3] line {line_num}: tax_id {tax_id} is not recognised by NCBI Taxonomy')

    for i, (line_num, tax_id, dataset) in enumerate(rows):
        ancestors = lineages.get(tax_id)
        if ancestors is None:
            continue
        for earlier_line, earlier_tax_id, earlier_dataset in rows[:i]:
            if earlier_tax_id in ancestors:
                errors.append(
                    f'[check 3] line {line_num}: tax_id {tax_id} ({dataset!r}) can never '
                    f'match -- it is a descendant of tax_id {earlier_tax_id} '
                    f'({earlier_dataset!r}) on line {earlier_line}, which takes precedence. '
                    f'Move the more specific row earlier.')

    resolved = len(tax_ids) - len(missing)
    warn(f'[check 3] ran - {resolved}/{len(tax_ids)} taxids resolved, '
         f'{len(errors)} problem(s) found')
    return True, errors


# --------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print('Usage: python validate_nextclade_table.py <tsv_file>', file=sys.stderr)
        return 2

    tsv_file = sys.argv[1]
    if not os.path.exists(tsv_file):
        print(f'File not found: {tsv_file}', file=sys.stderr)
        return 2

    print(f'Validating nextclade table: {tsv_file}')

    rows, errors = check_structure(tsv_file)
    if errors:
        # the later checks assume well-formed rows; report what we have and stop
        print('\nVALIDATION FAILED:')
        for error in errors:
            print(f'  {error}')
        return 1

    errors += check_dataset_names(rows)

    ordering_ran, ordering_errors = check_ordering(rows)
    errors += ordering_errors

    ordering_note = ('check 3 (row ordering) ran' if ordering_ran
                     else 'check 3 (row ordering) was SKIPPED - NCBI unavailable')
    print(f'\nSummary: {len(rows)} rows checked; {ordering_note}.')

    if errors:
        print('\nVALIDATION FAILED:')
        for error in errors:
            print(f'  {error}')
        return 1

    print('All nextclade table validations passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
