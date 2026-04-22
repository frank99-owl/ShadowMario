import csv


def read_csv(filepath):
    """Read CSV rows as [entity_type, x, y] entries."""
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= 3:
                data.append([row[0].strip(), row[1].strip(), row[2].strip()])
    return data
