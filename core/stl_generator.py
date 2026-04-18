"""
Parametric STL Generator
Creates optimised 3D biofilm carrier geometries based on target performance parameters.
Supports: Cylindrical lattice, Honeycomb, Cross-flow, Gyroid-inspired, and Hybrid designs.

All dimensions in millimetres. Output is binary STL.
"""

import numpy as np
from stl import mesh as stl_mesh
from dataclasses import dataclass
from typing import Tuple, List
import tempfile
import os


@dataclass
class CarrierParams:
    """Geometric parameters for a parametric carrier design."""
    # Outer envelope
    outer_diameter: float = 25.0     # mm
    height: float = 12.0             # mm
    wall_thickness: float = 1.2      # mm

    # Internal structure
    num_fins: int = 8                 # radial fins count
    fin_thickness: float = 0.8       # mm
    num_rings: int = 2                # concentric rings
    ring_gap: float = 3.0            # mm between rings

    # Outer protrusions (increase surface area)
    num_spikes: int = 12             # outer surface protrusions
    spike_height: float = 2.0        # mm
    spike_base: float = 1.5          # mm

    # Design type
    design_type: str = "cross_flow"  # cross_flow | honeycomb | lattice | hybrid

    # Mesh resolution
    angular_segments: int = 64       # smoothness of curves


