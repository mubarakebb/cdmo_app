"""
Buoyancy Analysis Module
Computes material-dependent buoyancy behavior for biofilm carriers
in faecal sludge reactors.

Buoyancy critically affects reactor mixing dynamics and carrier
distribution within MBBR and similar systems.
"""

import numpy as np
from dataclasses import dataclass
from core.geometry import GeometryMetrics
from core.materials import MATERIALS


@dataclass
class BuoyancyMetrics:
    """Buoyancy analysis results for a carrier-material combination."""
    material_name: str = ""
    material_density: float = 0.0      # g/cm³
    fluid_density: float = 1.0         # g/cm³
    
    # Effective density accounting for void spaces
    effective_density: float = 0.0     # g/cm³
    
    # Buoyancy force
    buoyancy_force: float = 0.0        # N (positive = upward)
    weight_force: float = 0.0          # N (downward)
    net_force: float = 0.0             # N (positive = floats)
    
    # Behavior classification
    behavior: str = ""                 # "Floats", "Sinks", "Neutrally Buoyant"
    fill_fraction: float = 0.0         # fraction 0-1 (how much submerged if floating)
    
    # Reactor suitability score (0-1)
    # For MBBR: neutral/slight positive buoyancy is ideal
    buoyancy_score: float = 0.0
    
    # Notes for reactor design
    reactor_notes: str = ""


def compute_buoyancy(
    geo: GeometryMetrics,
    material_name: str,
    fluid_density_kg_m3: float = 1015.0,  # kg/m³ medium faecal sludge
    gravity: float = 9.81                  # m/s²
) -> BuoyancyMetrics:
    """
    Compute buoyancy behavior for a carrier made from a given material
    submerged in a fluid of known density.
    
    Uses Archimedes principle:
    F_buoyancy = ρ_fluid × V_displaced × g
    F_weight   = ρ_effective × V_total × g
    
    Where effective density accounts for the void spaces in the carrier.
    """
    bm = BuoyancyMetrics()
    
    if material_name not in MATERIALS:
        raise ValueError(f"Unknown material: {material_name}")
    
    mat = MATERIALS[material_name]
    bm.material_name = material_name
    
    # Convert to consistent units (g/cm³ and cm³ for readability)
    mat_density_gcm3 = mat["density_mean"]          # g/cm³
    fluid_density_gcm3 = fluid_density_kg_m3 / 1000  # convert kg/m³ -> g/cm³
    
    bm.material_density = mat_density_gcm3
    bm.fluid_density = fluid_density_gcm3
    
    # Convert geometry from mm³ to cm³
    solid_volume_cm3 = geo.volume / 1000.0
    total_volume_cm3 = geo.bounding_box_volume / 1000.0
    
    # Effective density: mass of solid / total bounding volume
    # This is what determines buoyancy in practice
    mass_g = mat_density_gcm3 * solid_volume_cm3
    bm.effective_density = round(mass_g / total_volume_cm3, 4) if total_volume_cm3 > 0 else 0.0
    
    # Forces in Newtons (using SI: kg, m³, m/s²)
    mass_kg = mat_density_gcm3 * (geo.volume * 1e-6)  # mm³ -> m³
    displaced_vol_m3 = total_volume_cm3 * 1e-6          # cm³ -> m³
    fluid_density_kg = fluid_density_kg_m3
    
    bm.weight_force = round(mass_kg * gravity, 6)
    bm.buoyancy_force = round(fluid_density_kg * displaced_vol_m3 * gravity, 6)
    bm.net_force = round(bm.buoyancy_force - bm.weight_force, 6)
    
    # Classify behavior
    tolerance = 0.005  # N — near-neutral tolerance
    if bm.net_force > tolerance:
        bm.behavior = "Floats"
        # Calculate what fraction is submerged at equilibrium
        if fluid_density_gcm3 > 0 and total_volume_cm3 > 0:
            bm.fill_fraction = round(
                min(1.0, bm.effective_density / fluid_density_gcm3), 4)
        else:
            bm.fill_fraction = 0.0
    elif bm.net_force < -tolerance:
        bm.behavior = "Sinks"
        bm.fill_fraction = 1.0
    else:
        bm.behavior = "Neutrally Buoyant"
        bm.fill_fraction = 1.0
    
    # ── Buoyancy Score for MBBR Systems ─────────────────────────────
    # In MBBR/moving bed reactors:
    # - Slightly floating or neutrally buoyant = ideal (good mixing)
    # - Strongly floating = poor distribution, accumulates at surface
    # - Strongly sinking = settles, dead zones form
    
    density_ratio = bm.effective_density / fluid_density_gcm3
    
    if 0.85 <= density_ratio <= 1.05:
        # Near-neutral: ideal for mixing
        bm.buoyancy_score = 1.0
        bm.reactor_notes = "Ideal for MBBR — near-neutral buoyancy ensures uniform reactor distribution."
    elif 0.70 <= density_ratio < 0.85:
        # Moderately floating: acceptable with aeration
        bm.buoyancy_score = 0.75
        bm.reactor_notes = "Moderate positive buoyancy. Aeration can maintain adequate mixing."
    elif density_ratio < 0.70:
        # Strongly floating: problematic
        bm.buoyancy_score = 0.40
        bm.reactor_notes = "Strong positive buoyancy — risk of surface accumulation. Consider ballast or design modification."
    elif 1.05 < density_ratio <= 1.20:
        # Slightly sinking: acceptable with adequate mixing
        bm.buoyancy_score = 0.70
        bm.reactor_notes = "Slight negative buoyancy. Adequate mixing energy required to keep carriers suspended."
    else:
        # Strongly sinking
        bm.buoyancy_score = 0.35
        bm.reactor_notes = "High sinking tendency — risk of dead zones and settling. Increased mixing energy needed."
    
    bm.buoyancy_score = round(bm.buoyancy_score, 4)
    
    return bm


def compare_materials_buoyancy(
    geo: GeometryMetrics,
    fluid_density_kg_m3: float = 1015.0
) -> dict:
    """
    Compare buoyancy behavior across all four materials for a given geometry.
    Returns dictionary keyed by material name.
    """
    results = {}
    for material in MATERIALS.keys():
        results[material] = compute_buoyancy(geo, material, fluid_density_kg_m3)
    return results


def get_buoyancy_summary(bm: BuoyancyMetrics) -> dict:
    """Return clean dictionary for display."""
    return {
        "Material": bm.material_name,
        "Material Density (g/cm³)": bm.material_density,
        "Effective Density (g/cm³)": bm.effective_density,
        "Fluid Density (g/cm³)": bm.fluid_density,
        "Buoyancy Behavior": bm.behavior,
        "Net Force (N)": bm.net_force,
        "Submersion Fraction": bm.fill_fraction,
        "Buoyancy Score": bm.buoyancy_score,
        "Reactor Notes": bm.reactor_notes,
    }
