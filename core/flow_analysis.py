"""
Flow Analysis Engine
Empirical correlation-based hydraulic and mass transfer assessment
for biofilm carriers in faecal sludge reactors.

Uses:
- Ergun equation for pressure drop prediction
- Kozeny-Carman for permeability estimation  
- Sherwood number correlations for mass transfer coefficient
- Reynolds number for flow regime classification
"""

import numpy as np
from dataclasses import dataclass
from core.geometry import GeometryMetrics


@dataclass
class FlowMetrics:
    """All flow and mass transfer metrics for a carrier."""
    # Operating conditions used
    flow_velocity: float = 0.0       # m/s superficial velocity
    fluid_density: float = 1000.0    # kg/m³
    fluid_viscosity: float = 0.001   # Pa·s
    temperature: float = 25.0        # °C
    
    # Flow regime
    reynolds_number: float = 0.0
    flow_regime: str = ""
    
    # Pressure drop (Ergun equation)
    pressure_drop_per_m: float = 0.0  # Pa/m
    
    # Permeability (Kozeny-Carman)
    permeability: float = 0.0         # m²
    
    # Mass transfer
    sherwood_number: float = 0.0
    mass_transfer_coefficient: float = 0.0  # m/s
    
    # Composite flow efficiency score (0-1)
    flow_efficiency_score: float = 0.0
    
    # Clogging risk assessment
    clogging_risk: str = ""
    clogging_risk_score: float = 0.0  # 0=low risk, 1=high risk


