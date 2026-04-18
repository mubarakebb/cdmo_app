"""
Multi-Objective Scoring & Pareto Frontier Analysis Engine

Implements weighted scoring and Pareto optimality identification
for comparing biofilm carrier designs across competing objectives.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from core.geometry import GeometryMetrics
from core.flow_analysis import FlowMetrics
from core.buoyancy import BuoyancyMetrics
from core.materials import MATERIALS


@dataclass
class ObjectiveWeights:
    """User-configurable weights for each performance objective (must sum to 1.0)."""
    sav_ratio: float = 0.30          # Surface area to volume ratio
    porosity: float = 0.20           # Void fraction
    flow_efficiency: float = 0.20    # Hydraulic performance
    buoyancy: float = 0.15           # Reactor mixing suitability
    biofilm_affinity: float = 0.10   # Material surface biofilm attraction
    mechanical: float = 0.05         # Structural durability
    
    def normalize(self):
        """Ensure weights sum to exactly 1.0."""
        total = (self.sav_ratio + self.porosity + self.flow_efficiency +
                 self.buoyancy + self.biofilm_affinity + self.mechanical)
        if total == 0:
            raise ValueError("All weights are zero.")
        self.sav_ratio /= total
        self.porosity /= total
        self.flow_efficiency /= total
        self.buoyancy /= total
        self.biofilm_affinity /= total
        self.mechanical /= total
    
    def to_dict(self) -> dict:
        return {
            "SA/V Ratio": self.sav_ratio,
            "Porosity": self.porosity,
            "Flow Efficiency": self.flow_efficiency,
            "Buoyancy Suitability": self.buoyancy,
            "Biofilm Affinity": self.biofilm_affinity,
            "Mechanical Score": self.mechanical,
        }


@dataclass
class CarrierScore:
    """Complete evaluation result for a single carrier-material combination."""
    # Identity
    design_id: str = ""
    filename: str = ""
    material: str = ""
    
    # Individual objective scores (all 0-1 normalized)
    score_sav: float = 0.0
    score_porosity: float = 0.0
    score_flow: float = 0.0
    score_buoyancy: float = 0.0
    score_biofilm_affinity: float = 0.0
    score_mechanical: float = 0.0
    
    # Raw metric values (for Pareto analysis)
    sav_ratio: float = 0.0
    porosity: float = 0.0
    specific_surface_area: float = 0.0
    flow_efficiency: float = 0.0
    buoyancy_score: float = 0.0
    pressure_drop: float = 0.0
    mass_transfer_coeff: float = 0.0
    
    # Composite weighted score
    composite_score: float = 0.0
    rank: int = 0
    
    # Pareto
    is_pareto_optimal: bool = False
    pareto_dominated_by: List[str] = field(default_factory=list)


def normalize_scores(values: List[float], higher_is_better: bool = True) -> List[float]:
    """
    Min-max normalize a list of values to [0, 1].
    If higher_is_better=False, inverts the normalization.
    """
    arr = np.array(values, dtype=float)
    min_v, max_v = arr.min(), arr.max()
    
    if max_v == min_v:
        return [0.5] * len(values)  # all equal -> neutral score
    
    normalized = (arr - min_v) / (max_v - min_v)
    
    if not higher_is_better:
        normalized = 1.0 - normalized
    
    return normalized.tolist()


def score_carrier(
    geo: GeometryMetrics,
    flow: FlowMetrics,
    buoy: BuoyancyMetrics,
    material_name: str,
    design_id: str = "",
) -> CarrierScore:
    """
    Build a CarrierScore from analysis results.
    Raw scores are stored; normalization happens across the full population.
    """
    cs = CarrierScore()
    cs.design_id = design_id or f"{geo.filename}_{material_name}"
    cs.filename = geo.filename
    cs.material = material_name
    
    # Store raw metric values
    cs.sav_ratio = geo.sav_ratio
    cs.porosity = geo.porosity
    cs.specific_surface_area = geo.specific_surface_area
    cs.flow_efficiency = flow.flow_efficiency_score
    cs.buoyancy_score = buoy.buoyancy_score
    cs.pressure_drop = flow.pressure_drop_per_m
    cs.mass_transfer_coeff = flow.mass_transfer_coefficient
    
    # Material-based scores (fixed per material)
    mat = MATERIALS[material_name]
    cs.score_biofilm_affinity = mat["biofilm_affinity_score"]
    cs.score_mechanical = mat["mechanical_score"]
    cs.score_buoyancy = buoy.buoyancy_score
    cs.score_flow = flow.flow_efficiency_score
    
    return cs


def compute_composite_scores(
    carriers: List[CarrierScore],
    weights: ObjectiveWeights
) -> List[CarrierScore]:
    """
    Normalize all scores across the population and compute weighted composite scores.
    This must be called after ALL carriers have been scored, so normalization
    reflects the full design space being evaluated.
    """
    if not carriers:
        return carriers
    
    weights.normalize()
    
    # Extract raw values for population-level normalization
    sav_values = [c.sav_ratio for c in carriers]
    porosity_values = [c.porosity for c in carriers]
    flow_values = [c.flow_efficiency for c in carriers]
    buoy_values = [c.buoyancy_score for c in carriers]
    
    # Normalize each objective across population
    norm_sav = normalize_scores(sav_values, higher_is_better=True)
    norm_por = normalize_scores(porosity_values, higher_is_better=True)
    norm_flow = normalize_scores(flow_values, higher_is_better=True)
    norm_buoy = normalize_scores(buoy_values, higher_is_better=True)
    
    for i, carrier in enumerate(carriers):
        carrier.score_sav = round(norm_sav[i], 4)
        carrier.score_porosity = round(norm_por[i], 4)
        carrier.score_flow = round(norm_flow[i], 4)
        carrier.score_buoyancy = round(norm_buoy[i], 4)
        
        # Compute weighted composite
        carrier.composite_score = round(
            weights.sav_ratio       * carrier.score_sav +
            weights.porosity        * carrier.score_porosity +
            weights.flow_efficiency * carrier.score_flow +
            weights.buoyancy        * carrier.score_buoyancy +
            weights.biofilm_affinity * carrier.score_biofilm_affinity +
            weights.mechanical      * carrier.score_mechanical,
            4
        )
    
    # Rank by composite score
    carriers.sort(key=lambda c: c.composite_score, reverse=True)
    for i, carrier in enumerate(carriers):
        carrier.rank = i + 1
    
    return carriers


def find_pareto_frontier(
    carriers: List[CarrierScore],
    objectives: List[str] = None
) -> List[CarrierScore]:
    """
    Identify Pareto-optimal carriers.
    A carrier is Pareto-optimal if no other carrier is better on ALL objectives simultaneously.
    
    Default objectives: SA/V ratio, porosity, flow efficiency, buoyancy
    """
    if objectives is None:
        objectives = ["score_sav", "score_porosity", "score_flow", "score_buoyancy"]
    
    n = len(carriers)
    
    for i, carrier_i in enumerate(carriers):
        dominated = False
        dominators = []
        
        for j, carrier_j in enumerate(carriers):
            if i == j:
                continue
            
            # Check if carrier_j dominates carrier_i
            # j dominates i if j is >= i on all objectives AND > i on at least one
            scores_i = [getattr(carrier_i, obj) for obj in objectives]
            scores_j = [getattr(carrier_j, obj) for obj in objectives]
            
            j_dominates = all(sj >= si for si, sj in zip(scores_i, scores_j))
            j_strictly_better = any(sj > si for si, sj in zip(scores_i, scores_j))
            
            if j_dominates and j_strictly_better:
                dominated = True
                dominators.append(carrier_j.design_id)
        
        carrier_i.is_pareto_optimal = not dominated
        carrier_i.pareto_dominated_by = dominators
    
    return carriers


def generate_improvement_suggestions(carrier: CarrierScore, weights: ObjectiveWeights) -> List[str]:
    """
    Generate specific, quantified design improvement suggestions
    based on which objectives score lowest relative to their weight.
    """
    suggestions = []
    
    # Identify weakest objectives
    weighted_scores = {
        "SA/V Ratio": carrier.score_sav * weights.sav_ratio,
        "Porosity": carrier.score_porosity * weights.porosity,
        "Flow Efficiency": carrier.score_flow * weights.flow_efficiency,
        "Buoyancy": carrier.score_buoyancy * weights.buoyancy,
        "Biofilm Affinity": carrier.score_biofilm_affinity * weights.biofilm_affinity,
    }
    
    sorted_scores = sorted(weighted_scores.items(), key=lambda x: x[1])
    
    for obj, score in sorted_scores[:3]:  # Top 3 weakest
        if obj == "SA/V Ratio" and carrier.score_sav < 0.5:
            suggestions.append(
                f"SA/V ratio ({carrier.sav_ratio:.2f} mm⁻¹) is below median. "
                f"Consider increasing internal fins, adding surface texture, "
                f"or adopting a gyroid/lattice internal structure to increase surface area.")
        
        elif obj == "Porosity" and carrier.score_porosity < 0.5:
            suggestions.append(
                f"Porosity ({carrier.porosity:.2f}) is below median. "
                f"Increasing void fraction by enlarging flow channels or reducing "
                f"wall thickness could improve hydraulic conductivity and reduce clogging risk.")
        
        elif obj == "Flow Efficiency" and carrier.score_flow < 0.5:
            suggestions.append(
                f"Flow efficiency score ({carrier.flow_efficiency:.2f}) indicates high pressure drop "
                f"or poor mass transfer. Consider streamlining internal channels to reduce "
                f"resistance and improve nutrient/substrate delivery to biofilm.")
        
        elif obj == "Buoyancy" and carrier.score_buoyancy < 0.5:
            mat = carrier.material
            if mat == "PP":
                suggestions.append(
                    f"PP carrier floats strongly (density 0.91 g/cm³). "
                    f"Consider reducing porosity slightly to increase effective density, "
                    f"or use in reactors with bottom aeration to improve mixing.")
            elif mat in ["PETG", "PLA"]:
                suggestions.append(
                    f"{mat} carrier sinks (density > 1.0 g/cm³). "
                    f"Increase porosity to reduce effective density, "
                    f"or ensure adequate mixing energy to keep carriers suspended.")
        
        elif obj == "Biofilm Affinity" and carrier.score_biofilm_affinity < 0.5:
            suggestions.append(
                f"Material biofilm affinity is low for {carrier.material}. "
                f"Consider surface roughening during printing (lower layer height) "
                f"or chemical surface treatment to improve microbial attachment.")
    
    if not suggestions:
        suggestions.append("This design performs well across all objectives. "
                          "Fine-tune objective weights to explore trade-off improvements.")
    
    return suggestions


def get_ranking_summary(carriers: List[CarrierScore]) -> List[dict]:
    """Return a sorted list of summary dicts for table display."""
    return [
        {
            "Rank": c.rank,
            "Design": c.filename.replace(".stl", ""),
            "Material": c.material,
            "Composite Score": c.composite_score,
            "SA/V Score": c.score_sav,
            "Porosity Score": c.score_porosity,
            "Flow Score": c.score_flow,
            "Buoyancy Score": c.score_buoyancy,
            "Pareto Optimal": "✓" if c.is_pareto_optimal else "",
        }
        for c in sorted(carriers, key=lambda c: c.rank)
    ]
