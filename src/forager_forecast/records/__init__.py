"""GBIF occurrence records: requesting, loading, filtering and counting them.

- gbif_download: the T1 predicate, the DWCA download request (D45, D67) and its submission.
- occurrence: the one Record type and the loader that builds it from a DWCA occurrence.txt row,
  counting the rows it cannot type (D42, D66).
- filters: the one filter pipeline, with T1's step list and the R6 audit's, every step counted
  (D32, D65).
- counts and licenses: the count tables by stage, group, region and year, and by licence and
  publisher.
- sampler: the seeded 200-record hand-check sample and its CSV (T2).
- t1_record and t1_simple_csv: not part of the pipeline. Kept unchanged as the evidence of T1's
  provisional SIMPLE_CSV run (D67).

Source records are never modified: every function here reads a row or a Record and returns a
verdict, a count or a new object.
"""
