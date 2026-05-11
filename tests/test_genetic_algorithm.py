"""
Unit tests for core/genetic_algorithm.py

These tests avoid running the full GA (which generates 100s of STL files).
They cover the algorithm primitives, Individual/GAResult structures,
and the key fixes applied in this refactor.
"""

import numpy as np
import pytest

from core.genetic_algorithm import (
    DESIGN_BOUNDS,
    PARAM_NAMES,
    N_VARS,
    INTEGER_VARS,
    Individual,
    GAResult,
    genes_to_params,
    params_to_genes,
    random_individual,
    dominates,
    non_dominated_sort,
    crowding_distance,
    tournament_select,
    sbx_crossover,
    polynomial_mutation,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_ind(sav: float, por: float, flow: float, buoy: float) -> Individual:
    ind = Individual()
    ind.obj_sav      = sav
    ind.obj_porosity = por
    ind.obj_flow     = flow
    ind.obj_buoyancy = buoy
    ind.rank = 0
    ind.crowding_distance = 0.0
    ind.feasible = True
    ind.genes = np.zeros(N_VARS)
    return ind


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestBounds:
    def test_all_param_names_have_bounds(self):
        for name in PARAM_NAMES:
            assert name in DESIGN_BOUNDS
            lo, hi = DESIGN_BOUNDS[name]
            assert lo < hi

    def test_integer_vars_are_subset_of_params(self):
        assert INTEGER_VARS.issubset(set(PARAM_NAMES))


class TestGenesParams:
    def test_roundtrip_preserves_values(self):
        ind = random_individual("cross_flow")
        genes_back = params_to_genes(ind.params)
        for i, name in enumerate(PARAM_NAMES):
            if name not in INTEGER_VARS:
                assert abs(genes_back[i] - ind.genes[i]) < 0.01

    def test_integer_vars_are_integers(self):
        ind = random_individual("cross_flow")
        for name in INTEGER_VARS:
            idx = PARAM_NAMES.index(name)
            val = getattr(ind.params, name)
            assert val == int(val)


class TestRandomIndividual:
    def test_genes_within_bounds(self):
        ind = random_individual()
        for i, name in enumerate(PARAM_NAMES):
            lo, hi = DESIGN_BOUNDS[name]
            assert lo <= ind.genes[i] <= hi

    def test_two_seeds_differ(self):
        """Without seeding, two random individuals should (usually) differ."""
        np.random.seed(None)  # ensure no leftover seed
        a = random_individual()
        b = random_individual()
        # Allow a tiny probability of identical — but with 10 params it's negligible
        assert not np.allclose(a.genes, b.genes)


class TestDominates:
    def test_strictly_dominant(self):
        a = _make_ind(1.0, 1.0, 1.0, 1.0)
        b = _make_ind(0.5, 0.5, 0.5, 0.5)
        assert dominates(a, b)
        assert not dominates(b, a)

    def test_equal_not_dominant(self):
        a = _make_ind(0.5, 0.5, 0.5, 0.5)
        b = _make_ind(0.5, 0.5, 0.5, 0.5)
        assert not dominates(a, b)
        assert not dominates(b, a)

    def test_trade_off_not_dominant(self):
        a = _make_ind(1.0, 0.0, 0.5, 0.5)
        b = _make_ind(0.0, 1.0, 0.5, 0.5)
        assert not dominates(a, b)
        assert not dominates(b, a)


class TestNonDominatedSort:
    def test_single_pareto_front(self):
        """All trade-offs — every individual should be on front 1."""
        pop = [
            _make_ind(1.0, 0.0, 0.5, 0.5),
            _make_ind(0.0, 1.0, 0.5, 0.5),
            _make_ind(0.5, 0.5, 1.0, 0.0),
        ]
        fronts = non_dominated_sort(pop)
        assert len(fronts) == 1
        assert len(fronts[0]) == 3

    def test_two_fronts(self):
        """A dominates B — two separate fronts expected."""
        a = _make_ind(1.0, 1.0, 1.0, 1.0)
        b = _make_ind(0.5, 0.5, 0.5, 0.5)
        fronts = non_dominated_sort([a, b])
        assert len(fronts) == 2
        assert 0 in fronts[0]   # a is index 0 (first in list)


class TestCrowdingDistance:
    def test_boundary_individuals_get_inf(self):
        """The extreme individuals on a front should get infinite crowding distance."""
        pop = [_make_ind(float(i) / 4, 1.0 - float(i) / 4, 0.5, 0.5) for i in range(5)]
        front = list(range(5))
        crowding_distance(pop, front)
        sorted_by_sav = sorted(front, key=lambda i: pop[i].obj_sav)
        assert pop[sorted_by_sav[0]].crowding_distance == float("inf")
        assert pop[sorted_by_sav[-1]].crowding_distance == float("inf")


class TestTournamentSelect:
    def test_returns_an_individual(self):
        pop = [_make_ind(float(i), 0.5, 0.5, 0.5) for i in range(6)]
        for ind in pop:
            ind.rank = 1
            ind.crowding_distance = float(np.random.random())
        result = tournament_select(pop)
        assert isinstance(result, Individual)


class TestSBXCrossover:
    def test_children_within_bounds(self):
        p1 = random_individual()
        p2 = random_individual()
        c1, c2 = sbx_crossover(p1, p2)
        for i, name in enumerate(PARAM_NAMES):
            lo, hi = DESIGN_BOUNDS[name]
            assert lo <= c1.genes[i] <= hi
            assert lo <= c2.genes[i] <= hi

    def test_integer_vars_remain_integer(self):
        p1 = random_individual()
        p2 = random_individual()
        c1, c2 = sbx_crossover(p1, p2)
        for name in INTEGER_VARS:
            idx = PARAM_NAMES.index(name)
            assert c1.genes[idx] == int(round(c1.genes[idx]))
            assert c2.genes[idx] == int(round(c2.genes[idx]))


class TestPolynomialMutation:
    def test_mutant_within_bounds(self):
        ind = random_individual()
        mutant = polynomial_mutation(ind)
        for i, name in enumerate(PARAM_NAMES):
            lo, hi = DESIGN_BOUNDS[name]
            assert lo <= mutant.genes[i] <= hi

    def test_returns_copy_not_same_object(self):
        ind = random_individual()
        mutant = polynomial_mutation(ind)
        assert mutant is not ind


class TestRandomSeedBehaviour:
    def test_seeded_runs_are_identical(self):
        """Fix 1 regression: same seed must produce same initial genes."""
        np.random.seed(7)
        a = random_individual()
        np.random.seed(7)
        b = random_individual()
        np.testing.assert_array_equal(a.genes, b.genes)

    def test_unseeded_runs_differ(self):
        """Without seeding, two consecutive populations should differ."""
        np.random.seed(None)
        a = random_individual()
        b = random_individual()
        assert not np.allclose(a.genes, b.genes)
