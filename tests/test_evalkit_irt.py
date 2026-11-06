"""Tests for the IRT fitter and anchor-subset utilities."""

from __future__ import annotations

import numpy as np
import pytest

from evalkit.irt import (
    A_MAX,
    A_MIN,
    cluster_anchors,
    estimate_theta,
    fit_irt,
    info_anchors,
    kendall_tau_b,
    kmeans,
    sigmoid,
)


def test_sigmoid_properties() -> None:
    z = np.array([-100.0, 0.0, 100.0])
    p = sigmoid(z)
    assert p[0] == pytest.approx(0.0, abs=1e-6)
    assert p[1] == pytest.approx(0.5, abs=1e-6)
    assert p[2] == pytest.approx(1.0, abs=1e-6)


def test_fit_irt_recovers_known_parameters_simulated() -> None:
    rng = np.random.default_rng(42)
    n_models = 80
    n_items = 120
    true_theta = rng.standard_normal(n_models)
    true_c = rng.uniform(-1.5, 1.5, size=n_items)
    true_a = rng.uniform(0.7, 1.6, size=n_items)
    p = sigmoid(true_a[None, :] * true_theta[:, None] - true_c[None, :])
    y = (rng.random((n_models, n_items)) < p).astype(np.float64)

    fit_1 = fit_irt(y, model="1pl", sweeps=40)
    assert fit_1.theta.shape == (n_models,)
    assert fit_1.c.shape == (n_items,)
    assert np.all(fit_1.a == 1.0)
    corr_theta_1 = float(np.corrcoef(fit_1.theta, true_theta)[0, 1])
    assert corr_theta_1 > 0.85, f"1PL theta corr {corr_theta_1} too low"

    fit_2 = fit_irt(y, model="2pl", sweeps=40)
    assert np.all(fit_2.a >= A_MIN) and np.all(fit_2.a <= A_MAX)
    corr_theta_2 = float(np.corrcoef(fit_2.theta, true_theta)[0, 1])
    assert corr_theta_2 > 0.85, f"2PL theta corr {corr_theta_2} too low"
    corr_c = float(np.corrcoef(fit_2.c, true_c)[0, 1])
    assert corr_c > 0.80, f"2PL c corr {corr_c} too low"


def test_fit_irt_handles_missingness_and_soft_labels() -> None:
    rng = np.random.default_rng(7)
    y = rng.uniform(0.0, 1.0, size=(30, 40))
    mask = rng.random((30, 40)) > 0.15
    fit = fit_irt(y, mask=mask, model="2pl", sweeps=15)
    assert np.all(np.isfinite(fit.theta))
    assert np.all(np.isfinite(fit.a))
    assert np.all(np.isfinite(fit.c))


def test_fit_irt_tol_stops_early_and_sets_converged_flag() -> None:
    rng = np.random.default_rng(3)
    y = (rng.random((40, 60)) < 0.5).astype(np.float64)
    short = fit_irt(y, model="2pl", sweeps=3)
    assert short.sweeps == 3 and not short.converged
    tight = fit_irt(y, model="2pl", sweeps=400, tol=1e-4)
    assert tight.converged and tight.sweeps < 400
    assert abs(tight.last_change) < 1e-4
    full = fit_irt(y, model="2pl", sweeps=7)
    assert full.sweeps == 7


def test_estimate_theta_monotonic_in_score() -> None:
    rng = np.random.default_rng(0)
    n_items = 25
    a = rng.uniform(0.8, 1.5, size=n_items)
    c = rng.uniform(-1.0, 1.0, size=n_items)
    y_low = np.zeros((1, n_items))
    y_mid = np.full((1, n_items), 0.5)
    y_high = np.ones((1, n_items))
    mask = np.ones((1, n_items), dtype=bool)

    th_low = estimate_theta(a, c, y_low, mask)[0]
    th_mid = estimate_theta(a, c, y_mid, mask)[0]
    th_high = estimate_theta(a, c, y_high, mask)[0]
    assert th_low < th_mid < th_high


def test_kendall_tau_b() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert kendall_tau_b(x, x) == pytest.approx(1.0)
    assert kendall_tau_b(x, -x) == pytest.approx(-1.0)
    y = np.array([1.0, 3.0, 2.0, 4.0, 5.0])
    assert 0.7 < kendall_tau_b(x, y) < 0.9
    const = np.ones(5)
    assert np.isnan(kendall_tau_b(x, const))


def test_kmeans_and_cluster_anchors() -> None:
    rng = np.random.default_rng(3)
    c1 = rng.standard_normal((30, 4)) - 3.0
    c2 = rng.standard_normal((30, 4)) + 3.0
    x = np.vstack([c1, c2])
    labels, centres = kmeans(x, 2, rng, n_init=3)
    assert labels.shape == (60,)
    assert centres.shape == (2, 4)
    w = np.ones(60) / 60.0
    idx, masses = cluster_anchors(x, w, 2, rng)
    assert idx.size == 2
    assert masses.sum() == pytest.approx(1.0)
    assert set(idx).issubset(range(60))


def test_info_anchors_diversity() -> None:
    fit = fit_irt(np.eye(20), model="2pl", sweeps=10)
    anchors = info_anchors(fit, k=10)
    assert len(anchors) == 10
    assert len(set(anchors)) == 10  # distinct items chosen
