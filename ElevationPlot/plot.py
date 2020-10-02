import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np


def elevation_plot(X: list, Y: list, Z: list, axes=False) -> None:
    """
    Plot elevation data onto a 3D matplotlib graph
    :param X, Y, Z list: X, Y and Z points to plot on graph
    :param axes optional: bool display graph axes
    """
    # Init
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot points
    ax.plot_trisurf(X, Y, Z,
                    linewidth=0, antialiased=False, cmap='viridis')
    # Aditional Plot Properties
    if not axes:
        plt.axis('off')
    # Fill up as much of the screen as possible
    fig.tight_layout()
    # Labels
    ax.set_xlabel('Lat')
    ax.set_ylabel('Lon')
    ax.set_zlabel('Elevation')
    plt.show()
