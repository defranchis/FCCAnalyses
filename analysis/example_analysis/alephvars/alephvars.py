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

    # approch 1: naive (very slow)
    #def integral(val):
    #    # note: very slow, to update implementation later!
    #    # note: also assumes val is a 2D awkward array
    #    res = []
    #    for l1 in val:
    #        res.append([])
    #        for el in l1:
    #            res[-1].append(np.sum(dist>np.abs(float(el))) / norm)
    #    res = ak.Array(res)
    #    return res
    #probs = integral(ipsig)
    
    # approach 2: same but with np.vectorize (still very slow)
    #def integral(val):
    #    return np.sum(dist>np.abs(float(val))) / norm
    #vectorized_integral = np.vectorize(integral)
    #ipsig_num = ak.num(ipsig)
    #probs = ak.unflatten(vectorized_integral(ak.flatten(ipsig)), ipsig_num)

    # approach 3: histogram instead of full array
    bins = np.concatenate((np.linspace(0, 5, num=1000), np.linspace(5, np.quantile(dist, 0.99)*1.5, num=500)))
    bincenters = (bins[:-1] + bins[1:])/2
    hist = np.histogram(dist, bins=bins)[0]
    def integral(val):
        return np.sum(hist[bincenters>=abs(float(val))])/norm
    vectorized_integral = np.vectorize(integral)
    ipsig_num = ak.num(ipsig)
    probs = ak.unflatten(vectorized_integral(ak.flatten(ipsig)), ipsig_num)

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

    # calculate normalization factors
    n = ak.num(prob).to_numpy()
    maxn = np.amax(n)
    normfactors = np.ones((len(n), maxn))
    for j in range(1, maxn):
        normfactors[:, j] = np.power(-np.log(p), j)/math.factorial(j)
    normfactors = ak.fill_none(ak.pad_none(prob, maxn, axis=1), 0).to_numpy()
    normfactors = np.sum(normfactors, axis=1)

    # normalization
    pj = np.multiply(p, normfactors)

    # do clipping to range 0-1
    pj = np.clip(pj, a_min=0, a_max=1)
    
    return pj
