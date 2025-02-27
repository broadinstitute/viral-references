# File structure

This table is meant to allow pipelines to programmatically determine
whether or not they can run nextclade on their genome and which nextclade
dataset to use when doing so.

## Rows

Although this table is intended to be a lookup table based on the first
column (the NCBI tax ID), it is also intended to be an *ordered* table.
Specifically: earlier rows take precedence over later rows. If your taxon
of interest is equal to or taxonomically below (more specific) than the ID
in column 1, you can use the information in that row to run nextclade--however,
if your taxon of interest matches more than one row, use the earliest match.
In other words: when adding new rows to this table, if your new taxid
falls under or over any existing rows, put the most specific taxid earlier
in the table.

## Columns

The columns in the table are:

1. NCBI Tax ID -- any taxon at or below (more specific) than this taxid can use Nextclade.
2. Nextclade dataset name -- use this to run `nextclade dataset get --name=` to retrieve the correct dataset
