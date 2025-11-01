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
    events = events[:1]

    # make a distribution of z0, pvz, and dz
    bins = np.linspace(-3, 3, num=51)
    fig, ax = plt.subplots()
    ax.hist(events['pvz'], bins=bins, density=True, histtype='step', linewidth=2, label='PVz')
    ax.hist(ak.flatten(events['pfcand_z0_wrt0'], axis=None), bins=bins,
      density=True, histtype='step', linewidth=2, label='Z0 (wrt 0)')
    ax.hist(ak.flatten(events['pfcand_dz'], axis=None), bins=bins,
      density=True, histtype='step', linewidth=2, label='dz (wrt PV)')
    ax.legend()
    fig.tight_layout()
    fig.savefig('dz.png')

    # make a distribution of d0x, pvx, and dx
    bins = np.linspace(-0.2, 0.2, num=51)
    fig, ax = plt.subplots()
    d0x = np.abs(ak.flatten(events['pfcand_d0_wrt0'], axis=None)) * np.cos(ak.flatten(events['pfcand_phi0_wrt0'], axis=None))
    dx = np.abs(ak.flatten(events['pfcand_dxy'], axis=None)) * np.cos(ak.flatten(events['pfcand_dphi'], axis=None))
    ax.hist(events['pvx'], bins=bins, density=True, histtype='step', linewidth=2, label='PVx')
    ax.hist(d0x, bins=bins, density=True, histtype='step', linewidth=2, label='D0x (wrt 0)')
    ax.hist(dx, bins=bins, density=True, histtype='step', linewidth=2, label='dx (wrt PV)')
    ax.legend()
    fig.tight_layout()
    fig.savefig('dx.png')

    # make a distribution of d0y, pvy, and dy
    bins = np.linspace(-0.2, 0.2, num=51)
    fig, ax = plt.subplots()
    d0y = np.abs(ak.flatten(events['pfcand_d0_wrt0'], axis=None)) * np.sin(ak.flatten(events['pfcand_phi0_wrt0'], axis=None))
    dy = np.abs(ak.flatten(events['pfcand_dxy'], axis=None)) * np.sin(ak.flatten(events['pfcand_dphi'], axis=None))
    ax.hist(events['pvy'], bins=bins, density=True, histtype='step', linewidth=2, label='PVy')
    ax.hist(d0y, bins=bins, density=True, histtype='step', linewidth=2, label='D0y (wrt 0)')
    ax.hist(dy, bins=bins, density=True, histtype='step', linewidth=2, label='dy (wrt PV)')
    ax.legend()
    fig.tight_layout()
    fig.savefig('dy.png')

    # make a distribution of d0 and dxy
    bins = np.linspace(-0.2, 0.2, num=51)
    fig, ax = plt.subplots()
    ax.hist(ak.flatten(events['pfcand_d0_wrt0'], axis=None), bins=bins,
      density=True, histtype='step', linewidth=2, label='D0 (wrt0)')
    ax.hist(ak.flatten(events['pfcand_dxy'], axis=None), bins=bins,
      density=True, histtype='step', linewidth=2, label='dxy (wrt PV)')
    ax.legend()
    fig.tight_layout()
    fig.savefig('dxy.png')

    # make a scatter plot of d0, pvx/pvy, and dxy
    '''fig, ax = plt.subplots()
    markersize=3
    alpha = 1
    d0x = np.abs(ak.flatten(events['pfcand_d0_wrt0'], axis=None)) * np.cos(ak.flatten(events['pfcand_phi0_wrt0'], axis=None))
    d0y = np.abs(ak.flatten(events['pfcand_d0_wrt0'], axis=None)) * np.sin(ak.flatten(events['pfcand_phi0_wrt0'], axis=None))
    dx = np.abs(ak.flatten(events['pfcand_dxy'], axis=None)) * np.cos(ak.flatten(events['pfcand_dphi'], axis=None))
    dy = np.abs(ak.flatten(events['pfcand_dxy'], axis=None)) * np.sin(ak.flatten(events['pfcand_dphi'], axis=None))
    ax.scatter(events['pvx'], events['pvy'], s=markersize, alpha=alpha, label='PV')
    ax.scatter(d0x, d0y, s=markersize, alpha=alpha, label='PCA (wrt 0)')
    ax.scatter(dx, dy, s=markersize, alpha=alpha, label='PCA (wrt PV)')
    ax.legend()
    ax.set_xlim(-0.2, 0.2)
    ax.set_ylim(-0.2, 0.2)
    fig.tight_layout()
    fig.savefig('dxy.png')'''
