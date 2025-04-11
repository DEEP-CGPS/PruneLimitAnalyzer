import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import make_interp_spline

class AnalysisPlotter:
    """
    Class for analyzing and visualizing the impact of pruning on energy consumption.
    """
    def __init__(self, dataframe: pd.DataFrame, x_column: str, y_column: str, title: str):
        self.dataframe = dataframe
        self.x_column = x_column
        self.y_column = y_column
        self.title = title

    def _detect_stabilization(self, x_values: np.ndarray, y_values: np.ndarray, patience: int, min_delta: float):
        best_value = y_values[0]
        wait = 0
        for i in range(1, len(y_values)):
            if y_values[i] < best_value - min_delta:
                best_value = y_values[i]
                wait = 0
            else:
                wait += 1
                if wait >= patience:
                    return x_values[i]
        return None

    def plot_data(self, architectures: list, pruning_distributions: list, batch_sizes: list, patience: int, min_delta: float):
        sns.set(style="whitegrid")

        def get_combined_filtered(arch, pdistr, batch):
            filtered = self.dataframe[
                ((self.dataframe["Architecture"] == arch) &
                 (self.dataframe["Pruning Distribution"] == pdistr) &
                 (self.dataframe["BATCH_SIZE"] == batch)) |
                ((self.dataframe["Architecture"] == arch) &
                 (self.dataframe["BATCH_SIZE"] == batch) &
                 (self.dataframe[self.x_column] == 0))
            ]
            return filtered.sort_values(by=self.x_column)

        # Plot 1: Original
        plt.figure(figsize=(8, 5))
        for arch in architectures:
            for num, pdistr in enumerate(pruning_distributions):
                for batch in batch_sizes:
                    filtered = get_combined_filtered(arch, pdistr, batch)
                    if filtered.empty:
                        continue
                    x_values = filtered[self.x_column].values
                    y_values = filtered[self.y_column].values
                    std_col = "STD " + self.y_column.replace("Mean ", "")
                    std_values = filtered[std_col].values if std_col in filtered.columns else np.zeros_like(y_values)
                    label = f"{arch}-{pdistr}-Batch {batch}"
                    sns.lineplot(x=x_values, y=y_values, marker='o', label=label, errorbar=None)
                    if np.any(std_values > 0):
                        plt.fill_between(x_values, y_values - std_values, y_values + std_values, alpha=0.2)
                    if 0 in x_values and num == 0:
                        unpruned_value = y_values[np.where(x_values == 0)][0]
                        plt.scatter(0, unpruned_value, color='red', s=100, zorder=3, label=f"Unpruned Model ({arch}-Batch {batch})")
        plt.xlabel(self.x_column)
        plt.ylabel(self.y_column)
        plt.title(f"Original: {self.title}")
        plt.legend(fontsize='small')
        plt.show()

        # Plot 2: Smoothed with spline interpolation
        plt.figure(figsize=(8, 5))
        for arch in architectures:
            for num, pdistr in enumerate(pruning_distributions):
                for batch in batch_sizes:
                    filtered = get_combined_filtered(arch, pdistr, batch)
                    if filtered.empty:
                        continue
                    x_values = filtered[self.x_column].values
                    y_values = filtered[self.y_column].values
                    if len(x_values) >= 4:
                        spline = make_interp_spline(x_values, y_values, k=3)
                        x_smooth = np.linspace(x_values.min(), x_values.max(), 300)
                        y_smooth = spline(x_smooth)
                        label = f"{arch}-{pdistr}-Batch {batch}"
                        plt.plot(x_smooth, y_smooth, label=label)
                        if 0 in x_values and num == 0:
                            unpruned_value = y_values[np.where(x_values == 0)][0]
                            plt.scatter(0, unpruned_value, color='red', s=100, zorder=3, label=f"Unpruned Model ({arch}-Batch {batch})")
        plt.xlabel(self.x_column)
        plt.ylabel(self.y_column)
        plt.title(f"Spline Smooth: {self.title}")
        plt.legend(fontsize='small')
        plt.show()

        # Plot 3: Moving average (combined)
        plt.figure(figsize=(8, 5))
        for arch in architectures:
            for batch in batch_sizes:
                for num, pdistr in enumerate(pruning_distributions):
                    filtered = get_combined_filtered(arch, pdistr, batch)
                    if filtered.empty:
                        continue
                    x_values = filtered[self.x_column].values
                    y_values = filtered[self.y_column].values

                    if 0 in x_values:
                        # Ensure GPR=0 uses the exact value of the unpruned model
                        unpruned_value = y_values[np.where(x_values == 0)][0]

                    if len(y_values) >= 3:
                        y_moving_avg = np.convolve(y_values, np.ones(3)/3, mode='same')
                        if 0 in x_values:
                            idx_0 = np.where(x_values == 0)[0][0]
                            y_moving_avg[idx_0] = unpruned_value  # Force exact value at GPR=0

                        label = f"{arch}-{pdistr}-Batch {batch}"
                        plt.plot(x_values, y_moving_avg, label=label)
                        if 0 in x_values and num == 0:
                            plt.scatter(0, unpruned_value, color='red', s=100, zorder=3, label=f"Unpruned Model ({arch}-Batch {batch})")
        plt.xlabel(self.x_column)
        plt.ylabel(self.y_column)
        plt.title(f"Moving Average: {self.title}")
        plt.legend(fontsize='small')
        plt.show()

