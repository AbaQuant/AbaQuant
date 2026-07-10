"""Hierarchical Risk Parity allocation.

Purpose
-------
The module implements quasi-diagonalisation, cluster-risk estimation, and recursive bisection for Hierarchical Risk Parity portfolios.

Conventions
-----------
Covariance and correlation matrices must use a common asset ordering. Output weights are indexed by the supplied ticker labels.

References
----------
[ 1 ] Lopez de Prado, M. (2016), "Building Diversified Portfolios that Outperform Out of Sample".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform


def _get_quasi_diag(link: np.ndarray) -> list[int]:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    link : np.ndarray
        Hierarchical clustering linkage matrix.

    Returns
    -------
    list[int]
        Ordered collection produced by the  get quasi diag calculation.
    """
    link = link.astype(int)
    sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
    num_items = link[-1, 3]
    while sort_ix.max() >= num_items:
        sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)
        df0 = sort_ix[sort_ix >= num_items]
        i, j = df0.index, df0.values - num_items
        sort_ix[i] = link[j, 0]
        df1 = pd.Series(link[j, 1], index=i + 1)
        sort_ix = pd.concat([sort_ix, df1]).sort_index()
        sort_ix.index = range(sort_ix.shape[0])
    return sort_ix.tolist()


def _get_cluster_var(cov: pd.DataFrame, items: list[str]) -> float:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    cov : pd.DataFrame
        Covariance matrix ordered consistently with the associated asset vectors.
    items : list[str]
        Asset positions belonging to a hierarchical-risk-parity cluster.

    Returns
    -------
    float
        Computed  get cluster var as a scalar in the units implied by the input values.
    """
    cov_slice = cov.loc[items, items]
    ivp = 1.0 / np.diag(cov_slice)
    ivp /= ivp.sum()
    weights = ivp.reshape(-1, 1)
    return float((weights.T @ cov_slice.values @ weights).item())


def _recursive_bisection(cov: pd.DataFrame, sort_ix: list[str]) -> pd.Series:
    """Perform an internal calculation used by the documented public workflow.

    Parameters
    ----------
    cov : pd.DataFrame
        Covariance matrix ordered consistently with the associated asset vectors.
    sort_ix : list[str]
        Asset order produced by hierarchical quasi-diagonalisation.

    Returns
    -------
    pd.Series
        One-dimensional labeled result aligned to the documented input order.
    """
    weights = pd.Series(1.0, index=sort_ix)
    clusters = [sort_ix]
    while clusters:
        new_clusters = []
        for cluster in clusters:
            if len(cluster) > 1:
                half = len(cluster) // 2
                new_clusters += [cluster[:half], cluster[half:]]
        for i in range(0, len(new_clusters), 2):
            cluster_0, cluster_1 = new_clusters[i], new_clusters[i + 1]
            var_0 = _get_cluster_var(cov, cluster_0)
            var_1 = _get_cluster_var(cov, cluster_1)
            denom = var_0 + var_1
            alpha = 1 - var_0 / denom if denom > 0 else 0.5
            weights[cluster_0] *= alpha
            weights[cluster_1] *= 1 - alpha
        clusters = [cluster for cluster in new_clusters if len(cluster) > 1]
    return weights


def hierarchical_risk_parity(
    cov_matrix: pd.DataFrame,
    corr_matrix: pd.DataFrame,
    tickers: list[str],
) -> np.ndarray:
    """Compute Hierarchical Risk Parity weights from covariance and correlation inputs.

    Parameters
    ----------
    cov_matrix : pd.DataFrame
        Square covariance matrix ordered consistently with the asset order.
    corr_matrix : pd.DataFrame
        Square correlation matrix ordered consistently with covariance and ticker order.
    tickers : list[str]
        Ticker labels or an iterable of raw ticker strings.

    Returns
    -------
    np.ndarray
        Result of the hierarchical risk parity calculation.

    Notes
    -----
    This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
    """
    if len(tickers) < 2:
        return np.repeat(1.0 / max(len(tickers), 1), len(tickers))

    corr = corr_matrix.clip(-1, 1)
    dist_arr = np.sqrt(0.5 * (1 - corr.values)).copy()
    np.fill_diagonal(dist_arr, 0.0)
    link = linkage(squareform(dist_arr, checks=False), method="single")
    sort_ix = _get_quasi_diag(link)
    sorted_tickers = [tickers[i] for i in sort_ix]
    weights = _recursive_bisection(cov_matrix, sorted_tickers).reindex(tickers).values
    return weights / weights.sum()


__all__ = ["hierarchical_risk_parity"]
