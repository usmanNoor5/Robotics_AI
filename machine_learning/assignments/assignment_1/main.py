"""Main pipeline integrating all modules.
Assumes a CSV with columns (example): Hours,PrevScore,ExtraCurricular(Yes/No),SleepHours,SamplePapers,Performance
We will parse, encode 'Yes/No' to 1/0, scale numeric features with min-max, add bias column at front.
"""

import os
import sys

# For simplicity in this single-file distribution, call functions directly from above sections.
# from data_loader import load_csv1


import sys
from data_loader import load_csv1, strlist_to_numeric, train_val_test_split
from preprocessor import (
    encode_categorical, compute_min_max, min_max_scale_rows,
    add_bias_column, rows_to_features_targets
)
from model import (
    normal_equation_weights, predict_with_weights, mse, r_squared, 
    gradient_descent
)
from evaluator import (
    plot_actual_vs_predicted, plot_mse_history, print_weights_interpretation
)
from predictor import predict_single


def demo_pipeline(csv_path):
    # Load
    rows = load_csv1(csv_path, has_header=True)
    if not rows:
        print('No data found in', csv_path)
        return
    # Assume columns known; find total cols
    ncols = len(rows[0])
    #  last column is target
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
    # if len(sys.argv) < 2:
    #     print('Usage: python student_performance_predictor_project.py Student_Performance.csv')
    # else:
    csv_path = "Student_Performance.csv"
    demo_pipeline(csv_path)
