"""
Unit tests for core/flow_analysis.py
"""

import pytest
from core.geometry import GeometryMetrics
from core.flow_analysis import compute_flow_metrics, FlowMetrics, get_flow_summary


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _sample_geo(
    porosity: float = 0.65,
    hydraulic_diameter: float = 5.0,  # mm
    specific_surface_area: float = 2000.0,  # m²/m³
    sav_ratio: float = 0.8,
) -> GeometryMetrics:
    """Synthetic GeometryMetrics for flow tests."""
    geo = GeometryMetrics()
    geo.porosity = porosity
    geo.hydraulic_diameter = hydraulic_diameter
    geo.specific_surface_area = specific_surface_area
    geo.sav_ratio = sav_ratio
    geo.surface_area = 5000.0
    geo.volume = 6250.0
    geo.bounding_box_volume = 17857.0
    return geo


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestComputeFlowMetrics:
    def test_returns_flow_metrics(self):
        geo = _sample_geo()
        result = compute_flow_metrics(geo)
        assert isinstance(result, FlowMetrics)

    def test_reynolds_number_positive(self):
        result = compute_flow_metrics(_sample_geo(), superficial_velocity=0.01)
        assert result.reynolds_number > 0

    def test_pressure_drop_positive(self):
        result = compute_flow_metrics(_sample_geo(), superficial_velocity=0.01)
        assert result.pressure_drop_per_m > 0

    def test_flow_efficiency_in_range(self):
        result = compute_flow_metrics(_sample_geo())
        assert 0.0 <= result.flow_efficiency_score <= 1.0

    def test_degenerate_geometry_returns_zero_score(self):
        """Zero hydraulic diameter should not raise, just return score 0."""
        geo = _sample_geo(porosity=0.0, hydraulic_diameter=0.0)
        result = compute_flow_metrics(geo)
        assert result.flow_efficiency_score == 0.0

    def test_higher_velocity_increases_pressure_drop(self):
        geo = _sample_geo()
        low  = compute_flow_metrics(geo, superficial_velocity=0.005)
        high = compute_flow_metrics(geo, superficial_velocity=0.05)
        assert high.pressure_drop_per_m > low.pressure_drop_per_m

    def test_clogging_risk_high_for_low_porosity(self):
        geo = _sample_geo(porosity=0.40)
        result = compute_flow_metrics(geo)
        assert result.clogging_risk == "High"

    def test_clogging_risk_low_for_high_porosity(self):
        geo = _sample_geo(porosity=0.75, hydraulic_diameter=8.0)
        result = compute_flow_metrics(geo)
        assert result.clogging_risk == "Low"

    def test_flow_regime_classification(self):
        geo = _sample_geo(hydraulic_diameter=0.5)
        low_re = compute_flow_metrics(geo, superficial_velocity=0.001,
                                      fluid_density=1000.0, fluid_viscosity=0.001)
        assert low_re.flow_regime in ("Laminar (Darcy)", "Transitional", "Turbulent")

    def test_mass_transfer_coeff_positive(self):
        result = compute_flow_metrics(_sample_geo())
        assert result.mass_transfer_coefficient > 0

    def test_get_flow_summary_keys(self):
        result = compute_flow_metrics(_sample_geo())
        summary = get_flow_summary(result)
        for key in ("Reynolds Number", "Flow Regime", "Pressure Drop (Pa/m)",
                    "Flow Efficiency Score", "Clogging Risk"):
            assert key in summary
