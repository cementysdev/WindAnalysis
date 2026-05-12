"""
Code of Boris KRATZ
Source : https://github.com/cementysdev/scada_owt_fecamp
"""

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np

def plot_model(
    wind_speed,
    Power,
    Pitch,
    Rotation,
    model_Power,
    model_Rotation, 
    X_threshold
):
    # Figure
    fig, ax = plt.subplots(figsize=(9, 5))

    # Measurements
    ax.scatter(wind_speed, Rotation, c="red", s=15, label="Rotation (meas.)")
    ax.scatter(wind_speed, Power, c="tab:blue", s=15, label="Power (meas.)")
    ax.scatter(wind_speed, Pitch, c="green", s=15, label="Pitch (meas.)")

    # Models
    ax.plot(wind_speed, model_Rotation, c="black", lw=2, ls="--", label="Rotation (model)")
    ax.plot(wind_speed, model_Power, c="black", lw=2, ls="-.", label="Power (model)")

    # Vertical regime limits
    for x in X_threshold:
        ax.axvline(x, color="black", linestyle=":", alpha=1)

    # Axes & legend
    ax.set_xlabel("Wind speed (?)")
    ax.set_ylabel("Normalized value (-)")
    ax.set_ylim(0.0, 1.05)
    ax.grid(True)
    ax.legend(loc="best")

    plt.tight_layout()
    plt.show()

def plot_residual(
    wind_speed,
    res_Power,
    res_Rotation,
    X_threshold
):
    # Models
    # Figure (2 subplots)
    fig, axs = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    # Residuals: Rotation
    axs[0].scatter(
        wind_speed,
        res_Rotation,
        c="red",
        s=15,
        label="Residual Rotation"
    )
    axs[0].set_ylabel("Abs residual (-)")
    axs[0].grid(True)
    axs[0].legend()

    # Residuals: Power
    axs[1].scatter(
        wind_speed,
        res_Power,
        c="tab:blue",
        s=15,
        label="Residual Power"
    )
    axs[1].set_ylabel("Abs residual (-)")
    axs[1].set_xlabel("Wind speed")
    axs[1].grid(True)
    axs[1].legend()

    # Vertical regime limits
    for ax in axs:
        for x in X_threshold:
            ax.axvline(x, color="black", linestyle=":", alpha=1)

    plt.tight_layout()
    plt.show()

def plot_classification(
    wind_speed,
    Power,
    Pitch,
    Rotation,
    clusters,
    L_X
):
    # Discrete colormap 
    zone_labels = np.unique(clusters)
    n_zones = int(np.nanmax(clusters))
    colors = list(plt.cm.tab10.colors[:n_zones-1]) + ["#000000"] 
    cmap = ListedColormap(colors)
    bounds = np.arange(1, n_zones + 2) - 0.5
    norm = BoundaryNorm(bounds, cmap.N)
    
    # Figure with 3 subplots
    fig, axs = plt.subplots(
        3, 1, figsize=(9, 9), sharex=True,
        gridspec_kw={"right": 0.85}
    )

    # Rotation
    sc = axs[0].scatter(
        wind_speed, Rotation,
        c=clusters, s=15,
        cmap=cmap, norm=norm
    )
    axs[0].set_ylabel("Rotation (-)")
    axs[0].set_ylim(0.0, 1.05)
    axs[0].grid(True)

    # Power
    axs[1].scatter(
        wind_speed, Power,
        c=clusters, s=15,
        cmap=cmap, norm=norm
    )
    axs[1].set_ylabel("Power (-)")
    axs[1].set_ylim(0.0, 1.05)
    axs[1].grid(True)

    # Pitch
    axs[2].scatter(
        wind_speed, Pitch,
        c=clusters, s=15,
        cmap=cmap, norm=norm
    )
    axs[2].set_ylabel("Pitch (-)")
    axs[2].set_xlabel("Wind speed")
    axs[2].set_ylim(0.0, 1.05)
    axs[2].grid(True)

    # Vertical regime limits (shared)
    for ax in axs:
        for x in L_X:
            ax.axvline(x, color="black", linestyle=":", alpha=1)

    # Colorbar for clusters
    cax = fig.add_axes([0.88, 0.15, 0.03, 0.7])
    cbar = fig.colorbar(sc, cax=cax)
    cbar.set_ticks(zone_labels)
    cbar.set_label("Operating zone")
    
    plt.show()
