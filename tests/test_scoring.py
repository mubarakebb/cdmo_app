"""
Unit tests for core/scoring.py
"""

import copy
import pytest
from core.scoring import (
    ObjectiveWeights,
    CarrierScore,
    normalize_scores,
    compute_composite_scores,
    find_pareto_frontier,
    generate_improvement_suggestions,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_carrier(
    design_id: str = "test",
    material: str = "PLA",
    sav: float = 0.5,
    porosity: float = 0.6,
    flow: float = 0.7,
    buoy: float = 0.8,
    biofilm: float = 0.85,
    mechanical: float = 0.65,
) -> CarrierScore:
    cs = CarrierScore()
    cs.design_id = design_id
    cs.filename = f"{design_id}.stl"
    cs.material = material
    cs.sav_ratio = sav
    cs.porosity = porosity
    cs.flow_efficiency = flow
    cs.buoyancy_score = buoy
    cs.score_biofilm_affinity = biofilm
    cs.score_mechanical = mechanical
    return cs


def _default_weights() -> ObjectiveWeights:
    return ObjectiveWeights()  # defaults sum to 1.0


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestNormalizeScores:
    def test_min_max_normalization(self):
        result = normalize_scores([0.0, 5.0, 10.0])
        assert result[0] == pytest.approx(0.0)
        assert result[-1] == pytest.approx(1.0)

    def test_invert_when_lower_is_better(self):
        result = normalize_scores([1.0, 5.0, 10.0], higher_is_better=False)
        assert result[0] == pytest.approx(1.0)
        assert result[-1] == pytest.approx(0.0)

    def test_all_equal_returns_neutral(self):
        result = normalize_scores([3.0, 3.0, 3.0])
        assert all(v == pytest.approx(0.5) for v in result)


class TestObjectiveWeights:
    def test_normalize_sums_to_one(self):
        w = ObjectiveWeights(sav_ratio=1.0, porosity=1.0, flow_efficiency=1.0,
                             buoyancy=1.0, biofilm_affinity=1.0, mechanical=1.0)
        w.normalize()
        total = (w.sav_ratio + w.porosity + w.flow_efficiency +
                 w.buoyancy + w.biofilm_affinity + w.mechanical)
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_zero_weights_raises(self):
        w = ObjectiveWeights(sav_ratio=0.0, porosity=0.0, flow_efficiency=0.0,
                             buoyancy=0.0, biofilm_affinity=0.0, mechanical=0.0)
        with pytest.raises(ValueError):
            w.normalize()


class TestComputeCompositeScores:
    def test_returns_sorted_by_score(self):
        carriers = [_make_carrier("A", sav=0.1), _make_carrier("B", sav=0.9)]
        result = compute_composite_scores(carriers, _default_weights())
        assert result[0].rank == 1
        assert result[0].composite_score >= result[1].composite_score

    def test_scores_in_zero_one_range(self):
        carriers = [_make_carrier(f"c{i}", sav=i * 0.1) for i in range(5)]
        result = compute_composite_scores(carriers, _default_weights())
        for c in result:
            assert 0.0 <= c.composite_score <= 1.0

    def test_does_not_mutate_input_weights(self):
        """Regression for Fix 3: weights object must not be mutated."""
        w = ObjectiveWeights(sav_ratio=2.0, porosity=2.0, flow_efficiency=2.0,
                             buoyancy=2.0, biofilm_affinity=2.0, mechanical=2.0)
        original_sav = w.sav_ratio
        carriers = [_make_carrier("A"), _make_carrier("B")]
        compute_composite_scores(carriers, w)
        assert w.sav_ratio == original_sav, "weights object was mutated by compute_composite_scores"

    def test_empty_list_returns_empty(self):
        assert compute_composite_scores([], _default_weights()) == []


class TestFindParetoFrontier:
    def test_dominant_carrier_is_pareto(self):
        """Carrier A dominates all others — must be Pareto-optimal."""
        a = _make_carrier("A", sav=1.0, porosity=1.0, flow=1.0, buoy=1.0)
        b = _make_carrier("B", sav=0.5, porosity=0.5, flow=0.5, buoy=0.5)
        # Need normalized scores populated first
        carriers = compute_composite_scores([a, b], _default_weights())
        result = find_pareto_frontier(carriers)
        a_result = next(c for c in result if c.design_id == "A")
        b_result = next(c for c in result if c.design_id == "B")
        assert a_result.is_pareto_optimal
        assert not b_result.is_pareto_optimal

    def test_incomparable_carriers_both_pareto(self):
        """Two carriers on a trade-off — neither dominates the other."""
        a = _make_carrier("A", sav=1.0, porosity=0.0, flow=0.5, buoy=0.5)
        b = _make_carrier("B", sav=0.0, porosity=1.0, flow=0.5, buoy=0.5)
        carriers = compute_composite_scores([a, b], _default_weights())
        result = find_pareto_frontier(carriers)
        assert all(c.is_pareto_optimal for c in result)


class TestImprovementSuggestions:
    def test_returns_list_of_strings(self):
        c = _make_carrier("A")
        c.score_sav = 0.2
        c.score_porosity = 0.8
        c.score_flow = 0.8
        c.score_buoyancy = 0.8
        suggestions = generate_improvement_suggestions(c, _default_weights())
        assert isinstance(suggestions, list)
        assert len(suggestions) >= 1
        assert all(isinstance(s, str) for s in suggestions)

    def test_no_suggestions_for_perfect_carrier(self):
        c = _make_carrier("A")
        c.score_sav = 1.0
        c.score_porosity = 1.0
        c.score_flow = 1.0
        c.score_buoyancy = 1.0
        c.score_biofilm_affinity = 1.0
        suggestions = generate_improvement_suggestions(c, _default_weights())
        # Should fall back to "performs well" message
        assert len(suggestions) >= 1
