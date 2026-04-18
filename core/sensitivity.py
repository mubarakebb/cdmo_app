"""
Sensitivity Analysis Module
Quantifies how changes in geometric parameters affect each performance objective.

This produces publishable findings: parameter importance rankings,
sensitivity curves, and interaction effects.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Callable
from core.geometry import GeometryMetrics
from core.flow_analysis import compute_flow_metrics
from core.buoyancy import compute_buoyancy


@dataclass
class SensitivityResult:
    """Sensitivity analysis result for one parameter vs one objective."""
    parameter_name: str = ""
    objective_name: str = ""
    parameter_values: List[float] = field(default_factory=list)
    objective_values: List[float] = field(default_factory=list)
    sensitivity_index: float = 0.0     # normalised range: (max-min)/mean
    direction: str = ""                # "positive", "negative", "non-monotonic"
    r_squared: float = 0.0            # linearity of relationship


@dataclass
class SensitivityReport:
    """Full sensitivity analysis report for a carrier design."""
    base_filename: str = ""
    results: List[SensitivityResult] = field(default_factory=list)
    parameter_importance: Dict[str, float] = field(default_factory=dict)
    most_influential_parameter: str = ""
    most_sensitive_objective: str = ""


def _make_synthetic_geo(
    base_geo: GeometryMetrics,
    sav_ratio: float = None,
    porosity: float = None,
    surface_area: float = None,
    volume: float = None,
    hydraulic_diameter: float = None,
    specific_surface_area: float = None,
) -> GeometryMetrics:
    """Create a synthetic GeometryMetrics by varying individual parameters."""
    import copy
    geo = copy.deepcopy(base_geo)

    if sav_ratio is not None:
        geo.sav_ratio = sav_ratio
        # Adjust surface area to match new SA/V while keeping volume
        geo.surface_area = sav_ratio * geo.volume

    if porosity is not None:
        geo.porosity = porosity
        # Recompute volume from bounding box and new porosity
        geo.volume = geo.bounding_box_volume * (1 - porosity)
        geo.sav_ratio = geo.surface_area / geo.volume if geo.volume > 0 else 0

    if surface_area is not None:
        geo.surface_area = surface_area
        geo.sav_ratio = surface_area / geo.volume if geo.volume > 0 else 0

    if hydraulic_diameter is not None:
        geo.hydraulic_diameter = hydraulic_diameter

    if specific_surface_area is not None:
        geo.specific_surface_area = specific_surface_area

    return geo


def _compute_objectives(
    geo: GeometryMetrics,
    material: str,
    fluid_density: float,
    fluid_viscosity: float,
    flow_velocity: float
) -> Dict[str, float]:
    """Compute all objectives for a given geometry configuration."""
    from core.materials import MATERIALS

    flow = compute_flow_metrics(
        geo, flow_velocity, fluid_density, fluid_viscosity)
    buoy = compute_buoyancy(geo, material, fluid_density)
    mat = MATERIALS[material]

    return {
        "SA/V Ratio (mm⁻¹)": geo.sav_ratio,
        "Porosity": geo.porosity,
        "Flow Efficiency": flow.flow_efficiency_score,
        "Buoyancy Score": buoy.buoyancy_score,
        "Pressure Drop (Pa/m)": flow.pressure_drop_per_m,
        "Mass Transfer (m/s)": flow.mass_transfer_coefficient * 1e6,  # scale to µm/s
        "Clogging Risk Score": flow.clogging_risk_score,
        "Specific SA (m²/m³)": geo.specific_surface_area,
    }


def _sensitivity_index(values: List[float]) -> float:
    """Normalised sensitivity: (max - min) / mean."""
    arr = np.array(values)
    mean = np.mean(arr)
    if mean == 0:
        return 0.0
    return float((arr.max() - arr.min()) / abs(mean))


def _r_squared(x_vals: List[float], y_vals: List[float]) -> float:
    """R² of linear fit — measures linearity of the relationship."""
    x = np.array(x_vals)
    y = np.array(y_vals)
    if len(x) < 3 or np.std(y) == 0:
        return 1.0
    coeffs = np.polyfit(x, y, 1)
    y_fit = np.polyval(coeffs, x)
    ss_res = np.sum((y - y_fit) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else 1.0


def _direction(values: List[float]) -> str:
    """Determine if relationship is monotonically increasing, decreasing, or non-monotonic."""
    diffs = np.diff(values)
    if np.all(diffs >= -1e-8):
        return "positive"
    elif np.all(diffs <= 1e-8):
        return "negative"
    else:
        return "non-monotonic"


def run_sensitivity_analysis(
    base_geo: GeometryMetrics,
    material: str = "PLA",
    fluid_density: float = 1015.0,
    fluid_viscosity: float = 0.003,
    flow_velocity: float = 0.01,
    n_points: int = 20
) -> SensitivityReport:
    """
    Run full one-at-a-time (OAT) sensitivity analysis.
    Varies each geometric parameter over its feasible range while
    holding all others fixed at baseline.
    
    Returns a SensitivityReport with curves and importance rankings.
    """
    report = SensitivityReport(base_filename=base_geo.filename)

    # Parameter ranges — physically meaningful bounds for biofilm carriers
    parameter_ranges = {
        "SA/V Ratio (mm⁻¹)": np.linspace(
            max(0.2, base_geo.sav_ratio * 0.4),
            base_geo.sav_ratio * 2.0, n_points),

        "Porosity": np.linspace(0.30, 0.92, n_points),

        "Hydraulic Diameter (mm)": np.linspace(
            max(1.0, base_geo.hydraulic_diameter * 0.2),
            base_geo.hydraulic_diameter * 3.0, n_points),

        "Specific SA (m²/m³)": np.linspace(
            max(50, base_geo.specific_surface_area * 0.3),
            base_geo.specific_surface_area * 2.5, n_points),
    }

    # Map parameter names to geometry modification functions
    param_modifiers = {
        "SA/V Ratio (mm⁻¹)": lambda geo, v: _make_synthetic_geo(geo, sav_ratio=v),
        "Porosity":           lambda geo, v: _make_synthetic_geo(geo, porosity=v),
        "Hydraulic Diameter (mm)": lambda geo, v: _make_synthetic_geo(
            geo, hydraulic_diameter=v),
        "Specific SA (m²/m³)": lambda geo, v: _make_synthetic_geo(
            geo, specific_surface_area=v),
    }

    # Objectives to track
    objective_names = [
        "Flow Efficiency", "Pressure Drop (Pa/m)",
        "Mass Transfer (m/s)", "Buoyancy Score",
        "Clogging Risk Score", "Specific SA (m²/m³)"
    ]

    parameter_global_sensitivity = {}

    for param_name, param_values in parameter_ranges.items():
        param_importance_sum = 0.0

        for obj_name in objective_names:
            obj_values = []
            for val in param_values:
                geo_mod = param_modifiers[param_name](base_geo, val)
                objectives = _compute_objectives(
                    geo_mod, material, fluid_density, fluid_viscosity, flow_velocity)
                obj_values.append(objectives.get(obj_name, 0.0))

            si = _sensitivity_index(obj_values)
            r2 = _r_squared(param_values.tolist(), obj_values)
            d = _direction(obj_values)

            result = SensitivityResult(
                parameter_name=param_name,
                objective_name=obj_name,
                parameter_values=param_values.tolist(),
                objective_values=obj_values,
                sensitivity_index=round(si, 4),
                direction=d,
                r_squared=round(r2, 4)
            )
            report.results.append(result)
            param_importance_sum += si

        parameter_global_sensitivity[param_name] = round(
            param_importance_sum / len(objective_names), 4)

    # Sort by importance
    report.parameter_importance = dict(
        sorted(parameter_global_sensitivity.items(),
               key=lambda x: x[1], reverse=True))

    report.most_influential_parameter = max(
        parameter_global_sensitivity, key=parameter_global_sensitivity.get)

    # Most sensitive objective (highest average sensitivity across parameters)
    obj_sensitivity = {obj: 0.0 for obj in objective_names}
    for r in report.results:
        obj_sensitivity[r.objective_name] += r.sensitivity_index
    for obj in obj_sensitivity:
        obj_sensitivity[obj] /= len(parameter_ranges)
    report.most_sensitive_objective = max(obj_sensitivity, key=obj_sensitivity.get)

    return report


def get_sensitivity_matrix(report: SensitivityReport) -> Dict:
    """
    Extract a parameter × objective sensitivity matrix for heatmap display.
    Returns dict with 'parameters', 'objectives', 'matrix' keys.
    """
    params = list(dict.fromkeys(r.parameter_name for r in report.results))
    objs = list(dict.fromkeys(r.objective_name for r in report.results))

    matrix = np.zeros((len(params), len(objs)))
    for r in report.results:
        i = params.index(r.parameter_name)
        j = objs.index(r.objective_name)
        matrix[i][j] = r.sensitivity_index

    return {"parameters": params, "objectives": objs, "matrix": matrix.tolist()}
