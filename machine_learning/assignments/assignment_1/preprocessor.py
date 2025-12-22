def encode_categorical(rows, col_idx, mapping=None):
    """Encode a column with categorical strings into integers using provided mapping or Yes/No mapping.
    Returns new rows and mapping used.
    """
    if mapping is None:
        mapping = {}
        next_id = 0
        for r in rows:
            val = r[col_idx]
            if val not in mapping:
                mapping[val] = next_id
                next_id += 1
    new_rows = []
    for r in rows:
        nr = list(r)
        nr[col_idx] = mapping[nr[col_idx]]
        new_rows.append(nr)
    return new_rows, mapping

def compute_min_max(rows, col_idx):
    mn = None
    mx = None
    for r in rows:
        v = float(r[col_idx])
        if mn is None or v < mn:
            mn = v
        if mx is None or v > mx:
            mx = v
    return mn, mx


def compute_mean_std(rows, col_idx):
    n = 0
    s = 0.0
    for r in rows:
        n += 1
        s += float(r[col_idx])
    mean = s / n if n else 0.0
    ss = 0.0
    for r in rows:
        d = float(r[col_idx]) - mean
        ss += d * d
    variance = ss / n if n else 0.0
    std = variance ** 0.5
    return mean, std


def min_max_scale_rows(rows, col_idx, mn=None, mx=None):
    if mn is None or mx is None:
        mn, mx = compute_min_max(rows, col_idx)
    new = []
    rng = mx - mn if (mx is not None and mn is not None) else 0.0
    for r in rows:
        nr = list(r)
        try:
            v = float(nr[col_idx])
        except Exception:
            v = 0.0
        if rng == 0:
            nr[col_idx] = 0.0
        else:
            nr[col_idx] = (v - mn) / rng
        new.append(nr)
    return new, (mn, mx)


def z_score_scale_rows(rows, col_idx, mean=None, std=None):
    if mean is None or std is None:
        mean, std = compute_mean_std(rows, col_idx)
    new = []
    for r in rows:
        nr = list(r)
        try:
            v = float(nr[col_idx])
        except Exception:
            v = 0.0
        if std == 0:
            nr[col_idx] = 0.0
        else:
            nr[col_idx] = (v - mean) / std
        new.append(nr)
    return new, (mean, std)


def add_bias_column(rows, at_front=True):
    new = []
    for r in rows:
        nr = list(r)
        if at_front:
            nr = [1.0] + nr
        else:
            nr = nr + [1.0]
        new.append(nr)
    return new


def rows_to_features_targets(rows, feature_cols, target_col):
    X = []
    y = []
    for r in rows:
        xv = []
        for c in feature_cols:
            xv.append(float(r[c]))
        X.append(xv)
        y.append(float(r[target_col]))
    return X, y

