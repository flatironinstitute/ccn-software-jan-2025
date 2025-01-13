#!/usr/bin/env python3

import pynapple as nap
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Union, Optional
from numpy.typing import NDArray

__all__ = ["plot_features", "plot_head_direction_tuning_model"]

def plot_features(
    input_feature: Union[nap.Tsd, nap.TsdFrame, nap.TsdTensor, NDArray],
    sampling_rate: float,
    suptitle: str,
    n_rows: int = 20,
):
    """
    Plot feature matrix.

    Parameters
    ----------
    input_feature:
        The (num_samples, n_neurons, num_feature) feature array.
    sampling_rate:
        Sampling rate in hz.
    n_rows:
        Number of rows to plot.
    suptitle:
        Suptitle of the plot.

    Returns
    -------

    """
    input_feature = np.squeeze(input_feature).dropna()
    window_size = input_feature.shape[1]
    fig = plt.figure(figsize=(8, 8))
    plt.suptitle(suptitle)
    time = np.arange(0, window_size) / sampling_rate
    for k in range(n_rows):
        ax = plt.subplot(n_rows, 1, k + 1)
        plt.step(time, input_feature[k].squeeze(), where="post")

        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)

        ax.axvspan(0, time[-1], alpha=0.4, color="orange")
        ax.set_yticks([])
        if k != n_rows - 1:
            ax.set_xticks([])
        else:
            ax.set_xlabel("lag (sec)")
        if k in [0, n_rows - 1]:
            ax.set_ylabel("$t_{%d}$" % (window_size + k), rotation=0)

    plt.tight_layout()
    return fig


def plot_head_direction_tuning_model(
    tuning_curves: pd.DataFrame,
    predicted_firing_rate: nap.TsdFrame,
    spikes: nap.TsGroup,
    angle: nap.Tsd,
    pref_ang: Optional[pd.Series] = None,
    model_tuning_curves: Optional[pd.DataFrame] = None,
    threshold_hz: int = 1,
    start: float = 8910,
    end: float = 8960,
    cmap_label="hsv",
    figsize=None,
):
    """
    Plot head direction tuning.

    Parameters
    ----------
    tuning_curves:
        The tuning curve dataframe.
    predicted_firing_rate:
        The time series of the predicted rate.
    spikes:
        The spike times.
    angle:
        The heading angles.
    threshold_hz:
        Minimum firing rate for neuron to be plotted.,
    start:
        Start time
    end:
        End time
    cmap_label:
        cmap label ("hsv", "rainbow", "Reds", ...)
    figsize:
        Figure size in inches.

    Returns
    -------
    fig:
        The figure.
    """
    plot_ep = nap.IntervalSet(start, end)
    index_keep = spikes.restrict(plot_ep).getby_threshold("rate", threshold_hz).index

    # filter neurons
    tuning_curves = tuning_curves.loc[:, index_keep]
    if pref_ang is None:
        pref_ang = tuning_curves.idxmax()
    pref_ang = pref_ang.loc[index_keep]
    spike_tsd = (
        spikes.restrict(plot_ep).getby_threshold("rate", threshold_hz).to_tsd(pref_ang)
    )

    # plot raster and heading
    cmap = plt.get_cmap(cmap_label)
    unq_angles = np.unique(pref_ang.values)
    n_subplots = len(unq_angles)
    relative_color_levs = (unq_angles - unq_angles[0]) / (
        unq_angles[-1] - unq_angles[0]
    )

    if model_tuning_curves is None:
        n_rows = 4
    else:
        model_tuning_curves = model_tuning_curves.loc[:, index_keep]
        n_rows = 5
    if figsize is None:
        figsize = [12, 6]
        if n_rows == 5:
            figsize[1] += 2
    fig = plt.figure(figsize=figsize)
    # plot head direction angle
    ax = plt.subplot2grid(
        (n_rows, n_subplots), loc=(0, 0), rowspan=1, colspan=n_subplots, fig=fig
    )
    ax.plot(angle.restrict(plot_ep), color="k", lw=2)
    ax.set_ylabel("Angle (rad)")
    ax.set_title("Animal's Head Direction")

    ax = plt.subplot2grid(
        (n_rows, n_subplots), loc=(1, 0), rowspan=1, colspan=n_subplots, fig=fig
    )
    ax.set_title("Neural Activity")
    for i, ang in enumerate(unq_angles):
        sel = spike_tsd.d == ang
        ax.plot(
            spike_tsd[sel].t,
            np.ones(sel.sum()) * i,
            "|",
            color=cmap(relative_color_levs[i]),
            alpha=0.5,
        )
    ax.set_ylabel("Sorted Neurons")
    ax.set_xlabel("Time (s)")

    ax = plt.subplot2grid(
        (n_rows, n_subplots), loc=(2, 0), rowspan=1, colspan=n_subplots, fig=fig
    )
    ax.set_title("Neural Firing Rate")

    fr = predicted_firing_rate.restrict(plot_ep).d
    fr = fr.T / np.max(fr, axis=1)
    ax.imshow(fr[::-1], cmap="Blues", aspect="auto")
    ax.set_ylabel("Sorted Neurons")
    ax.set_xlabel("Time (s)")

    for i, ang in enumerate(unq_angles):
        neu_idx = np.argsort(pref_ang.values)[i]
        ax = plt.subplot2grid(
            (n_rows, n_subplots),
            loc=(3 + i // n_subplots, i % n_subplots),
            rowspan=1,
            colspan=1,
            fig=fig,
            projection="polar",
        )
        ax.fill_between(
            tuning_curves.iloc[:, neu_idx].index,
            np.zeros(len(tuning_curves)),
            tuning_curves.iloc[:, neu_idx].values,
            color=cmap(relative_color_levs[i]),
            alpha=0.5,
        )
        ax.set_xticks([])
        ax.set_yticks([])

    if model_tuning_curves is not None:
        for i, ang in enumerate(unq_angles):
            neu_idx = np.argsort(pref_ang.values)[i]

            ax = plt.subplot2grid(
                (n_rows, n_subplots),
                loc=(4 + i // n_subplots, i % n_subplots),
                rowspan=1,
                colspan=1,
                fig=fig,
                projection="polar",
            )
            ax.fill_between(
                model_tuning_curves.iloc[:, neu_idx].index,
                np.zeros(len(model_tuning_curves)),
                model_tuning_curves.iloc[:, neu_idx].values,
                color=cmap(relative_color_levs[i]),
                alpha=0.5,
            )
            ax.set_xticks([])
            ax.set_yticks([])
    plt.tight_layout()
    return fig
