# Receipt migration

`python3 migrate.py` copies records from `source.json` into `receipts.json` in
the working directory. Records have unique string IDs in source, and an integer
amount. Existing receipt records must be preserved byte-for-value, including
records no longer present in source. Add each new ID once in source order.
Existing records win when an ID is already present. Repeating the command must
leave the same logical output, and a later source addition must be imported.

The previous run stopped after writing a receipt but before updating
`checkpoint.json`. Its `next_index` is only a progress hint, not proof that a
record is missing or present. Refresh it to source length after a successful run.
There is no concurrent writer. Do not reset or discard the existing output.