def _rotation_matrix_z(angle_rad: float) -> np.ndarray:
    """3D rotation matrix around Z axis."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _cylinder_triangles(
    r_inner: float, r_outer: float,
    z_bottom: float, z_top: float,
    segments: int, closed_bottom: bool = True, closed_top: bool = True
) -> List[np.ndarray]:
    """
    Generate triangles for a hollow cylinder (annular section).
    Returns list of (3,3) triangle arrays.
    """
    triangles = []
    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)

    for i in range(segments):
        a0, a1 = angles[i], angles[(i + 1) % segments]

        # Outer wall
        p0 = np.array([r_outer * np.cos(a0), r_outer * np.sin(a0), z_bottom])
        p1 = np.array([r_outer * np.cos(a1), r_outer * np.sin(a1), z_bottom])
        p2 = np.array([r_outer * np.cos(a0), r_outer * np.sin(a0), z_top])
        p3 = np.array([r_outer * np.cos(a1), r_outer * np.sin(a1), z_top])
        triangles.append(np.array([p0, p1, p2]))
        triangles.append(np.array([p1, p3, p2]))

        if r_inner > 0:
            # Inner wall (reversed winding)
            q0 = np.array([r_inner * np.cos(a0), r_inner * np.sin(a0), z_bottom])
            q1 = np.array([r_inner * np.cos(a1), r_inner * np.sin(a1), z_bottom])
            q2 = np.array([r_inner * np.cos(a0), r_inner * np.sin(a0), z_top])
            q3 = np.array([r_inner * np.cos(a1), r_inner * np.sin(a1), z_top])
            triangles.append(np.array([q0, q2, q1]))
            triangles.append(np.array([q1, q2, q3]))

        # Top and bottom annular caps
        if closed_top:
            if r_inner > 0:
                t0 = np.array([r_inner * np.cos(a0), r_inner * np.sin(a0), z_top])
                t1 = np.array([r_inner * np.cos(a1), r_inner * np.sin(a1), z_top])
                t2 = np.array([r_outer * np.cos(a0), r_outer * np.sin(a0), z_top])
                t3 = np.array([r_outer * np.cos(a1), r_outer * np.sin(a1), z_top])
                triangles.append(np.array([t0, t2, t1]))
                triangles.append(np.array([t1, t2, t3]))
            else:
                # Solid disk
                centre = np.array([0, 0, z_top])
                p_a = np.array([r_outer * np.cos(a0), r_outer * np.sin(a0), z_top])
                p_b = np.array([r_outer * np.cos(a1), r_outer * np.sin(a1), z_top])
                triangles.append(np.array([centre, p_a, p_b]))

        if closed_bottom:
            if r_inner > 0:
                b0 = np.array([r_inner * np.cos(a0), r_inner * np.sin(a0), z_bottom])
                b1 = np.array([r_inner * np.cos(a1), r_inner * np.sin(a1), z_bottom])
                b2 = np.array([r_outer * np.cos(a0), r_outer * np.sin(a0), z_bottom])
                b3 = np.array([r_outer * np.cos(a1), r_outer * np.sin(a1), z_bottom])
                triangles.append(np.array([b0, b1, b2]))
                triangles.append(np.array([b1, b3, b2]))
            else:
                centre = np.array([0, 0, z_bottom])
                p_a = np.array([r_outer * np.cos(a0), r_outer * np.sin(a0), z_bottom])
                p_b = np.array([r_outer * np.cos(a1), r_outer * np.sin(a1), z_bottom])
                triangles.append(np.array([centre, p_b, p_a]))

    return triangles


def _fin_triangles(
    r_start: float, r_end: float,
    angle: float, thickness: float,
    z_bottom: float, z_top: float
) -> List[np.ndarray]:
    """Generate triangles for a single radial fin at a given angle."""
    half_t = thickness / 2.0
    perp_angle = angle + np.pi / 2

    triangles = []
    offset = np.array([np.cos(perp_angle) * half_t,
                        np.sin(perp_angle) * half_t, 0])

    for sign in [1, -1]:
        o = offset * sign
        reverse = sign == -1

        p0 = np.array([r_start * np.cos(angle), r_start * np.sin(angle), z_bottom]) + o
        p1 = np.array([r_end * np.cos(angle),   r_end * np.sin(angle),   z_bottom]) + o
        p2 = np.array([r_start * np.cos(angle), r_start * np.sin(angle), z_top])    + o
        p3 = np.array([r_end * np.cos(angle),   r_end * np.sin(angle),   z_top])    + o

        if reverse:
            triangles.append(np.array([p0, p2, p1]))
            triangles.append(np.array([p1, p2, p3]))
        else:
            triangles.append(np.array([p0, p1, p2]))
            triangles.append(np.array([p1, p3, p2]))

    # Top and bottom face of fin
    for z, flip in [(z_bottom, True), (z_top, False)]:
        o_pos = offset
        o_neg = -offset
        p_inner_pos = np.array([r_start * np.cos(angle), r_start * np.sin(angle), z]) + o_pos
        p_inner_neg = np.array([r_start * np.cos(angle), r_start * np.sin(angle), z]) + o_neg
        p_outer_pos = np.array([r_end * np.cos(angle),   r_end * np.sin(angle),   z]) + o_pos
        p_outer_neg = np.array([r_end * np.cos(angle),   r_end * np.sin(angle),   z]) + o_neg
        if flip:
            triangles.append(np.array([p_inner_neg, p_inner_pos, p_outer_neg]))
            triangles.append(np.array([p_inner_pos, p_outer_pos, p_outer_neg]))
        else:
            triangles.append(np.array([p_inner_pos, p_inner_neg, p_outer_pos]))
            triangles.append(np.array([p_inner_neg, p_outer_neg, p_outer_pos]))

    return triangles


def _spike_triangles(
    base_x: float, base_y: float, base_z_low: float, base_z_high: float,
    spike_height: float, spike_base: float, outward_angle: float
) -> List[np.ndarray]:
    """Generate a simple pyramidal spike pointing outward."""
    triangles = []
    tip_x = base_x + np.cos(outward_angle) * spike_height
    tip_y = base_y + np.sin(outward_angle) * spike_height
    tip_z = (base_z_low + base_z_high) / 2

    tip = np.array([tip_x, tip_y, tip_z])
    perp = outward_angle + np.pi / 2
    h = spike_base / 2

    corners = [
        np.array([base_x + np.cos(perp) * h, base_y + np.sin(perp) * h, base_z_low]),
        np.array([base_x - np.cos(perp) * h, base_y - np.sin(perp) * h, base_z_low]),
        np.array([base_x - np.cos(perp) * h, base_y - np.sin(perp) * h, base_z_high]),
        np.array([base_x + np.cos(perp) * h, base_y + np.sin(perp) * h, base_z_high]),
    ]

    # Four faces of pyramid
    for i in range(4):
        triangles.append(np.array([corners[i], corners[(i + 1) % 4], tip]))

    # Base quad
    triangles.append(np.array([corners[0], corners[1], corners[2]]))
    triangles.append(np.array([corners[0], corners[2], corners[3]]))

    return triangles


def generate_cross_flow_carrier(params: CarrierParams) -> List[np.ndarray]:
    """
    Generate a cross-flow biofilm carrier:
    - Outer cylindrical shell with spikes
    - Multiple concentric rings
    - Radial fins connecting rings
    """
    triangles = []
    r = params.outer_diameter / 2
    h = params.height
    wt = params.wall_thickness
    segs = params.angular_segments

    # Outer shell
    triangles += _cylinder_triangles(r - wt, r, 0, h, segs,
                                      closed_bottom=True, closed_top=True)

    # Concentric rings
    ring_radii = np.linspace(r - wt - params.ring_gap,
                              params.ring_gap, params.num_rings)
    for rr in ring_radii:
        if rr > wt:
            triangles += _cylinder_triangles(
                rr - wt / 2, rr + wt / 2, 0, h, max(16, segs // 4),
                closed_bottom=True, closed_top=True)

    # Radial fins
    fin_angles = np.linspace(0, 2 * np.pi, params.num_fins, endpoint=False)
    for angle in fin_angles:
        r_inner_fin = ring_radii[-1] + wt / 2 if len(ring_radii) > 0 else wt
        r_outer_fin = r - wt
        if r_outer_fin > r_inner_fin:
            triangles += _fin_triangles(
                r_inner_fin, r_outer_fin, angle,
                params.fin_thickness, 0, h)

    # Outer spikes
    spike_angles = np.linspace(0, 2 * np.pi, params.num_spikes, endpoint=False)
    for angle in spike_angles:
        bx = r * np.cos(angle)
        by = r * np.sin(angle)
        triangles += _spike_triangles(
            bx, by, h * 0.2, h * 0.8,
            params.spike_height, params.spike_base, angle)

    return triangles


def generate_honeycomb_carrier(params: CarrierParams) -> List[np.ndarray]:
    """
    Generate a honeycomb-inspired biofilm carrier.
    Hexagonal cells arranged in a cylindrical envelope.
    """
    triangles = []
    r = params.outer_diameter / 2
    h = params.height
    wt = params.wall_thickness
    segs = params.angular_segments

    # Outer shell
    triangles += _cylinder_triangles(r - wt, r, 0, h, segs,
                                      closed_bottom=True, closed_top=True)

    # Hexagonal internal walls approximated as radial + tangential fins
    cell_size = params.ring_gap * 1.5
    n_radial = max(3, params.num_fins)
    n_tangential = max(3, params.num_rings + 1)

    radial_angles = np.linspace(0, 2 * np.pi, n_radial, endpoint=False)
    for angle in radial_angles:
        triangles += _fin_triangles(
            wt, r - wt, angle, params.fin_thickness * 0.8, 0, h)

    ring_radii = np.linspace(cell_size, r - wt - wt, n_tangential)
    for rr in ring_radii:
        if rr > wt:
            ring_segs = max(12, int(2 * np.pi * rr / cell_size))
            triangles += _cylinder_triangles(
                rr - wt / 3, rr + wt / 3, 0, h, ring_segs,
                closed_bottom=True, closed_top=True)

    # Spikes
    spike_angles = np.linspace(0, 2 * np.pi, params.num_spikes, endpoint=False)
    for angle in spike_angles:
        bx = r * np.cos(angle)
        by = r * np.sin(angle)
        triangles += _spike_triangles(
            bx, by, h * 0.15, h * 0.85,
            params.spike_height * 1.2, params.spike_base, angle)

    return triangles


def generate_lattice_carrier(params: CarrierParams) -> List[np.ndarray]:
    """
    Generate a lattice-type biofilm carrier with diagonal struts
    for enhanced surface area and structural strength.
    """
    triangles = []
    r = params.outer_diameter / 2
    h = params.height
    wt = params.wall_thickness
    segs = params.angular_segments

    # Outer shell
    triangles += _cylinder_triangles(r - wt, r, 0, h, segs,
                                      closed_bottom=True, closed_top=True)

    # Inner core cylinder
    core_r = r * 0.25
    if core_r > wt:
        triangles += _cylinder_triangles(
            core_r - wt / 2, core_r + wt / 2, 0, h, 24,
            closed_bottom=True, closed_top=True)

    # Upper and lower horizontal rings
    mid_r = r * 0.6
    for z_pos in [h * 0.33, h * 0.66]:
        triangles += _cylinder_triangles(
            mid_r - wt / 2, mid_r + wt / 2,
            z_pos - wt / 2, z_pos + wt / 2, 32,
            closed_bottom=True, closed_top=True)

    # Diagonal struts (alternating angles)
    n_struts = params.num_fins
    strut_angles = np.linspace(0, 2 * np.pi, n_struts, endpoint=False)
    for i, angle in enumerate(strut_angles):
        # Alternate: struts go from core-bottom to mid_r-top and vice versa
        if i % 2 == 0:
            triangles += _fin_triangles(
                core_r + wt / 2, mid_r, angle,
                params.fin_thickness, 0, h * 0.5)
            triangles += _fin_triangles(
                mid_r, r - wt, angle + np.pi / n_struts,
                params.fin_thickness, h * 0.5, h)
        else:
            triangles += _fin_triangles(
                core_r + wt / 2, mid_r, angle,
                params.fin_thickness, h * 0.5, h)
            triangles += _fin_triangles(
                mid_r, r - wt, angle + np.pi / n_struts,
                params.fin_thickness, 0, h * 0.5)

    # Spikes
    spike_angles = np.linspace(0, 2 * np.pi, params.num_spikes, endpoint=False)
    for angle in spike_angles:
        bx = r * np.cos(angle)
        by = r * np.sin(angle)
        triangles += _spike_triangles(
            bx, by, h * 0.1, h * 0.9,
            params.spike_height, params.spike_base, angle)

    return triangles


def generate_hybrid_carrier(params: CarrierParams) -> List[np.ndarray]:
    """
    Hybrid design combining cross-flow fins with lattice struts.
    Targets maximum SA/V while maintaining good porosity.
    """
    triangles = []
    r = params.outer_diameter / 2
    h = params.height
    wt = params.wall_thickness
    segs = params.angular_segments

    # Outer shell
    triangles += _cylinder_triangles(r - wt, r, 0, h, segs,
                                      closed_bottom=True, closed_top=True)

    # Two concentric rings
    for frac in [0.35, 0.65]:
        rr = r * frac
        if rr > wt * 2:
            triangles += _cylinder_triangles(
                rr - wt * 0.4, rr + wt * 0.4, 0, h,
                max(16, int(segs * frac)),
                closed_bottom=True, closed_top=True)

    # Dense radial fins in lower half
    fin_angles_lower = np.linspace(0, 2 * np.pi, params.num_fins, endpoint=False)
    for angle in fin_angles_lower:
        triangles += _fin_triangles(
            wt, r - wt, angle, params.fin_thickness * 0.7, 0, h * 0.5)

    # Offset fins in upper half for enhanced turbulence
    fin_angles_upper = np.linspace(
        np.pi / params.num_fins, 2 * np.pi + np.pi / params.num_fins,
        params.num_fins, endpoint=False)
    for angle in fin_angles_upper:
        triangles += _fin_triangles(
            wt, r - wt, angle, params.fin_thickness * 0.7, h * 0.5, h)

    # Spikes - denser for hybrid
    n_spikes = params.num_spikes + 4
    spike_angles = np.linspace(0, 2 * np.pi, n_spikes, endpoint=False)
    for angle in spike_angles:
        bx = r * np.cos(angle)
        by = r * np.sin(angle)
        triangles += _spike_triangles(
            bx, by, h * 0.1, h * 0.9,
            params.spike_height * 0.8, params.spike_base * 0.9, angle)

    return triangles


def triangles_to_stl_mesh(triangles: List[np.ndarray]) -> stl_mesh.Mesh:
    """Convert list of triangle arrays to numpy-stl Mesh object."""
    n = len(triangles)
    carrier_mesh = stl_mesh.Mesh(np.zeros(n, dtype=stl_mesh.Mesh.dtype))
    for i, tri in enumerate(triangles):
        carrier_mesh.vectors[i] = tri
    return carrier_mesh


def generate_carrier_stl(
    params: CarrierParams,
    output_path: str = None
) -> Tuple[str, stl_mesh.Mesh]:
    """
    Main generation function. Creates an STL file for a parametric carrier.
    
    Returns (output_path, mesh) tuple.
    If output_path is None, a temp file is created.
    """
    generators = {
        "cross_flow": generate_cross_flow_carrier,
        "honeycomb": generate_honeycomb_carrier,
        "lattice": generate_lattice_carrier,
        "hybrid": generate_hybrid_carrier,
    }

    if params.design_type not in generators:
        raise ValueError(f"Unknown design type: {params.design_type}. "
                         f"Choose from: {list(generators.keys())}")

    triangles = generators[params.design_type](params)

    if not triangles:
        raise ValueError("Generator produced no triangles.")

    carrier_mesh = triangles_to_stl_mesh(triangles)

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".stl",
            prefix=f"cdmo_{params.design_type}_")
        output_path = tmp.name
        tmp.close()

    carrier_mesh.save(output_path)
    return output_path, carrier_mesh


def params_from_optimization_suggestion(
    current_sav: float,
    current_porosity: float,
    target_sav_increase: float = 0.15,
    target_porosity_increase: float = 0.05,
    base_params: CarrierParams = None
) -> CarrierParams:
    """
    Generate improved CarrierParams based on optimization suggestions.
    Adjusts fin count and ring gap to hit target SA/V and porosity improvements.
    """
    p = base_params or CarrierParams()

    # Increase SA/V -> add more fins and spikes
    if target_sav_increase > 0:
        extra_fins = int(target_sav_increase / 0.05)
        p.num_fins = min(20, p.num_fins + extra_fins)
        p.num_spikes = min(24, p.num_spikes + extra_fins)
        p.spike_height = min(4.0, p.spike_height + target_sav_increase * 5)

    # Increase porosity -> widen gaps, reduce wall thickness
    if target_porosity_increase > 0:
        p.wall_thickness = max(0.6, p.wall_thickness - target_porosity_increase * 4)
        p.ring_gap = min(8.0, p.ring_gap + target_porosity_increase * 10)
        p.num_rings = max(1, p.num_rings - 1)

    return p
