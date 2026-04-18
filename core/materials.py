"""
Material properties database for 3D printed biofilm carriers.
All properties are research-validated values for PLA, ABS, PETG, and PP.
"""

MATERIALS = {
    "PLA": {
        "name": "Polylactic Acid (PLA)",
        "density_min": 1.24,
        "density_max": 1.25,
        "density_mean": 1.245,
        "tensile_strength": 50.0,       # MPa
        "elastic_modulus": 3500.0,       # MPa
        "surface_energy": 38.0,          # mJ/m² - influences biofilm attachment
        "hydrophilicity": "moderate",
        "chemical_resistance": "low",
        "biodegradable": True,
        "print_difficulty": "easy",
        "biofilm_affinity_score": 0.85,  # 0-1, higher = better biofilm attachment
        "chemical_resistance_score": 0.40,
        "mechanical_score": 0.65,
        "color": "#4CAF50",
        "notes": "Biodegradable, good microbial affinity, lower chemical resistance"
    },
    "ABS": {
        "name": "Acrylonitrile Butadiene Styrene (ABS)",
        "density_min": 1.04,
        "density_max": 1.06,
        "density_mean": 1.05,
        "tensile_strength": 40.0,
        "elastic_modulus": 2300.0,
        "surface_energy": 42.0,
        "hydrophilicity": "moderate",
        "chemical_resistance": "moderate",
        "biodegradable": False,
        "print_difficulty": "moderate",
        "biofilm_affinity_score": 0.75,
        "chemical_resistance_score": 0.65,
        "mechanical_score": 0.80,
        "color": "#2196F3",
        "notes": "High impact resistance, good durability, requires heated bed"
    },
    "PETG": {
        "name": "Polyethylene Terephthalate Glycol (PETG)",
        "density_min": 1.27,
        "density_max": 1.29,
        "density_mean": 1.28,
        "tensile_strength": 53.0,
        "elastic_modulus": 2100.0,
        "surface_energy": 41.0,
        "hydrophilicity": "low",
        "chemical_resistance": "high",
        "biodegradable": False,
        "print_difficulty": "easy",
        "biofilm_affinity_score": 0.70,
        "chemical_resistance_score": 0.85,
        "mechanical_score": 0.75,
        "color": "#FF9800",
        "notes": "Excellent chemical resistance, smooth surface, higher density affects buoyancy"
    },
    "PP": {
        "name": "Polypropylene (PP)",
        "density_min": 0.90,
        "density_max": 0.91,
        "density_mean": 0.905,
        "tensile_strength": 35.0,
        "elastic_modulus": 1300.0,
        "surface_energy": 30.0,
        "hydrophilicity": "low",
        "chemical_resistance": "very_high",
        "biodegradable": False,
        "print_difficulty": "hard",
        "biofilm_affinity_score": 0.60,
        "chemical_resistance_score": 0.95,
        "mechanical_score": 0.60,
        "color": "#9C27B0",
        "notes": "Best chemical resistance, lightweight (floats), difficult to print"
    }
}

# Faecal sludge fluid properties (representative values)
FLUID_PROPERTIES = {
    "water": {
        "name": "Clean Water (reference)",
        "density": 1000.0,       # kg/m³
        "viscosity": 0.001,      # Pa·s at 20°C
        "temperature": 20.0      # °C
    },
    "faecal_sludge_low": {
        "name": "Faecal Sludge - Low Strength",
        "density": 1005.0,
        "viscosity": 0.0015,
        "temperature": 25.0
    },
    "faecal_sludge_medium": {
        "name": "Faecal Sludge - Medium Strength",
        "density": 1015.0,
        "viscosity": 0.003,
        "temperature": 25.0
    },
    "faecal_sludge_high": {
        "name": "Faecal Sludge - High Strength",
        "density": 1030.0,
        "viscosity": 0.006,
        "temperature": 30.0
    }
}


def get_material(name: str) -> dict:
    """Return material properties by name."""
    if name not in MATERIALS:
        raise ValueError(f"Material '{name}' not found. Available: {list(MATERIALS.keys())}")
    return MATERIALS[name]


def get_all_materials() -> list:
    """Return list of all material names."""
    return list(MATERIALS.keys())


def get_fluid(name: str) -> dict:
    """Return fluid properties by name."""
    if name not in FLUID_PROPERTIES:
        raise ValueError(f"Fluid '{name}' not found.")
    return FLUID_PROPERTIES[name]


def get_all_fluids() -> list:
    """Return list of all fluid names."""
    return list(FLUID_PROPERTIES.keys())
