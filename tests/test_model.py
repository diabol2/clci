import math
import pytest
from slci import DistrictNode, SLCICalculator
from slci.analysis import monte_carlo_p

calc = SLCICalculator(sla_hours=12.0)
N = DistrictNode("T", 8.0, 2.5, 1, 2, 0.3)


def test_index_in_unit_interval():
    assert 0 <= calc.components(N)["SLCI"] <= 1


def test_lognormal_preserves_mean_and_std():
    mu, s = calc.lognormal_params(8.0, 2.5)
    mean = math.exp(mu + s ** 2 / 2)
    std = math.sqrt((math.exp(s ** 2) - 1) * math.exp(2 * mu + s ** 2))
    assert mean == pytest.approx(8.0) and std == pytest.approx(2.5)


def test_monotonic_in_each_parameter():
    base = calc.components(N)["SLCI"]
    assert calc.components(N.with_changes(mean_time_h=6.0))["SLCI"] > base
    assert calc.components(N.with_changes(transfers_k=0))["SLCI"] > base
    assert calc.components(N.with_changes(freq_per_day=4))["SLCI"] > base
    assert calc.components(N.with_changes(bridge_vulnerability=0.1))["SLCI"] > base
    assert calc.components(N.with_changes(std_time_h=1.5))["SLCI"] > base


def test_monte_carlo_matches_analytic():
    a = calc.sla_probability(N.mean_time_h, N.std_time_h)
    assert monte_carlo_p(calc, N) == pytest.approx(a, abs=0.005)


def test_invalid_input():
    with pytest.raises(ValueError):
        DistrictNode("x", 5, 1, 1, 1, 1.5)
