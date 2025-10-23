import os
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


def histplot(histograms,
      stack = True,
      bins = None,
      histtype = 'fill',
      color = None,
      edgecolor = None,
      alpha = None,
      label = None,
      ax = None):

    # handle case where only one instance was provided
    if not isinstance(histograms, list):
        histograms = [histograms]
        color = [color]
        edgecolor = [edgecolor]
        label = [label]
    if not isinstance(alpha, list): alpha = [alpha]*len(histograms)

    for idx in range(len(histograms)):

        # set baseline
        baseline = np.zeros(len(histograms[idx]))
        if stack: baseline = sum(histograms[:idx])

        # make plot
        ax.stairs(baseline + histograms[idx],
                  baseline = baseline,
                  edges = bins,
                  fill = (histtype=='fill'),
                  linewidth = 2,
                  color = color[idx],
                  label = label[idx],
                  alpha = alpha[idx])

    return ax
