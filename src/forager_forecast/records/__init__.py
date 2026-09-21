"""Record audit (T2, docs/dispatch/2026-09-18-t2-record-audit.md).

Four pieces, each its own module and none of them touching the network:

- gbif_download: the GBIF download predicate T2 shares with T1, and the request around it.
- filters: the R6 filter pipeline, applied to a stream of records with every step counted.
- counts: the T1 boxes, the two forager groups, and the count table by stage, group, region, year.
- sampler: the seeded 200-record hand-check sample and its CSV.

Source records are never modified: every function here reads a mapping and returns a verdict, a
count or a new object. The pipeline drops nothing from its input; it decides what flows on.
"""
