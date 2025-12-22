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
