# viral-references
Reference genomes for viral genomics

## Accessing the Data

This repository is automatically deployed to Google Cloud Storage for public access.

### Latest Version (main branch)
```
gs://viral-references/main/assembly/reference_genomes.tsv
gs://viral-references/main/annotation/vadr/vadr-by-taxid.tsv
gs://viral-references/main/typing/nextclade-by-taxid.tsv
gs://viral-references/main/submission/table2asn-prohibited.tsv
```

### Versioned Releases
Pinned versions are available for reproducible workflows:
```
gs://viral-references/v1.0.0/assembly/reference_genomes.tsv
gs://viral-references/v1.1.0/assembly/reference_genomes.tsv
```

### Deployment
Data is automatically deployed via GitHub Actions:
- Every push to `main` updates `gs://viral-references/main/`
- Version tags (e.g., `v1.0.0`) create immutable snapshots at `gs://viral-references/v1.0.0/`
