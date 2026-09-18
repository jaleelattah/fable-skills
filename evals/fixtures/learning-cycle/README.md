# Order pricing

`pricing.quote(subtotal_cents)` returns the payable whole-cent amount for a
nonnegative integer subtotal. `policy.json` supplies the current minimum subtotal
and discount percentage. A subtotal **equal to or above** that minimum qualifies.
For a qualifying subtotal, multiply by the remaining percentage and round down
to whole cents. Smaller subtotals are unchanged. The JSON policy is authoritative
for numeric values; do not duplicate those values as constants in the code.

Run the existing checks with `python3 -B -m unittest discover -p 'test_*.py'`.
