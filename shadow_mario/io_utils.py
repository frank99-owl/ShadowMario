import csv


def read_csv(filepath):
    """读取 CSV 文件，返回列表，每项为 [type, x, y]。"""
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= 3:
                data.append([row[0].strip(), row[1].strip(), row[2].strip()])
    return data
