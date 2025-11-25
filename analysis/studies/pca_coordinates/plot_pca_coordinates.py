import os
import sys
import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt


if __name__=='__main__':

    # settings
    inputfiles = sys.argv[1:]
    treename = 'tree'
    variables = [
      'pvx',
      'pvy',
      'pvz',
      'pfcand_d0_wrt0',
      'pfcand_z0_wrt0',
      'pfcand_phi0_wrt0',
      'pfcand_dxy',
      'pfcand_dz',
      'pfcand_dphi',
      'pfcand_px',
      'pfcand_py'
    ]

    # read input files
    batches = []
    branches_to_read = variables
    for idx, inputfile in enumerate(inputfiles):
        print(f'Reading file {idx+1} / {len(inputfiles)}', end='\r')
        readstr = ':'.join([inputfile, treename])
        with uproot.open(readstr) as f:
            batches.append(f.arrays(branches_to_read))
    events = ak.concatenate(batches)

    # do selection
    events = events[np.abs(events['pvz']-0)>1e-12] 
    events = events[0:1]

    # calculate ips
    d0x = -ak.flatten(-events['pfcand_d0_wrt0'], axis=None) * np.sin(ak.flatten(events['pfcand_phi0_wrt0'], axis=None))
    dx = -ak.flatten(events['pfcand_dxy'], axis=None) * np.sin(ak.flatten(events['pfcand_dphi'], axis=None))
    d0y = ak.flatten(-events['pfcand_d0_wrt0'], axis=None) * np.cos(ak.flatten(events['pfcand_phi0_wrt0'], axis=None))
    dy = ak.flatten(events['pfcand_dxy'], axis=None) * np.cos(ak.flatten(events['pfcand_dphi'], axis=None))

    # for testing
    #d0x = d0x[:1]
    #d0y = d0y[:1]
    #dx = dx[:1]
    #dy = dy[:1]
    print(d0x)
    print(d0y)
    print(dx)
    print(dy)

    # make a scatter plot of d0, pvx/pvy, and dxy
    fig, ax = plt.subplots()
    markersize = 10
    alpha = 1
    ax.scatter(events['pvx'], events['pvy'], s=markersize, alpha=alpha, label='PV')
    ax.scatter(d0x, d0y, s=markersize, alpha=alpha, label='PCA (wrt 0)')
    ax.scatter(dx, dy, s=markersize, alpha=alpha, label='PCA (wrt PV)')
    ax.grid()
    ax.legend()
    ax.set_xlim(-0.1, 0.1)
    ax.set_ylim(-0.1, 0.1)
    ax.set_xlabel('PCA x-coordinate')
    ax.set_ylabel('PCA y-coordinate')
    ax.set_title('PCA transverse coordinates w.r.t. 0 and PV')
    fig.tight_layout()
    fig.savefig('dxy_scatter.png')
