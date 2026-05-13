"""
Session Persistence Module
Save and reload complete analysis sessions including all carrier results.
Enables working with all 16 carriers across multiple sessions.

Storage format: JSON (v2) — portable across Python versions and library updates.
Legacy pickle (.pkl) files are readable for one-way migration; new saves use .json.

Schema version history:
  v1  (pickle)  — original format, deprecated
  v2  (JSON)    — current; uses dataclass-to-dict serialization with type tags
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, fields
from typing import Any, Dict, List, Optional
from datetime import datetime

SESSION_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sessions")
SCHEMA_VERSION = 2


# ─── Helpers ──────────────────────────────────────────────────────────────────

def ensure_session_dir() -> None:
    os.makedirs(SESSION_DIR, exist_ok=True)


def _coerce_floats(d: dict) -> dict:
    """Recursively convert numpy scalars / booleans to plain Python types."""
    import numpy as np
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = _coerce_floats(v)
        elif isinstance(v, list):
            out[k] = [
                _coerce_floats(i) if isinstance(i, dict) else
                bool(i) if isinstance(i, (np.bool_,)) else
                int(i) if isinstance(i, (np.integer,)) else
                float(i) if isinstance(i, (np.floating,)) else i
                for i in v
            ]
        elif isinstance(v, (np.bool_,)):
            out[k] = bool(v)
        elif isinstance(v, (np.integer,)):
            out[k] = int(v)
        elif isinstance(v, (np.floating,)):
            out[k] = float(v)
        else:
            out[k] = v
    return out


def _carrier_score_to_dict(cs) -> dict:
    """Serialize a CarrierScore dataclass to a plain dict."""
    d = asdict(cs)
    return _coerce_floats(d)


def _dict_to_carrier_score(d: dict):
    """Deserialize a plain dict back to a CarrierScore dataclass."""
    from core.scoring import CarrierScore
    allowed = {f.name for f in fields(CarrierScore)}
    return CarrierScore(**{k: v for k, v in d.items() if k in allowed})


def _geo_to_dict(geo) -> dict:
    """Serialize a GeometryMetrics dataclass to a plain dict."""
    return _coerce_floats(asdict(geo))


def _dict_to_geo(d: dict):
    """Deserialize a plain dict back to a GeometryMetrics dataclass."""
    from core.geometry import GeometryMetrics
    allowed = {f.name for f in fields(GeometryMetrics)}
    return GeometryMetrics(**{k: v for k, v in d.items() if k in allowed})


def _flow_to_dict(flow) -> dict:
    return _coerce_floats(asdict(flow))


def _dict_to_flow(d: dict):
    from core.flow_analysis import FlowMetrics
    allowed = {f.name for f in fields(FlowMetrics)}
    return FlowMetrics(**{k: v for k, v in d.items() if k in allowed})


def _buoy_to_dict(buoy) -> dict:
    return _coerce_floats(asdict(buoy))


def _dict_to_buoy(d: dict):
    from core.buoyancy import BuoyancyMetrics
    allowed = {f.name for f in fields(BuoyancyMetrics)}
    return BuoyancyMetrics(**{k: v for k, v in d.items() if k in allowed})


def _result_to_dict(r: dict) -> dict:
    """Serialize a single result dict (containing dataclass objects) to JSON-safe dict."""
    return {
        "design_id":    r.get("design_id", ""),
        "filename":     r.get("filename", ""),
        "material":     r.get("material", ""),
        "geo":          _geo_to_dict(r["geo"])  if "geo"  in r else {},
        "flow":         _flow_to_dict(r["flow"]) if "flow" in r else {},
        "buoy":         _buoy_to_dict(r["buoy"]) if "buoy" in r else {},
        "carrier_score": _carrier_score_to_dict(r["carrier_score"]) if "carrier_score" in r else {},
    }


def _dict_to_result(d: dict) -> dict:
    """Deserialize a JSON dict back to a result dict with dataclass objects."""
    return {
        "design_id":    d.get("design_id", ""),
        "filename":     d.get("filename", ""),
        "material":     d.get("material", ""),
        "geo":          _dict_to_geo(d["geo"])   if d.get("geo")   else None,
        "flow":         _dict_to_flow(d["flow"]) if d.get("flow") else None,
        "buoy":         _dict_to_buoy(d["buoy"]) if d.get("buoy") else None,
        "carrier_score": _dict_to_carrier_score(d["carrier_score"]) if d.get("carrier_score") else None,
    }


# ─── Public API ───────────────────────────────────────────────────────────────

def save_session(
    session_name: str,
    results: List[Dict],
    all_carriers: List,
    params: Dict,
) -> str:
    """
    Save the complete analysis session to disk as JSON (schema v2).
    Returns the saved file path.
    """
    ensure_session_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = session_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{timestamp}.json"
    filepath = os.path.join(SESSION_DIR, filename)

    session_data = {
        "schema_version": SCHEMA_VERSION,
        "session_name":   session_name,
        "timestamp":      timestamp,
        "params":         params,
        "results_count":  len(results),
        "carriers_count": len(all_carriers),
        "results":        [_result_to_dict(r) for r in results],
        "all_carriers":   [_carrier_score_to_dict(c) for c in all_carriers],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)

    return filepath


def load_session(filepath: str) -> Dict:
    """
    Load a saved session from disk.
    Supports both v2 JSON and legacy v1 pickle files.
    """
    if filepath.endswith(".pkl"):
        return _load_pickle_legacy(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    version = raw.get("schema_version", 1)
    if version < 2:
        raise ValueError(
            f"Unsupported session schema version {version}. "
            "Re-save this session from a v2+ installation."
        )

    results    = [_dict_to_result(r) for r in raw.get("results", [])]
    carriers   = [_dict_to_carrier_score(c) for c in raw.get("all_carriers", [])]

    return {
        "schema_version": version,
        "session_name":   raw.get("session_name", ""),
        "timestamp":      raw.get("timestamp", ""),
        "params":         raw.get("params", {}),
        "results_count":  raw.get("results_count", len(results)),
        "carriers_count": raw.get("carriers_count", len(carriers)),
        "results":        results,
        "all_carriers":   carriers,
    }


def _load_pickle_legacy(filepath: str) -> Dict:
    """Read a legacy v1 pickle session (read-only migration path)."""
    import pickle
    with open(filepath, "rb") as f:
        data = pickle.load(f)
    # Mark it clearly as legacy so the UI can warn the user
    data["schema_version"] = 1
    data.setdefault("_legacy_pickle", True)
    return data


def list_sessions() -> List[Dict]:
    """List all saved sessions with metadata, newest first."""
    ensure_session_dir()
    sessions = []
    for fname in os.listdir(SESSION_DIR):
        if fname.endswith(".json") or fname.endswith(".pkl"):
            fpath = os.path.join(SESSION_DIR, fname)
            is_legacy = fname.endswith(".pkl")
            try:
                if is_legacy:
                    import pickle
                    with open(fpath, "rb") as f:
                        data = pickle.load(f)
                    meta = {
                        "filename":      fname,
                        "filepath":      fpath,
                        "session_name":  data.get("session_name", fname),
                        "timestamp":     data.get("timestamp", ""),
                        "results_count": data.get("results_count", 0),
                        "carriers_count": data.get("carriers_count", 0),
                        "is_legacy":     True,
                        "schema_version": 1,
                    }
                else:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    meta = {
                        "filename":      fname,
                        "filepath":      fpath,
                        "session_name":  data.get("session_name", fname),
                        "timestamp":     data.get("timestamp", ""),
                        "results_count": data.get("results_count", 0),
                        "carriers_count": data.get("carriers_count", 0),
                        "is_legacy":     False,
                        "schema_version": data.get("schema_version", 2),
                    }
                sessions.append(meta)
            except Exception:
                pass
    return sorted(sessions, key=lambda s: s["timestamp"], reverse=True)


def delete_session(filepath: str) -> bool:
    """Delete a saved session file."""
    try:
        os.remove(filepath)
        return True
    except Exception:
        return False


# ─── GA Result persistence ────────────────────────────────────────────────────

def save_ga_result(ga_result, session_name: str = "ga_run") -> str:
    """
    Persist a GAResult to a JSON file.
    Only lightweight scalars + geo_metrics dicts are stored; full Individual
    objects are reconstructed on load so the file stays small.
    Returns the saved file path.
    """
    ensure_session_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = session_name.replace(" ", "_").replace("/", "_")
    filename = f"{safe_name}_{timestamp}_ga.json"
    filepath = os.path.join(SESSION_DIR, filename)

    def _ind_to_dict(ind) -> dict:
        return {
            "genes":           ind.genes.tolist() if hasattr(ind.genes, "tolist") else list(ind.genes),
            "composite_score": float(ind.composite_score),
            "obj_sav":         float(ind.obj_sav),
            "obj_porosity":    float(ind.obj_porosity),
            "obj_flow":        float(ind.obj_flow),
            "obj_buoyancy":    float(ind.obj_buoyancy),
            "rank":            int(ind.rank),
            "feasible":        bool(ind.feasible),
            "geo_metrics":     {k: (float(v) if isinstance(v, (int, float)) else v)
                                for k, v in (ind.geo_metrics or {}).items()},
            "params": {
                "outer_diameter":   float(ind.params.outer_diameter) if ind.params else 0,
                "height":           float(ind.params.height) if ind.params else 0,
                "wall_thickness":   float(ind.params.wall_thickness) if ind.params else 0,
                "num_fins":         int(ind.params.num_fins) if ind.params else 0,
                "fin_thickness":    float(ind.params.fin_thickness) if ind.params else 0,
                "num_rings":        int(ind.params.num_rings) if ind.params else 0,
                "ring_gap":         float(ind.params.ring_gap) if ind.params else 0,
                "num_spikes":       int(ind.params.num_spikes) if ind.params else 0,
                "spike_height":     float(ind.params.spike_height) if ind.params else 0,
                "spike_base":       float(ind.params.spike_base) if ind.params else 0,
                "design_type":      str(ind.params.design_type) if ind.params else "",
            } if ind.params else {},
        }

    data = {
        "schema_version":    SCHEMA_VERSION,
        "type":              "ga_result",
        "timestamp":         timestamp,
        "session_name":      session_name,
        "design_type":       ga_result.design_type,
        "material":          ga_result.material,
        "n_generations":     ga_result.n_generations,
        "convergence_data":  [float(x) for x in ga_result.convergence_data],
        "mean_convergence_data": [float(x) for x in getattr(ga_result, "mean_convergence_data", [])],
        "generation_history": ga_result.generation_history,
        "pareto_front":      [_ind_to_dict(ind) for ind in ga_result.pareto_front],
        "population":        [_ind_to_dict(ind) for ind in ga_result.population],
        "best_composite":    _ind_to_dict(ga_result.best_composite) if ga_result.best_composite else None,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return filepath


def load_ga_result(filepath: str):
    """Load a saved GAResult from a JSON file. Returns a GAResult dataclass."""
    from core.genetic_algorithm import GAResult, Individual, genes_to_params
    import numpy as np

    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if raw.get("type") != "ga_result":
        raise ValueError("File is not a GA result — use load_session() for analysis sessions.")

    def _dict_to_ind(d: dict) -> Individual:
        ind = Individual()
        ind.genes = np.array(d.get("genes", []))
        ind.composite_score = d.get("composite_score", 0.0)
        ind.obj_sav         = d.get("obj_sav", 0.0)
        ind.obj_porosity    = d.get("obj_porosity", 0.0)
        ind.obj_flow        = d.get("obj_flow", 0.0)
        ind.obj_buoyancy    = d.get("obj_buoyancy", 0.0)
        ind.rank            = d.get("rank", 0)
        ind.feasible        = d.get("feasible", True)
        ind.geo_metrics     = d.get("geo_metrics", {})
        params_d = d.get("params", {})
        if params_d:
            ind.params = genes_to_params(ind.genes, params_d.get("design_type", "cross_flow"))
        return ind

    result = GAResult(
        design_type=raw.get("design_type", "cross_flow"),
        material=raw.get("material", "PLA"),
        n_generations=raw.get("n_generations", 0),
    )
    result.convergence_data    = raw.get("convergence_data", [])
    result.mean_convergence_data = raw.get("mean_convergence_data", [])
    result.generation_history  = raw.get("generation_history", [])
    result.pareto_front        = [_dict_to_ind(d) for d in raw.get("pareto_front", [])]
    result.population          = [_dict_to_ind(d) for d in raw.get("population", [])]
    result.best_composite      = _dict_to_ind(raw["best_composite"]) if raw.get("best_composite") else None

    return result


def list_ga_results() -> List[Dict]:
    """List all saved GA result files with metadata, newest first."""
    ensure_session_dir()
    results = []
    for fname in os.listdir(SESSION_DIR):
        if not fname.endswith("_ga.json"):
            continue
        fpath = os.path.join(SESSION_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append({
                "filename":      fname,
                "filepath":      fpath,
                "session_name":  data.get("session_name", fname),
                "timestamp":     data.get("timestamp", ""),
                "design_type":   data.get("design_type", ""),
                "material":      data.get("material", ""),
                "n_generations": data.get("n_generations", 0),
                "pareto_size":   len(data.get("pareto_front", [])),
            })
        except Exception:
            pass
    return sorted(results, key=lambda x: x["timestamp"], reverse=True)


def export_session_csv(all_carriers: List, results: List[Dict]) -> str:
    """Export full session to CSV string for download."""
    import csv
    import io

    output = io.StringIO()
    fieldnames = [
        "design_id", "filename", "material", "rank", "composite_score",
        "is_pareto_optimal", "sav_ratio", "porosity", "specific_surface_area",
        "flow_efficiency", "buoyancy_score", "pressure_drop", "mass_transfer_coeff",
        "score_sav", "score_porosity", "score_flow", "score_buoyancy",
        "score_biofilm_affinity", "score_mechanical",
    ]
    geo_fields = [
        "surface_area", "volume", "bounding_box_volume",
        "hydraulic_diameter", "dim_x", "dim_y", "dim_z",
        "num_triangles", "is_watertight",
    ]
    all_fields = fieldnames + geo_fields

    writer = csv.DictWriter(output, fieldnames=all_fields, extrasaction="ignore")
    writer.writeheader()

    result_map = {r["design_id"]: r for r in results}

    for c in all_carriers:
        row = {f: getattr(c, f, "") for f in fieldnames}
        row["is_pareto_optimal"] = c.is_pareto_optimal

        matching = result_map.get(c.design_id)
        if matching and matching.get("geo"):
            geo = matching["geo"]
            for gf in geo_fields:
                row[gf] = getattr(geo, gf, "")

        writer.writerow(row)

    return output.getvalue()
