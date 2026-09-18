import json
from pathlib import Path


def main():
    source = json.loads(Path("source.json").read_text())
    receipts = json.loads(Path("receipts.json").read_text())
    checkpoint = json.loads(Path("checkpoint.json").read_text())
    for row in source[checkpoint["next_index"]:]:
        receipts.append(row)
    Path("receipts.json").write_text(json.dumps(receipts) + "\n")
    Path("checkpoint.json").write_text(json.dumps({"next_index": len(source)}) + "\n")


if __name__ == "__main__":
    main()
