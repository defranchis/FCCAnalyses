import os
import sys
import math
import numpy as np
import awkward as ak


def ipsig_prob(ipsig):
    '''
    Build probability scores for impact parameter significances.
    Input arguments:
    - ipsig: awkward array of impact parameter significances.
    Returns:
    - array of the same shape as input with probability scores.
    The probability distribution is constructed from the negative side of the ipsigs.
    '''

    # separate the negative and the positive ipsigs
    negipsig = ipsig[ipsig < 0]

    # define a probability distribution for the (absolute value of the) negative ipsigs
    dist = np.abs(ak.flatten(negipsig, axis=None).to_numpy())
    norm = len(dist)
    def integral(val):
        # note: very slow, to update implementation later!
        # note: also assumes val is a 2D awkward array
        res = []
        for l1 in val:
            res.append([])
            for el in l1:
                res[-1].append(np.sum(dist>np.abs(float(el))) / norm)
        res = ak.Array(res)
        return res

    # apply function
    probs = integral(ipsig)
    factor = ak.where(ipsig<0, -ak.ones_like(ipsig), ak.ones_like(ipsig))
    probs = np.multiply(probs, factor)

    return probs


def jet_ipsig_prob(ipsig, prob=None):
    '''
    Combine per-track impact parameter probabilities into per-jet probabilities.
    '''

    # recalculate per-track probabilities if needed
    if prob is None: prob = ipsig_prob(ipsig)

    # select only positive probabilities
    prob = prob[prob>0]

    # make product
    p = ak.prod(prob, axis=1).to_numpy()

    # normalization
    # note: very slow, to update implementation later!
    pj = []
    n = ak.num(prob).to_numpy()
    for pval, nval in zip(p, n):
        factor = sum([np.power(-np.log(pval), j)/math.factorial(j) for j in range(nval)])
        pj.append(pval * factor)
    pj = np.array(pj)
    
    return pj
