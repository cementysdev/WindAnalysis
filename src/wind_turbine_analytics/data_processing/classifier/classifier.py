import numpy as np
from src.wind_turbine_analytics.data_processing.classifier.model import (
    blade_rotation_speed,
    blade_active_power,
)
from src.wind_turbine_analytics.data_processing.classifier.utilities import (
    robust_calibration,
    create_mask,
    classifier_operating_regime,
)
from src.wind_turbine_analytics.data_processing.classifier.vis import (
    plot_model,
    plot_classification,
    plot_residual,
)


class Regime_Classification:

    def __init__(self, id="", y_threshold=None, dr=0.1, class_both=True):
        self.id = id
        self.theta_rot = None
        self.theta_pwer = None
        self.X_threshold = None

        # y_threshold in [0, 1] fix the plateau of the power model and rotation (in normalized space)
        if y_threshold is None:
            y_threshold = 1.0
        self.y_threshold = y_threshold

        # Classification parameters
        self.dr = dr  # residual threshold (outside = outliers)
        # if "class_both" is true, the model will classify the data in both operating models (power and rotation)
        # else the model will classify the data in the power model only
        self.both = class_both

        self.__build__()

    def __build__(self):
        self.model_blade_rot = lambda x, *theta: blade_rotation_speed(
            x, *theta, y_threshold=self.y_threshold
        )
        self.model_blade_pwer = lambda x, *theta: blade_active_power(
            x, *theta, y_threshold=self.y_threshold
        )

    def fixed(self, theta_rot, theta_pwer):
        """
        Fixed model parameters
        """
        self.theta_pwer = theta_pwer
        self.theta_rot = theta_rot

        X0_, X1_, X3_ = self.theta_rot[1:]

        # X2_ = self.theta_pwer[3]
        a, b, X0 = self.theta_pwer[:3]
        slope = a * b / 4.0
        intercept = a / 2.0 - slope * X0
        X2_ = (1.0 - intercept) / slope

        self.X_threshold = [X0_, X1_, X2_, X3_]

    def fit(
        self,
        x_wind,
        y_rot,
        y_pwer,
        bounds_pwer=None,
        x0_pwer=None,
        bounds_rot=None,
        x0_rot=None,
        loss="linear",
    ):
        """
        Fit the operating mode model (blade_rotation_speed, blade_active_power) to the operational data.
        ----------
        x_wind : array_like
            Wind speed normalized (min_max) data.
        y_rot : array_like
            Blade rotation speed normalized (min_max) data
        y_pwer : array_like
            Blade active power
        """

        if bounds_rot is None or x0_rot is None:
            x0_rot = (0.05, 3.0, 10.0, 25.0)
            bounds_rot = ((0.0, 3.0, 5.0, 20.0), (1.0, 5.0, 15.0, 30.0))
        if bounds_pwer is None or x0_pwer is None:
            x0_pwer = (1, 0, 5, 25)
            bounds_pwer = ((-np.inf, 0, 5, 20), (np.inf, np.inf, 15, 30))

        self.theta_rot = robust_calibration(
            x_wind,
            y_rot,
            self.model_blade_rot,
            bounds_rot,
            x0_rot,
            loss=loss,
            method="trf",
            f_scale=0.1,
        ).x
        self.theta_pwer = robust_calibration(
            x_wind,
            y_pwer,
            self.model_blade_pwer,
            bounds_pwer,
            x0_pwer,
            loss=loss,
            method="trf",
            f_scale=0.1,
        ).x

        X0_, X1_, X3_ = self.theta_rot[1:]

        # X2_ = self.theta_pwer[3]
        a, b, X0 = self.theta_pwer[:3]
        slope = a * b / 4.0
        intercept = a / 2.0 - slope * X0
        X2_ = (1.0 - intercept) / slope

        self.X_threshold = [X0_, X1_, X2_, X3_]

    def predict(self, x_wind):
        """
        Predict operating mode of the wind turbine based on the calibrated models
        ----------
        x_wind : array_like
            Wind speed normalized (min_max) data.
        """
        y_model_rot = self.model_blade_rot(x_wind, *self.theta_rot)
        y_model_pwer = self.model_blade_pwer(x_wind, *self.theta_pwer)
        return y_model_rot, y_model_pwer

    def __build_residual_mask__(self, x_wind, y_rot, y_pwer):
        """
        Identify outliers in the data and build a mask to exclude them from the two analytical calibrated models
        ----------
        x_wind : array_like
            Wind speed normalized (min_max) data.
        y_rot : array_like
            Blade rotation speed normalized (min_max) data
        y_pwer : array_like
            Blade active power
        """
        y_model_rot, y_model_pwer = self.predict(x_wind)
        mask_outlier = create_mask(
            y_rot, y_pwer, y_model_rot, y_model_pwer, dr=self.dr, both=self.both
        )
        return mask_outlier

    def classify(self, x_wind, y_rot, y_pwer):
        """
        Predict operational mode of the wind turbine see classifier_operating_regime() for details
        ----------
        x_wind : array_like
            Wind speed normalized (min_max) data.
        y_rot : array_like
            Blade rotation speed normalized (min_max) data
        y_pwer : array_like
            Blade active power
        """
        mask = self.__build_residual_mask__(x_wind, y_rot, y_pwer)
        X0, X1, X2, X3 = self.X_threshold
        print(self.X_threshold)
        clusters = classifier_operating_regime(x_wind, mask, X0, X1, X2, X3)
        return clusters

    def calcul_residual(self, x_wind, y_rot, y_pwer):
        """
        Calculate the residual between the observed and predicted values for the rotation speed and power
        ----------
        x_wind : array_like
            Wind speed normalized (min_max) data.
        y_rot : array_like
            Blade rotation speed normalized (min_max) data
        y_pwer : array_like
            Blade active power
        """
        y_model_rot, y_model_pwer = self.predict(x_wind)
        res_rot = y_rot - y_model_rot
        res_pow = y_pwer - y_model_pwer
        return res_rot, res_pow

    def plot_validation(self, x_wind, y_rot, y_pwer, y_pitch):
        """
        Plot the observed and predicted values for the rotation speed and power
        """
        self.fit(x_wind, y_rot, y_pwer)

        # idx = np.argsort(x_wind)
        # x_wind = x_wind[idx]
        # y_rot, y_pwer, y_pitch = y_rot[idx], y_pwer[idx], y_pitch[idx]
        # y_model_rot, y_model_pwer = self.predict(x_wind)

        print("FIT RESULT")

        # plot_model(
        #     wind_speed = x_wind,
        #     Power = y_pwer,
        #     Rotation = y_rot,
        #     Pitch = y_pitch,
        #     model_Power = y_model_pwer,
        #     model_Rotation = y_model_rot,
        #     X_threshold = self.X_threshold
        # )

        # print()

        # print('RESIDUAL PLOT')

        # res_Rotation, res_Power = self.calcul_residual(x_wind, y_rot, y_pwer)
        # plot_residual(
        #     wind_speed = x_wind,
        #     res_Power = res_Power,
        #     res_Rotation = res_Rotation,
        #     X_threshold = self.X_threshold
        # )

        print()

        print("CLASSIFICATION PLOT")
        clusters = self.classify(x_wind, y_rot, y_pwer)
        print(np.unique(clusters))
        plot_classification(
            wind_speed=x_wind,
            Power=y_pwer,
            Pitch=y_pitch,
            Rotation=y_rot,
            clusters=clusters,
            L_X=self.X_threshold,
        )

        print()
