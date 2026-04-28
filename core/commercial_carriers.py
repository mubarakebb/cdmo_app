"""
Commercial MBBR Carrier Benchmarks
Published specifications used for direct comparison with CDMO designs.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CommercialCarrier:
    """Specifications for a commercial MBBR carrier."""
    name: str
    manufacturer: str
    material: str
    diameter_mm: float
    height_mm: float
    sa_v_ratio: float                  # Converted from specific surface area estimate, mm^-1
    specific_surface_area: float       # m2/m3
    sa_basis: str                      # active / effective / protected
    density_g_cm3: float
    porosity: float
    biofilm_affinity: float
    clogging_risk: str
    source_label: str = "Published commercial carrier"
    notes: str = ""

    @property
    def dimensions_label(self) -> str:
        """Return a compact diameter x height display string."""
        return f"{self.diameter_mm:.0f} x {self.height_mm:.0f} mm"


REFERENCE_URLS: List[str] = [
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6985336/",
    "http://technomaps.veoliawatertechnologies.com/anita/en/anita_mox.htm",
    "https://www.mbbr-media.com/product/mutagbiochip/",
]


PUBLISHED_MBBR_REFERENCES: List[str] = REFERENCE_URLS


PUBLISHED_MBBR_TABLE_MD = """
| Carrier | Manufacturer | Material | Diameter (mm) | Height (mm) | SA/V (mm^-1) | Specific SA (m^2/m^3) | SA Basis | Density (g/cm^3) | Porosity | Biofilm Affinity | Clogging Risk |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| AnoxKaldnes K1 | AnoxKaldnes | HDPE | 10.0 | 7.0 | 0.0714 | 500.0 | effective | 0.96 | 0.85 | 0.75 | Medium |
| AnoxKaldnes K3 | AnoxKaldnes | HDPE | 25.0 | 10.0 | 0.0500 | 500.0 | protected | 0.96 | 0.85 | 0.74 | Low |
| AnoxKaldnes K5 | AnoxKaldnes | HDPE | 35.0 | 2.0 | 0.1143 | 800.0 | protected | 0.96 | 0.87 | 0.78 | Medium |
| AnoxKaldnes BiofilmChip M | AnoxKaldnes | HDPE | 48.0 | 3.0 | 0.1667 | 1200.0 | protected | 0.96 | 0.90 | 0.80 | Medium |
| Mutag BioChip | MUTAG | PE | 30.0 | 3.0 | 0.6111 | 5500.0 | active | 0.95 | 0.92 | 0.82 | Low |
""".strip()


def build_published_mbbr_table_md(carriers: List[CommercialCarrier] | None = None) -> str:
    """Render the published carrier list as a markdown table."""
    rows = carriers or COMMERCIAL_CARRIERS
    header = (
        "| Carrier | Manufacturer | Material | Diameter (mm) | Height (mm) | SA/V (mm^-1) | "
        "Specific SA (m^2/m^3) | SA Basis | Density (g/cm^3) | Porosity | Biofilm Affinity | Clogging Risk |"
    )
    separator = "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |"
    lines = [header, separator]
    for carrier in rows:
        lines.append(
            f"| {carrier.name} | {carrier.manufacturer} | {carrier.material} | {carrier.diameter_mm:.1f} | "
            f"{carrier.height_mm:.1f} | {carrier.sa_v_ratio:.4f} | {carrier.specific_surface_area:.1f} | "
            f"{carrier.sa_basis} | {carrier.density_g_cm3:.2f} | {carrier.porosity:.2f} | "
            f"{carrier.biofilm_affinity:.2f} | {carrier.clogging_risk} |"
        )
    return "\n".join(lines)


# Published commercial carrier data requested by user.
COMMERCIAL_CARRIERS: List[CommercialCarrier] = [
    CommercialCarrier(
        name="AnoxKaldnes K1",
        manufacturer="AnoxKaldnes",
        material="HDPE",
        diameter_mm=10.0,
        height_mm=7.0,
        sa_v_ratio=0.0714,
        specific_surface_area=500.0,
        sa_basis="effective",
        density_g_cm3=0.96,
        porosity=0.85,
        biofilm_affinity=0.75,
        clogging_risk="Medium",
        notes="Published as 500 m2/m3 effective area.",
    ),
    CommercialCarrier(
        name="AnoxKaldnes K3",
        manufacturer="AnoxKaldnes",
        material="HDPE",
        diameter_mm=25.0,
        height_mm=10.0,
        sa_v_ratio=0.0500,
        specific_surface_area=500.0,
        sa_basis="protected",
        density_g_cm3=0.96,
        porosity=0.85,
        biofilm_affinity=0.74,
        clogging_risk="Low",
        notes="Published as 500 m2/m3 protected area.",
    ),
    CommercialCarrier(
        name="AnoxKaldnes K5",
        manufacturer="AnoxKaldnes",
        material="HDPE",
        diameter_mm=35.0,
        height_mm=2.0,
        sa_v_ratio=0.1143,
        specific_surface_area=800.0,
        sa_basis="protected",
        density_g_cm3=0.96,
        porosity=0.87,
        biofilm_affinity=0.78,
        clogging_risk="Medium",
        notes="Published as 800 m2/m3 protected area.",
    ),
    CommercialCarrier(
        name="AnoxKaldnes BiofilmChip M",
        manufacturer="AnoxKaldnes",
        material="HDPE",
        diameter_mm=48.0,
        height_mm=3.0,
        sa_v_ratio=0.1667,
        specific_surface_area=1200.0,
        sa_basis="protected",
        density_g_cm3=0.96,
        porosity=0.90,
        biofilm_affinity=0.80,
        clogging_risk="Medium",
        notes="Published as 1200 m2/m3 protected area.",
    ),
    CommercialCarrier(
        name="Mutag BioChip",
        manufacturer="MUTAG",
        material="PE",
        diameter_mm=30.0,
        height_mm=3.0,
        sa_v_ratio=0.6111,
        specific_surface_area=5500.0,
        sa_basis="active",
        density_g_cm3=0.95,
        porosity=0.92,
        biofilm_affinity=0.82,
        clogging_risk="Low",
        notes="Published as 5500 m2/m3 active area; 30 mm disc.",
    ),
]


def get_carrier_by_name(name: str) -> CommercialCarrier:
    """Retrieve a carrier by exact name match."""
    for c in COMMERCIAL_CARRIERS:
        if c.name == name:
            return c
    return None


def compare_to_commercial(
    user_sav: float,
    user_porosity: float,
    user_specific_sa: float
) -> Dict:
    """Compare a CDMO design against commercial carriers."""
    all_sav = [c.sa_v_ratio for c in COMMERCIAL_CARRIERS]
    all_por = [c.porosity for c in COMMERCIAL_CARRIERS]
    all_ssa = [c.specific_surface_area for c in COMMERCIAL_CARRIERS]

    def percentile_rank(value: float, distribution: List[float]) -> float:
        if not distribution:
            return 50.0
        ranked = sum(1 for v in distribution if v <= value)
        return (ranked / len(distribution)) * 100.0

    return {
        "user_sav": user_sav,
        "mean_commercial_sav": sum(all_sav) / len(all_sav),
        "sav_percentile": percentile_rank(user_sav, all_sav),
        "user_porosity": user_porosity,
        "mean_commercial_porosity": sum(all_por) / len(all_por),
        "porosity_percentile": percentile_rank(user_porosity, all_por),
        "user_specific_sa": user_specific_sa,
        "mean_commercial_ssa": sum(all_ssa) / len(all_ssa),
        "ssa_percentile": percentile_rank(user_specific_sa, all_ssa),
        "commercial_count": len(COMMERCIAL_CARRIERS),
    }
