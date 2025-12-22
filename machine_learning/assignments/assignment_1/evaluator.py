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
