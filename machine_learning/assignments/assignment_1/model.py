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
