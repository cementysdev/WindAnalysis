"""
Code of Boris KRATZ
Source : https://github.com/cementysdev/scada_owt_fecamp
"""

import numpy as np
from scipy.optimize import least_squares

def robust_calibration(x_obs, y_obs, mod_fct, bounds, x0, loss='linear', method = 'trf', f_scale = 0.1):
    # Advice : take huber loss (more robust than quadratic error)
    
    def residus(theta, x, y):
        return mod_fct(x, *theta) - y
    
    res_robust = least_squares(fun = residus, loss = loss, method = method, f_scale = f_scale, x0 = x0, bounds = bounds, args = (x_obs, y_obs))
    
    return res_robust

def residual_filter(y_obs, y_model, dr=0.1):
    
    r = abs(y_obs - y_model)
    mask = r <= dr
    
    return mask

def create_mask(y_obs_rot, y_obs_pow, y_model_rot, y_model_pow, dr=0.1, both=True):
    
    mask_pow = residual_filter(y_obs_pow, y_model_pow, dr)
    
    if both:
        mask_rot = residual_filter(y_obs_rot, y_model_rot, dr)
        return mask_rot & mask_pow

    return mask_pow

def classifier_operating_regime(x_obs, mask, X0, X1, X2, X3):

    operating_regime = np.zeros_like(x_obs, dtype=int)
    
    # Zone 1 : stop (low wind speed)
    mask1 = (x_obs < X0) 
    operating_regime[mask1] = 1
    
    # Zone 2 : start
    mask2 = (x_obs < X1) & (x_obs >= X0) 
    operating_regime[mask2] = 2
    
    # Zone 3 : max rotation but not max power
    mask3 = (x_obs < X2) & (x_obs >= X1) 
    operating_regime[mask3] = 3
    
    # Zone 4 : max power
    mask4 = (x_obs < X3) & (x_obs >= X2) 
    operating_regime[mask4] = 4
    
    # Zone 5 : stop (high wind speed)
    mask5 = (x_obs >= X3) 
    operating_regime[mask5] = 5
    
    # Zone 6 
    operating_regime[~mask] = 6
    
    return operating_regime
