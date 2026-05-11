"""
Unit tests for core/geometry.py

Uses a programmatically generated minimal STL (a cube) so no external
fixture files are required.
"""

import os
import struct
import tempfile

import numpy as np
import pytest

from core.geometry import (
    GeometryMetrics,
    analyze_stl,
    compute_hydraulic_diameter,
    get_metrics_summary,
    load_and_validate_stl,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _write_cube_stl(path: str, side: float = 10.0) -> None:
    """Write a binary STL representing a unit cube (12 triangles)."""
    s = side
    # 8 vertices of the cube
    triangles = [
        # Bottom (-Z)
        ([0,0,0],[s,0,0],[s,s,0]), ([0,0,0],[s,s,0],[0,s,0]),
        # Top (+Z)
        ([0,0,s],[s,s,s],[s,0,s]), ([0,0,s],[0,s,s],[s,s,s]),
        # Front (-Y)
        ([0,0,0],[s,0,s],[s,0,0]), ([0,0,0],[0,0,s],[s,0,s]),
        # Back (+Y)
        ([0,s,0],[s,s,0],[s,s,s]), ([0,s,0],[s,s,s],[0,s,s]),
        # Left (-X)
        ([0,0,0],[0,s,0],[0,s,s]), ([0,0,0],[0,s,s],[0,0,s]),
        # Right (+X)
        ([s,0,0],[s,s,s],[s,s,0]), ([s,0,0],[s,0,s],[s,s,s]),
    ]
    with open(path, "wb") as f:
        f.write(b"\x00" * 80)              # header
        f.write(struct.pack("<I", len(triangles)))
        for v0, v1, v2 in triangles:
            # normal (zeros — trimesh will fix)
            f.write(struct.pack("<fff", 0.0, 0.0, 0.0))
            for v in (v0, v1, v2):
                f.write(struct.pack("<fff", *v))
            f.write(struct.pack("<H", 0))  # attribute byte count


@pytest.fixture
def cube_stl(tmp_path):
    """Fixture: path to a 10mm cube STL."""
    path = str(tmp_path / "cube.stl")
    _write_cube_stl(path, side=10.0)
    return path


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestLoadAndValidate:
    def test_loads_valid_stl(self, cube_stl):
        mesh, issues = load_and_validate_stl(cube_stl)
        assert mesh is not None
        assert len(mesh.faces) == 12

    def test_raises_on_missing_file(self):
        with pytest.raises((ValueError, Exception)):
            load_and_validate_stl("/nonexistent/path/fake.stl")


class TestAnalyzeStl:
    def test_returns_geometry_metrics(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        assert isinstance(metrics, GeometryMetrics)

    def test_filename_uses_basename(self, cube_stl):
        """Regression: must use os.path.basename — not a slash split."""
        metrics = analyze_stl(cube_stl)
        assert metrics.filename == "cube.stl"
        assert "/" not in metrics.filename
        assert "\\" not in metrics.filename

    def test_volume_positive(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        assert metrics.volume > 0

    def test_surface_area_positive(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        assert metrics.surface_area > 0

    def test_sav_ratio_positive(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        assert metrics.sav_ratio > 0

    def test_porosity_in_range(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        # A solid cube has zero porosity (or very close to it)
        assert 0.0 <= metrics.porosity < 0.05

    def test_cube_dimensions_approx(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        for dim in (metrics.dim_x, metrics.dim_y, metrics.dim_z):
            assert abs(dim - 10.0) < 0.5, f"Unexpected dimension: {dim}"

    def test_cube_volume_approx(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        assert abs(metrics.volume - 1000.0) < 5.0, f"Volume {metrics.volume} != ~1000 mm³"


class TestHydraulicDiameter:
    def test_zero_porosity_returns_zero(self, cube_stl):
        import trimesh
        mesh = trimesh.load(cube_stl, force="mesh")
        assert compute_hydraulic_diameter(mesh, 0.0) == 0.0

    def test_positive_for_valid_inputs(self, cube_stl):
        import trimesh
        mesh = trimesh.load(cube_stl, force="mesh")
        dh = compute_hydraulic_diameter(mesh, 0.5)
        assert dh >= 0.0


class TestGetMetricsSummary:
    def test_returns_dict_with_expected_keys(self, cube_stl):
        metrics = analyze_stl(cube_stl)
        summary = get_metrics_summary(metrics)
        for key in ("Filename", "Surface Area (mm²)", "Volume (mm³)",
                    "SA/V Ratio (mm⁻¹)", "Porosity", "Watertight"):
            assert key in summary
