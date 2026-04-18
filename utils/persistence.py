"""
Session Persistence Module
Save and reload complete analysis sessions including all carrier results.
Enables working with all 16 carriers across multiple sessions.
"""

import json
import os
import pickle
from dataclasses import asdict
from typing import List, Dict, Any
from datetime import datetime


SESSION_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sessions")


def ensure_session_dir():
    os.makedirs(SESSION_DIR, exist_ok=True)


def save_session(
    session_name: str,
    results: List[Dict],
    all_carriers: List,
    params: Dict
) -> str:
    """
    Save the complete analysis session to disk.
    Returns the saved file path.
    """
    ensure_session_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{session_name.replace(' ', '_')}_{timestamp}.pkl"
    filepath = os.path.join(SESSION_DIR, filename)

    session_data = {
        "session_name": session_name,
        "timestamp": timestamp,
        "params": params,
        "results_count": len(results),
        "carriers_count": len(all_carriers),
        "results": results,
        "all_carriers": all_carriers,
    }

    with open(filepath, "wb") as f:
        pickle.dump(session_data, f)

    return filepath


def load_session(filepath: str) -> Dict:
    """Load a saved session from disk."""
    with open(filepath, "rb") as f:
        return pickle.load(f)


def list_sessions() -> List[Dict]:
    """List all saved sessions with metadata."""
    ensure_session_dir()
    sessions = []
    for fname in os.listdir(SESSION_DIR):
        if fname.endswith(".pkl"):
            fpath = os.path.join(SESSION_DIR, fname)
            try:
                with open(fpath, "rb") as f:
                    data = pickle.load(f)
                sessions.append({
                    "filename": fname,
                    "filepath": fpath,
                    "session_name": data.get("session_name", fname),
                    "timestamp": data.get("timestamp", ""),
                    "results_count": data.get("results_count", 0),
                    "carriers_count": data.get("carriers_count", 0),
                })
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


def export_session_csv(all_carriers: List, results: List[Dict]) -> str:
    """
    Export full session to CSV string for download.
    """
    import csv
    import io

    output = io.StringIO()
    fieldnames = [
        "design_id", "filename", "material", "rank", "composite_score",
        "is_pareto_optimal", "sav_ratio", "porosity", "specific_surface_area",
        "flow_efficiency", "buoyancy_score", "pressure_drop", "mass_transfer_coeff",
        "score_sav", "score_porosity", "score_flow", "score_buoyancy",
        "score_biofilm_affinity", "score_mechanical"
    ]

    # Add geometry fields from results
    geo_fields = [
        "surface_area", "volume", "bounding_box_volume",
        "hydraulic_diameter", "dim_x", "dim_y", "dim_z",
        "num_triangles", "is_watertight"
    ]
    all_fields = fieldnames + geo_fields

    writer = csv.DictWriter(output, fieldnames=all_fields, extrasaction='ignore')
    writer.writeheader()

    result_map = {r["design_id"]: r for r in results}

    for c in all_carriers:
        row = {f: getattr(c, f, "") for f in fieldnames}
        row["is_pareto_optimal"] = c.is_pareto_optimal

        # Add geometry data if available
        matching = result_map.get(c.design_id)
        if matching and "geo" in matching:
            geo = matching["geo"]
            for gf in geo_fields:
                row[gf] = getattr(geo, gf, "")

        writer.writerow(row)

    return output.getvalue()
