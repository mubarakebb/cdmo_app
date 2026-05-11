"""
Geometry Analysis Engine
Processes STL files to extract all geometric performance metrics
for biofilm carrier evaluation.
"""

import os

import numpy as np
import trimesh
from dataclasses import dataclass, field
from typing import Optional
import warnings


@dataclass
class GeometryMetrics:
    """All geometric metrics extracted from an STL file."""
    # Identity
    filename: str = ""
    
    # Mesh health
    is_watertight: bool = False
    is_winding_consistent: bool = False
    euler_number: int = 0
    num_triangles: int = 0
    num_vertices: int = 0
    
    # Raw dimensions (mm)
    dim_x: float = 0.0
    dim_y: float = 0.0
    dim_z: float = 0.0
    
    # Core geometric metrics
    surface_area: float = 0.0        # mm²
    volume: float = 0.0              # mm³
    bounding_box_volume: float = 0.0 # mm³
    porosity: float = 0.0            # void fraction 0-1
    sav_ratio: float = 0.0           # mm⁻¹ (Surface Area to Volume ratio)
    
    # Derived metrics
    hydraulic_diameter: float = 0.0  # mm - characteristic length for flow
    specific_surface_area: float = 0.0  # m²/m³ - normalized for reactor design
    
    # Mesh repair info
    was_repaired: bool = False
    repair_notes: str = ""


def load_and_validate_stl(filepath: str) -> tuple[trimesh.Trimesh, list]:
    """
    Load STL file and validate mesh quality.
    Returns mesh and list of any issues found.
    """
    issues = []
    
    try:
        mesh = trimesh.load(filepath, force='mesh')
    except Exception as e:
        raise ValueError(f"Failed to load STL file: {e}")
    
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("File did not load as a valid triangle mesh.")
    
    if len(mesh.faces) == 0:
        raise ValueError("Mesh has no faces — file may be empty or corrupt.")
    
    if not mesh.is_watertight:
        issues.append("Mesh is not watertight (has holes). Attempting repair.")
    
    if not mesh.is_winding_consistent:
        issues.append("Inconsistent face winding detected. Fixing normals.")
        mesh.fix_normals()
    
    return mesh, issues


def repair_mesh(mesh: trimesh.Trimesh) -> tuple[trimesh.Trimesh, str]:
    """
    Attempt to repair common mesh issues.
    Returns repaired mesh and repair notes.
    """
    notes = []
    
    # Fix winding/normals
    trimesh.repair.fix_normals(mesh)
    notes.append("Normals fixed.")
    
    # Fill holes if present
    trimesh.repair.fill_holes(mesh)
    if mesh.is_watertight:
        notes.append("Holes filled successfully.")
    else:
        notes.append("Some holes remain — porosity calculation uses bounding box method.")
    
    return mesh, " ".join(notes)


def compute_hydraulic_diameter(mesh: trimesh.Trimesh, porosity: float) -> float:
    """
    Compute hydraulic diameter using the packed bed model.
    Dh = (4 * porosity) / (surface_area_per_unit_volume * (1 - porosity))
    
    This is used in empirical flow correlations (Ergun equation etc.)
    Returns hydraulic diameter in mm.
    """
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    bb_volume_m3 = (dims[0] * dims[1] * dims[2]) * 1e-9  # convert mm³ to m³
    surface_area_m2 = mesh.area * 1e-6  # convert mm² to m²
    
    # Specific surface area (m²/m³)
    a_s = surface_area_m2 / bb_volume_m3
    
    if a_s == 0 or porosity >= 1.0:
        return 0.0
    
    # Hydraulic diameter (m) -> convert to mm
    dh_m = (4 * porosity) / (a_s * (1 - porosity))
    return dh_m * 1000  # return in mm


def analyze_stl(filepath: str, unit: str = "mm") -> GeometryMetrics:
    """
    Main analysis function. Loads STL, validates, repairs if needed,
    and computes all geometric performance metrics.
    
    Parameters:
        filepath: Path to STL file
        unit: Unit system of the STL file ('mm' or 'm')
    
    Returns:
        GeometryMetrics dataclass with all computed values
    """
    metrics = GeometryMetrics()
    metrics.filename = os.path.basename(filepath)
    
    # Load and validate
    mesh, issues = load_and_validate_stl(filepath)
    
    # Repair if needed
    if not mesh.is_watertight or not mesh.is_winding_consistent:
        mesh, repair_notes = repair_mesh(mesh)
        metrics.was_repaired = True
        metrics.repair_notes = repair_notes
    
    # Unit scaling — Blender exports in mm by default
    scale_factor = 1.0
    if unit == "m":
        scale_factor = 1000.0  # convert m to mm
        mesh.apply_scale(scale_factor)
    
    # Mesh health
    metrics.is_watertight = mesh.is_watertight
    metrics.is_winding_consistent = mesh.is_winding_consistent
    metrics.euler_number = mesh.euler_number
    metrics.num_triangles = len(mesh.faces)
    metrics.num_vertices = len(mesh.vertices)
    
    # Bounding box dimensions (mm)
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    metrics.dim_x = round(float(dims[0]), 4)
    metrics.dim_y = round(float(dims[1]), 4)
    metrics.dim_z = round(float(dims[2]), 4)
    
    # Core geometric metrics
    metrics.surface_area = round(float(mesh.area), 4)           # mm²
    metrics.volume = round(abs(float(mesh.volume)), 4)          # mm³
    metrics.bounding_box_volume = round(float(
        dims[0] * dims[1] * dims[2]), 4)                        # mm³
    
    # Porosity: fraction of bounding box that is void
    if metrics.bounding_box_volume > 0:
        metrics.porosity = round(
            1.0 - (metrics.volume / metrics.bounding_box_volume), 4)
    
    # SA/V ratio (mm⁻¹)
    if metrics.volume > 0:
        metrics.sav_ratio = round(metrics.surface_area / metrics.volume, 4)
    
    # Specific surface area (m²/m³) — normalized for reactor engineering
    bb_vol_m3 = metrics.bounding_box_volume * 1e-9
    sa_m2 = metrics.surface_area * 1e-6
    if bb_vol_m3 > 0:
        metrics.specific_surface_area = round(sa_m2 / bb_vol_m3, 2)
    
    # Hydraulic diameter (mm)
    metrics.hydraulic_diameter = round(
        compute_hydraulic_diameter(mesh, metrics.porosity), 4)
    
    return metrics


def get_metrics_summary(metrics: GeometryMetrics) -> dict:
    """
    Return a clean dictionary of the most important metrics
    for display and scoring purposes.
    """
    return {
        "Filename": metrics.filename,
        "Dimensions (mm)": f"{metrics.dim_x:.1f} × {metrics.dim_y:.1f} × {metrics.dim_z:.1f}",
        "Surface Area (mm²)": metrics.surface_area,
        "Volume (mm³)": metrics.volume,
        "SA/V Ratio (mm⁻¹)": metrics.sav_ratio,
        "Porosity": metrics.porosity,
        "Specific Surface Area (m²/m³)": metrics.specific_surface_area,
        "Hydraulic Diameter (mm)": metrics.hydraulic_diameter,
        "Triangles": metrics.num_triangles,
        "Watertight": metrics.is_watertight,
    }