def compute_flow_metrics(
    geo: GeometryMetrics,
    superficial_velocity: float = 0.01,   # m/s
    fluid_density: float = 1015.0,        # kg/m³ (medium faecal sludge)
    fluid_viscosity: float = 0.003,       # Pa·s
    temperature: float = 25.0,            # °C
    diffusivity: float = 1.5e-9           # m²/s (substrate diffusivity in water)
) -> FlowMetrics:
    """
    Compute all hydraulic and mass transfer metrics using empirical correlations.
    
    Parameters:
        geo: GeometryMetrics from geometry analysis
        superficial_velocity: Approach velocity of fluid (m/s)
        fluid_density: Density of fluid (kg/m³)
        fluid_viscosity: Dynamic viscosity (Pa·s)
        temperature: Operating temperature (°C)
        diffusivity: Molecular diffusivity of limiting substrate (m²/s)
    """
    flow = FlowMetrics()
    flow.flow_velocity = superficial_velocity
    flow.fluid_density = fluid_density
    flow.fluid_viscosity = fluid_viscosity
    flow.temperature = temperature
    
    # Convert geometry to SI units
    porosity = geo.porosity
    dh_m = geo.hydraulic_diameter / 1000.0  # mm -> m
    specific_sa = geo.specific_surface_area  # m²/m³ already in SI
    
    # Guard against degenerate geometry
    if dh_m <= 0 or porosity <= 0 or porosity >= 1:
        flow.flow_regime = "Undefined"
        flow.flow_efficiency_score = 0.0
        return flow

    # ── Reynolds Number ──────────────────────────────────────────────
    # Using hydraulic diameter as characteristic length
    flow.reynolds_number = round(
        (fluid_density * superficial_velocity * dh_m) / fluid_viscosity, 4)
    
    if flow.reynolds_number < 10:
        flow.flow_regime = "Laminar (Darcy)"
    elif flow.reynolds_number < 300:
        flow.flow_regime = "Transitional"
    else:
        flow.flow_regime = "Turbulent"

    # ── Pressure Drop — Ergun Equation ───────────────────────────────
    # ΔP/L = (150 μ (1-ε)² v) / (ε³ dp²)  +  (1.75 ρ (1-ε) v²) / (ε³ dp)
    # dp = hydraulic diameter as equivalent particle diameter
    dp = dh_m
    eps = porosity
    mu = fluid_viscosity
    rho = fluid_density
    v = superficial_velocity
    
    viscous_term = (150 * mu * (1 - eps)**2 * v) / (eps**3 * dp**2)
    inertial_term = (1.75 * rho * (1 - eps) * v**2) / (eps**3 * dp)
    flow.pressure_drop_per_m = round(viscous_term + inertial_term, 4)

    # ── Permeability — Kozeny-Carman ─────────────────────────────────
    # k = (dp² * ε³) / (180 * (1-ε)²)
    if (1 - eps) > 0:
        flow.permeability = round(
            (dp**2 * eps**3) / (180 * (1 - eps)**2), 12)

    # ── Mass Transfer — Sherwood Number Correlation ──────────────────
    # Using Wilson-Geankoplis correlation for packed beds:
    # Sh = (1.09 / ε) * Re^(1/3) * Sc^(1/3)   [Re < 55]
    # Sh = (0.91 / ε) * Re^(0.49) * Sc^(1/3)  [Re >= 55]
    
    kinematic_viscosity = fluid_viscosity / fluid_density
    schmidt_number = kinematic_viscosity / diffusivity
    
    if flow.reynolds_number < 55:
        flow.sherwood_number = round(
            (1.09 / eps) * (flow.reynolds_number ** (1/3)) * (schmidt_number ** (1/3)), 4)
    else:
        flow.sherwood_number = round(
            (0.91 / eps) * (flow.reynolds_number ** 0.49) * (schmidt_number ** (1/3)), 4)
    
    # Mass transfer coefficient (m/s)
    if dh_m > 0:
        flow.mass_transfer_coefficient = round(
            flow.sherwood_number * diffusivity / dh_m, 8)

    # ── Clogging Risk Assessment ──────────────────────────────────────
    # For faecal sludge, clogging risk increases when porosity < 0.6
    # and hydraulic diameter < 3mm (particles can't pass through)
    if porosity < 0.50:
        flow.clogging_risk = "High"
        flow.clogging_risk_score = 0.85
    elif porosity < 0.65:
        flow.clogging_risk = "Moderate"
        flow.clogging_risk_score = 0.50
    else:
        flow.clogging_risk = "Low"
        flow.clogging_risk_score = 0.15
    
    # Increase risk if hydraulic diameter is very small
    if geo.hydraulic_diameter < 3.0:
        flow.clogging_risk_score = min(1.0, flow.clogging_risk_score + 0.2)
        flow.clogging_risk = "High" if flow.clogging_risk_score > 0.6 else flow.clogging_risk

    # ── Flow Efficiency Score (0-1) ───────────────────────────────────
    # Composite score balancing: low pressure drop, high mass transfer,
    # low clogging risk, appropriate flow regime
    
    # Normalize pressure drop (lower is better, reference: 1000 Pa/m)
    pressure_score = max(0.0, 1.0 - (flow.pressure_drop_per_m / 5000.0))
    
    # Normalize mass transfer (higher is better, reference: 1e-5 m/s)
    mt_score = min(1.0, flow.mass_transfer_coefficient / 1e-5)
    
    # Clogging penalty
    clog_score = 1.0 - flow.clogging_risk_score
    
    # Flow regime bonus (transitional is ideal for biofilm reactors)
    if flow.flow_regime == "Transitional":
        regime_score = 1.0
    elif flow.flow_regime == "Laminar (Darcy)":
        regime_score = 0.6
    else:
        regime_score = 0.75
    
    flow.flow_efficiency_score = round(
        0.30 * pressure_score +
        0.35 * mt_score +
        0.25 * clog_score +
        0.10 * regime_score, 4)
    
    return flow


def get_flow_summary(flow: FlowMetrics) -> dict:
    """Return clean dictionary of flow metrics for display."""
    return {
        "Reynolds Number": flow.reynolds_number,
        "Flow Regime": flow.flow_regime,
        "Pressure Drop (Pa/m)": flow.pressure_drop_per_m,
        "Permeability (m²)": f"{flow.permeability:.3e}",
        "Sherwood Number": flow.sherwood_number,
        "Mass Transfer Coefficient (m/s)": f"{flow.mass_transfer_coefficient:.3e}",
        "Clogging Risk": flow.clogging_risk,
        "Flow Efficiency Score": flow.flow_efficiency_score,
    }
