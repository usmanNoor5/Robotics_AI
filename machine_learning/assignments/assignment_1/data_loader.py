def load_csv1(path, has_header=True):
    """Load CSV manually using open() and string splitting. Returns list of rows (each row: list of strings).
    Empty lines are ignored. Leading/trailing whitespace stripped.
    """
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0 and has_header:
                header = line.strip()  # keep if needed
                continue
            line = line.strip()
            if not line:
                continue
            cols = [c.strip() for c in line.split(',')]
            rows.append(cols)
    return rows



def load_data(filepath):
    data = []
    with open(filepath, 'r') as f:
        lines = f.readlines()

    headers = lines[0].strip().split(',')
    for line in lines[1:]:
        if line.strip() == '':
            continue
        parts = line.strip().split(',')
        data.append(parts)
    return headers, data

def strlist_to_numeric(rows, converters):
    """Convert list of string rows to numeric where possible.
    converters is a list of callables or None per column index.
    If converter fails, raises ValueError.
    Returns list of rows with converted values.
    """
    out = []

    for r in rows:
        newr = []
        for i, val in enumerate(r):
            conv = converters[i] if i < len(converters) else None
            if conv is None:
                newr.append(val)
            else:
                newr.append(conv(val))
        out.append(newr)
    return out


def train_val_test_split(rows, train_ratio=0.7, val_ratio=0.15, seed=None):
    """Split list of rows into train/val/test using indexing (no random.shuffle to keep deterministic unless seed provided).
    If seed is provided, we'll perform a simple seeded shuffle using a linear congruential generator.
    """
    n = len(rows)
    idxs = list(range(n))
    if seed is not None:
        # simple reproducible shuffle
        a, c, m = 1664525, 1013904223, 2**32
        r = seed
        for i in range(n-1, -1, -1):
            r = (a * r + c) % m
            j = r % (i+1)
            idxs[i], idxs[j] = idxs[j], idxs[i]
    # else keep order
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    train = [rows[i] for i in idxs[:train_end]]
    val = [rows[i] for i in idxs[train_end:val_end]]
    test = [rows[i] for i in idxs[val_end:]]
    return train, val, test
def preprocess_data(data):
    """
    Converts 'Yes'/'No' to 1/0 and all numeric strings to int or float.
    """
    processed = []
    for row in data:
        new_row = []
        for value in row:
            # Convert Yes/No
            if value == 'Yes':
                new_row.append(1)
            elif value == 'No':
                new_row.append(0)
            else:
                # Try to convert to int or float
                try:
                    if '.' in value:
                        new_row.append(float(value))
                    else:
                        new_row.append(int(value))
                except ValueError:
                    # Keep as string if conversion fails
                    new_row.append(value)
        processed.append(new_row)
    return processed

# def main():
#     header, data= load_data(filepath='Student_Performance.csv')
#     data = preprocess_data(data=data)
#     train, val,test =train_val_test_split(data)
#     # print(val)
#     # print(header)
#     # print(data)

# main()