"""
Code of Boris KRATZ
Source : https://github.com/cementysdev/scada_owt_fecamp
"""

import numpy as np

def blade_rotation_speed(x, *theta, y_threshold=1.0):

    if y_threshold < 0 and y_threshold > 1:
        y_threshold = 1.0

    # The unknown parameters that we want to find
    a, X0, X1, X2 = theta
    b = y_threshold - a * (X1 - X0)

    y = np.zeros_like(x, dtype=float)

    mask_1 = x < X0
    mask_2 = (x >= X0) & (x < X1)
    mask_3 = (x >= X1) & (x < X2)
    mask_4 = x >= X2

    # Plateau
    y[mask_1] = 0.0

    # Linear
    y[mask_2] = a * (x[mask_2] - X0) + b

    # Plateau
    # y_nom =  (a * (X1 - X0) + b)
    y[mask_3] = y_threshold

    # Cut-off
    y[mask_4] = 0.0

    return y

def blade_active_power(x, *theta, y_threshold=1.0):
    
    if y_threshold < 0 and y_threshold > 1:
        y_threshold = 1.0

    # The unknown parameters that we want to find
    a, b, X0, X2 = theta
    
    # C1 continuity at X0
    slope = a * b / 4.0
    intercept = a / 2.0 - slope * X0
    
    # With y[mask_3] = 1
    X1 = (y_threshold - intercept) / slope

    mask_1 = (x <= X0)
    mask_2 = (x > X0) & (x <= X1)
    mask_3 = (x > X1) & (x <= X2)
    mask_4 = (x > X2)
    
    # Vectorized the expression 
    y = np.zeros_like(x)
    
    # Sigmoid part
    y[mask_1] = a / (1.0 + np.exp(-b* (x[mask_1] - X0)))

    # Linear
    y[mask_2] = slope * x[mask_2] + intercept

    # Plateau
    y[mask_3] = y_threshold
    # y[mask_3] = slope * X1 + intercept

    # Cut-off
    y[mask_4] = 0.0

    return y
