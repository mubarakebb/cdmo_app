"""
Genetic Algorithm Optimiser
Searches the parametric carrier design space to find Pareto-optimal geometries.

Uses NSGA-II style multi-objective genetic algorithm:
- Population of parametric carrier designs
- Tournament selection
- Simulated binary crossover (SBX)
- Polynomial mutation
- Non-dominated sorting for Pareto ranking
- Crowding distance for diversity preservation

This is the research core of the automated design improvement claim.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Callable
import copy
import os
import tempfile
from contextlib import contextmanager

from core.stl_generator import CarrierParams, generate_carrier_stl
from core.geometry import analyze_stl
from core.flow_analysis import compute_flow_metrics
from core.buoyancy import compute_buoyancy
from core.materials import MATERIALS


# ─── Design Variable Bounds ───────────────────────────────────────────────────
DESIGN_BOUNDS = {
    "outer_diameter":    (15.0,  80.0),
    "height":            (5.0,   35.0),
    "wall_thickness":    (0.5,   3.0),
    "num_fins":          (3,     20),
    "fin_thickness":     (0.4,   2.5),
    "num_rings":         (0,     5),
    "ring_gap":          (1.0,   10.0),
    "num_spikes":        (0,     24),
    "spike_height":      (0.5,   5.0),
    "spike_base":        (0.5,   3.5),
}

PARAM_NAMES = list(DESIGN_BOUNDS.keys())
N_VARS = len(PARAM_NAMES)
INTEGER_VARS = {"num_fins", "num_rings", "num_spikes"}  # must be integers


@dataclass
class Individual:
    """A single candidate design in the genetic algorithm population."""
    genes: np.ndarray = field(default_factory=lambda: np.zeros(N_VARS))
    
    # Objective values (all maximised internally — negate if minimising)
    obj_sav: float = 0.0
    obj_porosity: float = 0.0
    obj_flow: float = 0.0
    obj_buoyancy: float = 0.0
    
    # NSGA-II metadata
    rank: int = 0
    crowding_distance: float = 0.0
    domination_count: int = 0
    dominated_set: List[int] = field(default_factory=list)
    
    # Derived
    composite_score: float = 0.0
    params: CarrierParams = None
    geo_metrics: dict = field(default_factory=dict)
    feasible: bool = True
    error: str = ""


@dataclass 
class GAResult:
    """Result of a genetic algorithm optimisation run."""
    population: List[Individual] = field(default_factory=list)
    pareto_front: List[Individual] = field(default_factory=list)
    generation_history: List[dict] = field(default_factory=list)
    best_composite: Individual = None
    n_generations: int = 0
    design_type: str = "cross_flow"
    material: str = "PLA"
    convergence_data: List[float] = field(default_factory=list)
    mean_convergence_data: List[float] = field(default_factory=list)


def genes_to_params(genes: np.ndarray, design_type: str = "cross_flow") -> CarrierParams:
    """Convert gene array to CarrierParams, applying bounds and integer constraints."""
    bounds = DESIGN_BOUNDS
    
    p = CarrierParams()
    p.design_type = design_type
    p.angular_segments = 32  # fixed for speed during optimisation
    
    for i, name in enumerate(PARAM_NAMES):
        lo, hi = bounds[name]
        val = float(np.clip(genes[i], lo, hi))
        if name in INTEGER_VARS:
            val = int(round(val))
        setattr(p, name, val)
    
    return p


def params_to_genes(params: CarrierParams) -> np.ndarray:
    """Convert CarrierParams back to gene array."""
    genes = np.zeros(N_VARS)
    for i, name in enumerate(PARAM_NAMES):
        genes[i] = float(getattr(params, name, 0))
    return genes


def random_individual(design_type: str = "cross_flow") -> Individual:
    """Create a random individual within bounds."""
    ind = Individual()
    genes = np.zeros(N_VARS)
    for i, name in enumerate(PARAM_NAMES):
        lo, hi = DESIGN_BOUNDS[name]
        if name in INTEGER_VARS:
            genes[i] = float(np.random.randint(int(lo), int(hi) + 1))
        else:
            genes[i] = np.random.uniform(lo, hi)
    ind.genes = genes
    ind.params = genes_to_params(genes, design_type)
    return ind


@contextmanager
def _tmp_stl(params):
    """Context manager that generates a carrier STL, yields the path, then always deletes it."""
    path = None
    try:
        path, _ = generate_carrier_stl(params)
        yield path
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


def evaluate_individual(
    ind: Individual,
    material: str,
    fluid_density: float,
    fluid_viscosity: float,
    flow_velocity: float,
    weights: Dict[str, float],
    sav_population_max: float = 0.0,
) -> Individual:
    """
    Evaluate a single individual by generating its STL and computing all objectives.
    Marks infeasible if generation or analysis fails.

    Parameters:
        sav_population_max: Running maximum SA/V across the current population used
            for dynamic normalisation.  Pass 0.0 (default) to skip normalisation
            (raw value capped at 1.0 via min()).
    """
    try:
        with _tmp_stl(ind.params) as tmp_path:
            from core.geometry import analyze_stl as _analyze
            geo = _analyze(tmp_path)

        # Sanity checks — reject degenerate geometries
        if geo.porosity < 0.20 or geo.porosity > 0.97:
            ind.feasible = False
            ind.error = f"Porosity {geo.porosity:.2f} out of feasible range"
            return ind

        if geo.sav_ratio <= 0 or geo.volume <= 0:
            ind.feasible = False
            ind.error = "Zero or negative SA/V or volume"
            return ind

        flow = compute_flow_metrics(geo, flow_velocity, fluid_density, fluid_viscosity)
        buoy = compute_buoyancy(geo, material, fluid_density)

        # Material scores (fixed per material — same as scoring.py)
        from core.materials import MATERIALS as _MATS
        mat_data = _MATS.get(material, {})
        biofilm_score  = float(mat_data.get("biofilm_affinity_score", 0.0))
        mechanical_score = float(mat_data.get("mechanical_score", 0.0))

        # Store objectives (all maximised)
        ind.obj_sav      = geo.sav_ratio
        ind.obj_porosity = geo.porosity
        ind.obj_flow     = flow.flow_efficiency_score
        ind.obj_buoyancy = buoy.buoyancy_score

        # Dynamic SAV normalisation: use population max if available, else cap at 1.0
        if sav_population_max > 0:
            norm_sav = min(1.0, geo.sav_ratio / sav_population_max)
        else:
            norm_sav = min(1.0, geo.sav_ratio)

        # All six objectives — consistent with scoring.py ObjectiveWeights
        w_total = (
            weights.get("sav_ratio", 0.30)
            + weights.get("porosity", 0.20)
            + weights.get("flow_efficiency", 0.20)
            + weights.get("buoyancy", 0.15)
            + weights.get("biofilm_affinity", 0.10)
            + weights.get("mechanical", 0.05)
        ) or 1.0  # guard against all-zero weights

        ind.composite_score = (
            weights.get("sav_ratio", 0.30)       * norm_sav +
            weights.get("porosity", 0.20)         * geo.porosity +
            weights.get("flow_efficiency", 0.20)  * flow.flow_efficiency_score +
            weights.get("buoyancy", 0.15)         * buoy.buoyancy_score +
            weights.get("biofilm_affinity", 0.10) * biofilm_score +
            weights.get("mechanical", 0.05)       * mechanical_score
        ) / w_total
        
        ind.geo_metrics = {
            "sav_ratio": geo.sav_ratio,
            "porosity": geo.porosity,
            "surface_area": geo.surface_area,
            "volume": geo.volume,
            "specific_surface_area": geo.specific_surface_area,
            "hydraulic_diameter": geo.hydraulic_diameter,
            "flow_efficiency": flow.flow_efficiency_score,
            "buoyancy_score": buoy.buoyancy_score,
            "pressure_drop": flow.pressure_drop_per_m,
            "mass_transfer": flow.mass_transfer_coefficient,
            "dim_x": geo.dim_x,
            "dim_y": geo.dim_y,
            "dim_z": geo.dim_z,
        }
        ind.feasible = True
        
    except ModuleNotFoundError as e:
        # Missing runtime dependency should fail fast with actionable guidance.
        raise RuntimeError(
            f"Missing Python dependency: '{e.name}'. "
            "Install requirements.txt (or pip install networkx) and rerun optimisation."
        ) from e
    except Exception as e:
        ind.feasible = False
        ind.error = str(e)

    return ind


def dominates(a: Individual, b: Individual) -> bool:
    """Return True if individual a dominates individual b (all obj >= and at least one >)."""
    objs_a = [a.obj_sav, a.obj_porosity, a.obj_flow, a.obj_buoyancy]
    objs_b = [b.obj_sav, b.obj_porosity, b.obj_flow, b.obj_buoyancy]
    return (all(oa >= ob for oa, ob in zip(objs_a, objs_b)) and
            any(oa > ob for oa, ob in zip(objs_a, objs_b)))


def non_dominated_sort(population: List[Individual]) -> List[List[int]]:
    """NSGA-II non-dominated sorting. Returns list of Pareto fronts (indices)."""
    n = len(population)
    domination_count = [0] * n
    dominated_sets = [[] for _ in range(n)]
    fronts = [[]]
    
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if dominates(population[i], population[j]):
                dominated_sets[i].append(j)
            elif dominates(population[j], population[i]):
                domination_count[i] += 1
        
        population[i].domination_count = domination_count[i]
        population[i].dominated_set = dominated_sets[i]
        
        if domination_count[i] == 0:
            population[i].rank = 1
            fronts[0].append(i)
    
    current_front = 0
    while fronts[current_front]:
        next_front = []
        for i in fronts[current_front]:
            for j in dominated_sets[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    population[j].rank = current_front + 2
                    next_front.append(j)
        current_front += 1
        fronts.append(next_front)
    
    return [f for f in fronts if f]


def crowding_distance(population: List[Individual], front: List[int]) -> None:
    """Compute crowding distance for individuals in a Pareto front."""
    n = len(front)
    if n <= 2:
        for idx in front:
            population[idx].crowding_distance = float('inf')
        return
    
    objectives = ["obj_sav", "obj_porosity", "obj_flow", "obj_buoyancy"]
    
    for idx in front:
        population[idx].crowding_distance = 0.0
    
    for obj in objectives:
        sorted_front = sorted(front, key=lambda i: getattr(population[i], obj))
        
        population[sorted_front[0]].crowding_distance = float('inf')
        population[sorted_front[-1]].crowding_distance = float('inf')
        
        obj_range = (getattr(population[sorted_front[-1]], obj) -
                     getattr(population[sorted_front[0]], obj))
        
        if obj_range == 0:
            continue
        
        for k in range(1, n - 1):
            population[sorted_front[k]].crowding_distance += (
                getattr(population[sorted_front[k + 1]], obj) -
                getattr(population[sorted_front[k - 1]], obj)
            ) / obj_range


def tournament_select(population: List[Individual]) -> Individual:
    """Binary tournament selection based on rank and crowding distance."""
    i, j = np.random.choice(len(population), 2, replace=False)
    a, b = population[i], population[j]
    
    if a.rank < b.rank:
        return copy.deepcopy(a)
    elif b.rank < a.rank:
        return copy.deepcopy(b)
    elif a.crowding_distance > b.crowding_distance:
        return copy.deepcopy(a)
    else:
        return copy.deepcopy(b)


def sbx_crossover(
    parent1: Individual, parent2: Individual,
    eta: float = 15.0, crossover_prob: float = 0.9,
    design_type: str = "cross_flow"
) -> Tuple[Individual, Individual]:
    """Simulated Binary Crossover (SBX)."""
    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)
    
    if np.random.random() > crossover_prob:
        return child1, child2
    
    for i, name in enumerate(PARAM_NAMES):
        lo, hi = DESIGN_BOUNDS[name]
        
        if np.random.random() < 0.5:
            continue
        
        x1, x2 = parent1.genes[i], parent2.genes[i]
        
        if abs(x1 - x2) < 1e-10:
            continue
        
        if x1 > x2:
            x1, x2 = x2, x1
        
        beta = 1.0 + (2.0 * (x1 - lo) / (x2 - x1))
        alpha = 2.0 - beta ** (-(eta + 1.0))
        u = np.random.random()
        
        if u <= 1.0 / alpha:
            beta_q = (u * alpha) ** (1.0 / (eta + 1.0))
        else:
            beta_q = (1.0 / (2.0 - u * alpha)) ** (1.0 / (eta + 1.0))
        
        c1 = 0.5 * ((x1 + x2) - beta_q * (x2 - x1))
        c2 = 0.5 * ((x1 + x2) + beta_q * (x2 - x1))
        
        c1 = np.clip(c1, lo, hi)
        c2 = np.clip(c2, lo, hi)
        
        if name in INTEGER_VARS:
            c1, c2 = float(int(round(c1))), float(int(round(c2)))
        
        child1.genes[i] = c1
        child2.genes[i] = c2
    
    child1.params = genes_to_params(child1.genes, design_type)
    child2.params = genes_to_params(child2.genes, design_type)
    return child1, child2


def polynomial_mutation(
    ind: Individual, eta: float = 20.0,
    mutation_prob: float = None, design_type: str = "cross_flow"
) -> Individual:
    """Polynomial mutation operator."""
    mutant = copy.deepcopy(ind)
    if mutation_prob is None:
        mutation_prob = 1.0 / N_VARS
    
    for i, name in enumerate(PARAM_NAMES):
        if np.random.random() > mutation_prob:
            continue
        
        lo, hi = DESIGN_BOUNDS[name]
        x = mutant.genes[i]
        delta1 = (x - lo) / (hi - lo)
        delta2 = (hi - x) / (hi - lo)
        
        u = np.random.random()
        if u < 0.5:
            delta_q = (2.0 * u + (1.0 - 2.0 * u) * (1.0 - delta1) ** (eta + 1.0)) ** (1.0 / (eta + 1.0)) - 1.0
        else:
            delta_q = 1.0 - (2.0 * (1.0 - u) + 2.0 * (u - 0.5) * (1.0 - delta2) ** (eta + 1.0)) ** (1.0 / (eta + 1.0))
        
        x_new = np.clip(x + delta_q * (hi - lo), lo, hi)
        if name in INTEGER_VARS:
            x_new = float(int(round(x_new)))
        
        mutant.genes[i] = x_new
    
    mutant.params = genes_to_params(mutant.genes, design_type)
    return mutant


def run_genetic_algorithm(
    n_generations: int = 20,
    population_size: int = 20,
    design_type: str = "cross_flow",
    material: str = "PLA",
    fluid_density: float = 1015.0,
    fluid_viscosity: float = 0.003,
    flow_velocity: float = 0.01,
    weights: Dict[str, float] = None,
    progress_callback: Callable = None,
    seed_params: CarrierParams = None,
    random_seed: int = None,
) -> GAResult:
    """
    Run NSGA-II multi-objective genetic algorithm to optimise carrier geometry.

    Parameters:
        n_generations: Number of generations to evolve
        population_size: Must be even; typical values 10-30 for speed
        design_type: Carrier topology to optimise
        material: Material for buoyancy and affinity scoring
        progress_callback: Optional function(gen, total, best_score) for UI updates
        seed_params: Optional starting design to seed the initial population
        random_seed: Optional integer seed for reproducible runs (None = random).

    Returns:
        GAResult with Pareto front and convergence history
    """
    if weights is None:
        weights = {
            "sav_ratio": 0.30, "porosity": 0.20,
            "flow_efficiency": 0.20, "buoyancy": 0.15,
            "biofilm_affinity": 0.10, "mechanical": 0.05,
        }

    if random_seed is not None:
        np.random.seed(random_seed)

    result = GAResult(design_type=design_type, material=material,
                      n_generations=n_generations)
    
    # Initialise population
    population = []
    for i in range(population_size):
        if i == 0 and seed_params is not None:
            ind = Individual()
            ind.genes = params_to_genes(seed_params)
            ind.params = copy.deepcopy(seed_params)
            ind.params.design_type = design_type
            ind.params.angular_segments = 32
        else:
            ind = random_individual(design_type)
        population.append(ind)
    
    # Evaluate initial population (first pass — no SAV max yet)
    for i, ind in enumerate(population):
        population[i] = evaluate_individual(
            ind, material, fluid_density, fluid_viscosity, flow_velocity, weights)
        if progress_callback:
            progress_callback(0, n_generations, i / population_size * 0.1)

    # Compute population-level SAV max for dynamic normalisation in subsequent evals
    feasible_sav = [ind.obj_sav for ind in population if ind.feasible and ind.obj_sav > 0]
    sav_pop_max = max(feasible_sav) if feasible_sav else 0.0
    
    # Remove infeasible
    population = [ind for ind in population if ind.feasible]
    if len(population) < 4:
        raise ValueError("Too few feasible individuals in initial population. "
                         "Try a different design type or relax constraints.")
    
    # Main loop
    for gen in range(n_generations):
        # Sort and assign ranks
        fronts = non_dominated_sort(population)
        for front in fronts:
            crowding_distance(population, front)
        
        # Record history
        feasible = [ind for ind in population if ind.feasible]
        if feasible:
            best_composite = max(feasible, key=lambda x: x.composite_score)
            mean_composite = float(np.mean([ind.composite_score for ind in feasible]))
            result.generation_history.append({
                "generation": gen + 1,
                "best_composite": best_composite.composite_score,
                "mean_composite": mean_composite,
                "best_sav": best_composite.obj_sav,
                "best_porosity": best_composite.obj_porosity,
                "best_flow": best_composite.obj_flow,
                "pareto_front_size": len(fronts[0]) if fronts else 0,
                "population_size": len(feasible),
            })
            result.convergence_data.append(best_composite.composite_score)
            result.mean_convergence_data.append(mean_composite)
        
        if progress_callback:
            best_s = best_composite.composite_score if feasible else 0
            progress_callback(gen + 1, n_generations, (gen + 1) / n_generations)
        
        # Generate offspring
        offspring = []
        attempts = 0
        while len(offspring) < population_size and attempts < population_size * 5:
            attempts += 1
            p1 = tournament_select(population)
            p2 = tournament_select(population)
            c1, c2 = sbx_crossover(p1, p2, design_type=design_type)
            c1 = polynomial_mutation(c1, design_type=design_type)
            c2 = polynomial_mutation(c2, design_type=design_type)
            
            c1 = evaluate_individual(
                c1, material, fluid_density, fluid_viscosity, flow_velocity, weights,
                sav_population_max=sav_pop_max)
            c2 = evaluate_individual(
                c2, material, fluid_density, fluid_viscosity, flow_velocity, weights,
                sav_population_max=sav_pop_max)
            
            if c1.feasible:
                offspring.append(c1)
            if c2.feasible and len(offspring) < population_size:
                offspring.append(c2)
        
        # Combine and select next generation (elitism)
        combined = population + offspring
        combined = [ind for ind in combined if ind.feasible]
        
        fronts = non_dominated_sort(combined)
        for front in fronts:
            crowding_distance(combined, front)
        
        # Build next population
        next_population = []
        for front in fronts:
            if len(next_population) + len(front) <= population_size:
                next_population.extend([combined[i] for i in front])
            else:
                # Fill remaining slots by crowding distance
                remaining = population_size - len(next_population)
                sorted_front = sorted(
                    front,
                    key=lambda i: combined[i].crowding_distance,
                    reverse=True
                )
                next_population.extend([combined[i] for i in sorted_front[:remaining]])
                break
        
        population = next_population
        if len(population) < 4:
            break

        # Update SAV max for next generation
        gen_sav = [ind.obj_sav for ind in population if ind.feasible and ind.obj_sav > 0]
        if gen_sav:
            sav_pop_max = max(sav_pop_max, max(gen_sav))
    
    # Final Pareto front
    fronts = non_dominated_sort(population)
    result.population = population
    
    pareto_indices = fronts[0] if fronts else []
    result.pareto_front = [population[i] for i in pareto_indices]
    
    if result.pareto_front:
        result.best_composite = max(
            result.pareto_front, key=lambda x: x.composite_score)
    elif population:
        result.best_composite = max(population, key=lambda x: x.composite_score)
    
    return result


def ga_result_to_dataframe(result: GAResult):
    """Convert GA Pareto front to a pandas DataFrame for display."""
    import pandas as pd
    rows = []
    for i, ind in enumerate(result.pareto_front):
        g = ind.geo_metrics
        rows.append({
            "Rank": i + 1,
            "Composite Score": round(ind.composite_score, 4),
            "SA/V Ratio (mm⁻¹)": round(g.get("sav_ratio", 0), 4),
            "Porosity": round(g.get("porosity", 0), 4),
            "Flow Efficiency": round(g.get("flow_efficiency", 0), 4),
            "Buoyancy Score": round(g.get("buoyancy_score", 0), 4),
            "Surface Area (mm²)": round(g.get("surface_area", 0), 1),
            "Spec. SA (m²/m³)": round(g.get("specific_surface_area", 0), 1),
            "Outer Diam. (mm)": ind.params.outer_diameter,
            "Height (mm)": ind.params.height,
            "Num Fins": ind.params.num_fins,
            "Num Rings": ind.params.num_rings,
            "Num Spikes": ind.params.num_spikes,
            "Wall Thick. (mm)": ind.params.wall_thickness,
        })
    return pd.DataFrame(rows)
