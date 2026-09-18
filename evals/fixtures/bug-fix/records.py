def merge_records(existing, incoming):
    result = list(existing)
    seen = {record["id"] for record in existing}
    for record in incoming:
        if record["id"] not in seen:
            result.append(record)
    return result
