# Record merge

`records.merge_records(existing, incoming)` returns a new list of dictionaries.
IDs are strings. Keep the first occurrence of each ID across existing records
followed by incoming records, preserve that encounter order and record contents,
and do not mutate either input. Existing input can also contain duplicate IDs.
Merging the same incoming batch again must not change the result.

Run tests: `python3 -B -m unittest discover`.
