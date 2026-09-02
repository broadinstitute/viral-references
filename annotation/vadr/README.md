# File structure

This table is meant to allow pipelines to programmatically determine
whether or not they can run VADR on their taxon and also how to run VADR
on their taxon.

## Rows

Although this table is intended to be a lookup table based on the first
column (the NCBI tax ID), it is also intended to be an *ordered* table.
Specifically: earlier rows take precedence over later rows. If your taxon
of interest is equal to or taxonomically below (more specific) than the ID
in column 1, you can use the information in that row to run VADR--however,
if your taxon of interest matches more than one row, use the earliest match.
In other words: when adding new rows to this table, if your new taxid
falls under or over any existing rows, put the most specific taxid earlier
in the table. Examples currently in this data include Dengue before
Flaviviridae, Norovirus before Caliciviridae, and SARS-CoV-2 and the
four seasonal HCoV species before Coronaviridae.

## Columns

The columns in the table are:

1. NCBI Tax ID -- any taxon at or below (more specific) than this taxid can use these parameters to run VADR.
2. NCBI Taxon Name -- this isn't meant to be consumed downstream, just to keep the file human readable / maintainable.
3. min_seq_len (optional) -- use as the `--minlen` parameter to `fasta-trim-terminal-ambigs.pl`
4. max_seq_len (optional) -- use as the `--maxlen` parameter to `fasta-trim-terminal-ambigs.pl`
5. VADR minimum RAM (GB) (optional) -- for cloud or HPC setups where memory consumption must be specified, this is the estimated minimum RAM required by VADR when utilizing these models, if known.
6. VADR CLI options -- these are command line parameters to pass to VADR. Do not include `--split`, `--cpu`, or `--mdir` options here, as that will be handled by pipeline/script code downstream.
7. VADR model tar URL -- this is a URL to download a `.tar.gz` file containing the VADR model. The tar file must contain *one* top level subdirectory with all files underneath that subdirectory.
8. VADR model subdirectory (optional) -- if the tar file has one additional subdirectory layer below the first subdirectory, name it here.
