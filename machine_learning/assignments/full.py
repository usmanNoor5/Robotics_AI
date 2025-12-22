# Student Performance Predictor (Pure Python, only matplotlib allowed)
# Project files concatenated in one script for easy copy-paste into separate modules.
# Files included (separate by header comments):
# data_loader.py
# preprocessor.py
# model.py
# evaluator.py
# predictor.py
# main.py

# ------------------------
# file: data_loader.py
# ------------------------

def load_csv(path, has_header=True):
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


# ------------------------
# file: preprocessor.py
# ------------------------

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


# ------------------------
# file: model.py
# ------------------------

# Basic linear algebra utilities implemented with loops

def transpose(mat):
    if not mat:
        return []
    r = len(mat)
    c = len(mat[0])
    out = [[0.0 for _ in range(r)] for _ in range(c)]
    for i in range(r):
        for j in range(c):
            out[j][i] = mat[i][j]
    return out


def matmul(A, B):
    # A: m x n, B: n x p => out m x p
    if not A or not B:
        return []
    m = len(A)
    n = len(A[0])
    n2 = len(B)
    p = len(B[0])
    if n != n2:
        raise ValueError('Incompatible shapes for multiplication')
    out = [[0.0 for _ in range(p)] for _ in range(m)]
    for i in range(m):
        for j in range(p):
            s = 0.0
            for k in range(n):
                s += A[i][k] * B[k][j]
            out[i][j] = s
    return out


def mat_vec_mul(A, v):
    # A: m x n, v: length n => returns length m
    if not A:
        return []
    m = len(A)
    n = len(A[0])
    if n != len(v):
        raise ValueError('Incompatible shapes for mat-vec')
    out = [0.0] * m
    for i in range(m):
        s = 0.0
        for j in range(n):
            s += A[i][j] * v[j]
        out[i] = s
    return out


def vec_sub(a, b):
    return [a[i] - b[i] for i in range(len(a))]

def vec_add(a, b):
    return [a[i] + b[i] for i in range(len(a))]

def scalar_vec_mul(s, v):
    return [s * vi for vi in v]


def dot(a, b):
    s = 0.0
    for i in range(len(a)):
        s += a[i] * b[i]
    return s


def identity_matrix(n):
    I = [[0.0]*n for _ in range(n)]
    for i in range(n):
        I[i][i] = 1.0
    return I


def augment_matrix(A, B):
    # A: n x n, B: n x m, returns n x (n+m)
    n = len(A)
    m = len(B[0])
    out = [list(A[i]) + list(B[i]) for i in range(n)]
    return out


def gauss_jordan_inverse(A):
    # Returns inverse of square matrix A using Gauss-Jordan elimination
    n = len(A)
    if n == 0:
        return []
    # build augmented [A | I]
    AM = [ [float(x) for x in row] + identity_row for row, identity_row in zip(A, identity_matrix(n)) ]
    # forward elimination
    for col in range(n):
        # find pivot
        pivot_row = None
        max_val = 0.0
        for r in range(col, n):
            v = abs(AM[r][col])
            if v > max_val:
                max_val = v
                pivot_row = r
        if pivot_row is None or max_val == 0.0:
            raise ValueError('Matrix is singular and cannot be inverted')
        # swap
        if pivot_row != col:
            AM[col], AM[pivot_row] = AM[pivot_row], AM[col]
        # normalize pivot row
        pivot = AM[col][col]
        for j in range(2*n):
            AM[col][j] /= pivot
        # eliminate other rows
        for r in range(n):
            if r == col:
                continue
            factor = AM[r][col]
            if factor == 0:
                continue
            for j in range(2*n):
                AM[r][j] -= factor * AM[col][j]
    # extract inverse
    inv = [row[n:] for row in AM]
    return inv


def normal_equation_weights(X, y, l2=0.0):
    # X: m x n, y: length m
    Xt = transpose(X)  # n x m
    XtX = matmul(Xt, X)  # n x n
    # add L2 regularization to diagonal
    if l2 != 0.0:
        for i in range(len(XtX)):
            XtX[i][i] += l2
    Xty = mat_vec_mul(Xt, y)  # length n
    # convert Xty to n x 1 matrix
    Xty_mat = [[v] for v in Xty]
    try:
        XtX_inv = gauss_jordan_inverse(XtX)
    except Exception as e:
        raise
    w_mat = matmul(XtX_inv, Xty_mat)  # n x 1
    w = [row[0] for row in w_mat]
    return w


def predict_with_weights(X, w):
    # X: m x n, w: length n
    preds = mat_vec_mul(X, w)
    return preds


def mse(y_true, y_pred):
    n = len(y_true)
    s = 0.0
    for i in range(n):
        d = y_true[i] - y_pred[i]
        s += d * d
    return s / n if n else 0.0


