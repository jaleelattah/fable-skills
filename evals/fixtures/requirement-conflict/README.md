# Current credit behavior

The current implementation qualifies balances strictly above one minor currency
unit. Existing tests encode that behavior. The user's new requirement may differ.
Run tests without bytecode writes: `python3 -B -m unittest discover`.
