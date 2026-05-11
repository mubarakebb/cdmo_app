"""
Unit tests for utils/persistence.py

Tests the JSON schema-v2 save/load cycle for both analysis sessions
and GA results. Does NOT test the legacy pickle path.
"""

import json
import os
import tempfile

import pytest

from core.geometry import GeometryMetrics
from core.flow_analysis import FlowMetrics
from core.buoyancy import BuoyancyMetrics
from core.scoring import CarrierScore
from utils.persistence import (
    SCHEMA_VERSION,
    _carrier_score_to_dict,
    _dict_to_carrier_score,
    _geo_to_dict,
    _dict_to_geo,
    _flow_to_dict,
    _dict_to_flow,
    _buoy_to_dict,
    _dict_to_buoy,
    save_session,
    load_session,
    list_sessions,
    delete_session,
    export_session_csv,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_geo():
    g = GeometryMetrics()
    g.filename = "test.stl"
    g.surface_area = 5000.0
    g.volume = 1000.0
    g.bounding_box_volume = 3000.0
    g.porosity = 0.667
    g.sav_ratio = 5.0
    g.specific_surface_area = 2000.0
    g.hydraulic_diameter = 4.0
    g.dim_x = 20.0; g.dim_y = 20.0; g.dim_z = 20.0
    g.num_triangles = 1200
    g.is_watertight = True
    return g


@pytest.fixture
def sample_flow():
    f = FlowMetrics()
    f.flow_velocity = 0.01
    f.fluid_density = 1015.0
    f.fluid_viscosity = 0.003
    f.reynolds_number = 12.5
    f.flow_regime = "Laminar (Darcy)"
    f.pressure_drop_per_m = 450.0
    f.flow_efficiency_score = 0.72
    f.clogging_risk = "Low"
    f.clogging_risk_score = 0.15
    return f


@pytest.fixture
def sample_buoy():
    b = BuoyancyMetrics()
    b.material_name = "PLA"
    b.material_density = 1.245
    b.fluid_density = 1.015
    b.effective_density = 0.415
    b.behavior = "Floats"
    b.buoyancy_score = 0.75
    b.reactor_notes = "Test notes."
    return b


@pytest.fixture
def sample_carrier():
    c = CarrierScore()
    c.design_id = "test_PLA"
    c.filename = "test.stl"
    c.material = "PLA"
    c.composite_score = 0.72
    c.sav_ratio = 5.0
    c.porosity = 0.667
    c.score_sav = 0.8
    c.score_porosity = 0.7
    c.score_flow = 0.65
    c.score_buoyancy = 0.75
    c.score_biofilm_affinity = 0.85
    c.score_mechanical = 0.65
    c.is_pareto_optimal = True
    c.rank = 1
    return c


@pytest.fixture
def session_dir(tmp_path, monkeypatch):
    """Redirect SESSION_DIR to a temp directory for isolation."""
    import utils.persistence as pers
    monkeypatch.setattr(pers, "SESSION_DIR", str(tmp_path))
    return tmp_path


# ─── Serialization round-trip tests ───────────────────────────────────────────

class TestGeometrySerialization:
    def test_roundtrip(self, sample_geo):
        d = _geo_to_dict(sample_geo)
        restored = _dict_to_geo(d)
        assert restored.filename == sample_geo.filename
        assert restored.surface_area == pytest.approx(sample_geo.surface_area)
        assert restored.porosity == pytest.approx(sample_geo.porosity)
        assert restored.is_watertight == sample_geo.is_watertight


class TestFlowSerialization:
    def test_roundtrip(self, sample_flow):
        d = _flow_to_dict(sample_flow)
        restored = _dict_to_flow(d)
        assert restored.flow_regime == sample_flow.flow_regime
        assert restored.pressure_drop_per_m == pytest.approx(sample_flow.pressure_drop_per_m)


class TestBuoyancySerialization:
    def test_roundtrip(self, sample_buoy):
        d = _buoy_to_dict(sample_buoy)
        restored = _dict_to_buoy(d)
        assert restored.material_name == sample_buoy.material_name
        assert restored.buoyancy_score == pytest.approx(sample_buoy.buoyancy_score)
        assert restored.behavior == sample_buoy.behavior


class TestCarrierScoreSerialization:
    def test_roundtrip(self, sample_carrier):
        d = _carrier_score_to_dict(sample_carrier)
        restored = _dict_to_carrier_score(d)
        assert restored.design_id == sample_carrier.design_id
        assert restored.composite_score == pytest.approx(sample_carrier.composite_score)
        assert restored.is_pareto_optimal == sample_carrier.is_pareto_optimal
        assert restored.rank == sample_carrier.rank


# ─── Session save/load tests ──────────────────────────────────────────────────

class TestSaveLoadSession:
    def test_save_creates_json_file(
        self, session_dir, sample_geo, sample_flow, sample_buoy, sample_carrier
    ):
        results = [{"design_id": "test_PLA", "filename": "test.stl",
                     "material": "PLA", "geo": sample_geo,
                     "flow": sample_flow, "buoy": sample_buoy,
                     "carrier_score": sample_carrier}]
        path = save_session("test_session", results, [sample_carrier], {})
        assert path.endswith(".json")
        assert os.path.exists(path)

    def test_saved_file_is_valid_json(
        self, session_dir, sample_geo, sample_flow, sample_buoy, sample_carrier
    ):
        results = [{"design_id": "x", "filename": "x.stl", "material": "PLA",
                     "geo": sample_geo, "flow": sample_flow, "buoy": sample_buoy,
                     "carrier_score": sample_carrier}]
        path = save_session("test", results, [sample_carrier], {})
        with open(path) as f:
            data = json.load(f)
        assert data["schema_version"] == SCHEMA_VERSION

    def test_load_restores_carriers(
        self, session_dir, sample_geo, sample_flow, sample_buoy, sample_carrier
    ):
        results = [{"design_id": "test_PLA", "filename": "test.stl",
                     "material": "PLA", "geo": sample_geo,
                     "flow": sample_flow, "buoy": sample_buoy,
                     "carrier_score": sample_carrier}]
        path = save_session("session", results, [sample_carrier], {})
        loaded = load_session(path)
        assert len(loaded["all_carriers"]) == 1
        c = loaded["all_carriers"][0]
        assert c.design_id == "test_PLA"
        assert c.composite_score == pytest.approx(0.72)

    def test_load_restores_results(
        self, session_dir, sample_geo, sample_flow, sample_buoy, sample_carrier
    ):
        results = [{"design_id": "test_PLA", "filename": "test.stl",
                     "material": "PLA", "geo": sample_geo,
                     "flow": sample_flow, "buoy": sample_buoy,
                     "carrier_score": sample_carrier}]
        path = save_session("session", results, [sample_carrier], {})
        loaded = load_session(path)
        assert len(loaded["results"]) == 1
        geo = loaded["results"][0]["geo"]
        assert geo.surface_area == pytest.approx(5000.0)


class TestListSessions:
    def test_empty_dir_returns_empty(self, session_dir):
        assert list_sessions() == []

    def test_saved_session_appears_in_list(
        self, session_dir, sample_geo, sample_flow, sample_buoy, sample_carrier
    ):
        results = [{"design_id": "x", "filename": "x.stl", "material": "PLA",
                     "geo": sample_geo, "flow": sample_flow, "buoy": sample_buoy,
                     "carrier_score": sample_carrier}]
        save_session("my_session", results, [sample_carrier], {})
        sessions = list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_name"] == "my_session"


class TestDeleteSession:
    def test_delete_removes_file(
        self, session_dir, sample_geo, sample_flow, sample_buoy, sample_carrier
    ):
        results = [{"design_id": "x", "filename": "x.stl", "material": "PLA",
                     "geo": sample_geo, "flow": sample_flow, "buoy": sample_buoy,
                     "carrier_score": sample_carrier}]
        path = save_session("to_delete", results, [sample_carrier], {})
        assert os.path.exists(path)
        result = delete_session(path)
        assert result is True
        assert not os.path.exists(path)


class TestExportCsv:
    def test_export_returns_string(
        self, sample_geo, sample_flow, sample_buoy, sample_carrier
    ):
        results = [{"design_id": "test_PLA", "filename": "test.stl",
                     "material": "PLA", "geo": sample_geo,
                     "flow": sample_flow, "buoy": sample_buoy,
                     "carrier_score": sample_carrier}]
        csv = export_session_csv([sample_carrier], results)
        assert isinstance(csv, str)
        assert "test_PLA" in csv
        assert "PLA" in csv