def r_squared(y_true, y_pred):
    n = len(y_true)
    mean = sum(y_true) / n if n else 0.0
    ss_tot = 0.0
    ss_res = 0.0
    for i in range(n):
        ss_tot += (y_true[i] - mean) ** 2
        ss_res += (y_true[i] - y_pred[i]) ** 2
    return 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0


def gradient_descent(X, y, lr=0.01, epochs=1000, l2=0.0, verbose=False):
    # X: m x n, y: length m
    m = len(X)
    n = len(X[0])
    # initialize weights to 0
    w = [0.0] * n
    history = []
    for epoch in range(epochs):
        preds = mat_vec_mul(X, w)
        # compute gradient: (1/m) * X^T (preds - y) + (l2/m)*w
        grad = [0.0] * n
        for j in range(n):
            s = 0.0
            for i in range(m):
                s += (preds[i] - y[i]) * X[i][j]
            grad[j] = (s / m) + (l2 / m) * w[j]
        # update weights
        for j in range(n):
            w[j] -= lr * grad[j]
        if epoch % max(1, epochs//20) == 0:
            current_mse = mse(y, mat_vec_mul(X, w))
            history.append((epoch, current_mse))
            if verbose:
                print('Epoch', epoch, 'MSE', current_mse)
    return w, history


# ------------------------
# file: evaluator.py
# ------------------------

import matplotlib
matplotlib.use('Agg')  # prevent interactive backend when used headless
import matplotlib.pyplot as plt


def plot_actual_vs_predicted(y_true, y_pred, fname='actual_vs_pred.png'):
    plt.figure()
    plt.scatter(list(range(len(y_true))), y_true, label='Actual')
    plt.scatter(list(range(len(y_pred))), y_pred, label='Predicted')
    plt.legend()
    plt.xlabel('Sample index')
    plt.ylabel('Target')
    plt.title('Actual vs Predicted')
    plt.savefig(fname)
    plt.close()


def plot_mse_history(history, fname='mse_history.png'):
    if not history:
        return
    epochs = [h[0] for h in history]
    mses = [h[1] for h in history]
    plt.figure()
    plt.plot(epochs, mses)
    plt.xlabel('Epoch')
    plt.ylabel('MSE')
    plt.title('MSE over training')
    plt.savefig(fname)
    plt.close()


def print_weights_interpretation(w, feature_names):
    print('Model weights and interpretation:')
    for i, wi in enumerate(w):
        fname = feature_names[i] if i < len(feature_names) else f'X{i}'
        print(f'  {fname}: {wi:.5f}')


# ------------------------
# file: predictor.py
# ------------------------

def predict_single(input_feats, preprocessors, w):
    """input_feats: list of raw features (matching original order)
    preprocessors: dict containing encoders/scalers and their parameters used in training
    w: trained weight vector for features including bias at front if used
    This function applies encoding and scaling in same order as training and returns prediction (float)
    """
    # copy
    x = list(input_feats)
    # encode categorical columns
    if 'encoders' in preprocessors:
        for col_idx, mapping in preprocessors['encoders'].items():
            val = x[col_idx]
            x[col_idx] = mapping.get(val, 0)
    # scaling
    if 'min_max' in preprocessors:
        for col_idx, (mn, mx) in preprocessors['min_max'].items():
            v = float(x[col_idx])
            rng = mx - mn if mx is not None and mn is not None else 0.0
            x[col_idx] = 0.0 if rng == 0 else (v - mn)/rng
    if 'z_score' in preprocessors:
        for col_idx, (mean, std) in preprocessors['z_score'].items():
            v = float(x[col_idx])
            x[col_idx] = 0.0 if std == 0 else (v - mean)/std
    # add bias in front
    xv = [1.0] + [float(xx) for xx in x]
    # compute dot
    pred = 0.0
    for i in range(len(w)):
        pred += w[i] * xv[i]
    return pred


# ------------------------
# file: main.py
# ------------------------

"""Main pipeline integrating all modules.
Assumes a CSV with columns (example): Hours,PrevScore,ExtraCurricular(Yes/No),SleepHours,SamplePapers,Performance
We will parse, encode 'Yes/No' to 1/0, scale numeric features with min-max, add bias column at front.
"""

import os
import sys

# For simplicity in this single-file distribution, call functions directly from above sections.


def demo_pipeline(csv_path):
    # Load
    rows = load_csv(csv_path, has_header=True)
    if not rows:
        print('No data found in', csv_path)
        return
    # Assume columns known; find total cols
    ncols = len(rows[0])
    # We assume last column is target
    target_col = ncols - 1
    feature_cols = list(range(0, target_col))
    # First, encode categorical values such as 'Yes'/'No' in any column which contains non-numeric entries
    # detect categorical columns
    cat_cols = []
    for c in feature_cols:
        is_cat = False
        for r in rows:
            try:
                float(r[c])
            except Exception:
                is_cat = True
                break
        if is_cat:
            cat_cols.append(c)
    preprocessors = {'encoders': {}, 'min_max': {}, 'z_score': {}}
    # encode each categorical column
    for c in cat_cols:
        rows, mapping = encode_categorical(rows, c)
        preprocessors['encoders'][c] = mapping
    # Convert all entries to numeric strings -> floats
    converters = [None] * ncols
    for i in range(ncols):
        converters[i] = lambda x, i=i: float(x)
    numeric_rows = strlist_to_numeric(rows, converters)
    # Split
    train, val, test = train_val_test_split(numeric_rows, train_ratio=0.7, val_ratio=0.15, seed=42)
    print(f'Samples: total={len(numeric_rows)} train={len(train)} val={len(val)} test={len(test)}')
    # Apply min-max scaling on numeric feature columns (not target)
    for c in feature_cols:
        # compute on train and apply same to val/test
        mn, mx = compute_min_max(train, c)
        train, _ = min_max_scale_rows(train, c, mn, mx)
        val, _ = min_max_scale_rows(val, c, mn, mx)
        test, _ = min_max_scale_rows(test, c, mn, mx)
        preprocessors['min_max'][c] = (mn, mx)
    # Optionally z-score target? We'll leave target as-is.
    # Prepare X,y
    X_train, y_train = rows_to_features_targets(train, feature_cols, target_col)
    X_val, y_val = rows_to_features_targets(val, feature_cols, target_col)
    X_test, y_test = rows_to_features_targets(test, feature_cols, target_col)
    # Add bias column at front of X matrices
    X_train = add_bias_column(X_train, at_front=True)
    X_val = add_bias_column(X_val, at_front=True)
    X_test = add_bias_column(X_test, at_front=True)
    # Feature names
    feature_names = ['bias'] + [f'X{c}' for c in feature_cols]

    # --- Simple linear regression (single best feature) via closed-form (normal equation)
    # Choose first feature as simple example
    simple_feature_idx = 1  # after bias, using first actual feature -> X_train column index 1
    # Build X_simple matrices
    Xs_train = [[row[simple_feature_idx]] for row in X_train]
    # But normal_equation expects bias included; add bias col
    Xs_train = add_bias_column(Xs_train, at_front=True)  # now bias + single feature
    y_strain = y_train
    w_simple = normal_equation_weights(Xs_train, y_strain, l2=0.0)
    preds_simple = predict_with_weights(add_bias_column([[r[simple_feature_idx]] for r in X_test], at_front=True), w_simple)
    mse_s = mse(y_test, preds_simple)
    r2_s = r_squared(y_test, preds_simple)
    print('\nSimple Linear Regression (single feature)')
    print('Weights:', w_simple)
    print(f'Test MSE: {mse_s:.5f}, R2: {r2_s:.5f}')

    # --- Multiple linear regression via normal equation
    w_mult = normal_equation_weights(X_train, y_train, l2=1e-5)
    preds_mult = predict_with_weights(X_test, w_mult)
    mse_m = mse(y_test, preds_mult)
    r2_m = r_squared(y_test, preds_mult)
    print('\nMultiple Linear Regression (normal equation)')
    print('Weights:', w_mult)
    print(f'Test MSE: {mse_m:.5f}, R2: {r2_m:.5f}')
    print_weights_interpretation(w_mult, feature_names)
    plot_actual_vs_predicted(y_test, preds_mult, fname='actual_vs_pred_mult.png')

    # --- Multiple linear regression via gradient descent with L2
    w_gd, history = gradient_descent(X_train, y_train, lr=0.1, epochs=1000, l2=0.01, verbose=False)
    preds_gd = predict_with_weights(X_test, w_gd)
    mse_gd = mse(y_test, preds_gd)
    r2_gd = r_squared(y_test, preds_gd)
    print('\nMultiple Linear Regression (gradient descent)')
    print('Weights (GD):', w_gd)
    print(f'Test MSE: {mse_gd:.5f}, R2: {r2_gd:.5f}')
    plot_mse_history(history, fname='mse_history.png')

    # Save some outputs
    print('\nPlots saved: actual_vs_pred_mult.png, mse_history.png')

    # Demonstrate a sample prediction
    sample = [7, 85, 'Yes', 8, 5]
    pred_sample = predict_single(sample, preprocessors, w_mult)
    print('\nSample input:', sample)
    print('Predicted performance (mult model):', pred_sample)


# If run as script
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python student_performance_predictor_project.py path/to/data.csv')
    else:
        csv_path = sys.argv[1]
        demo_pipeline(csv_path)
