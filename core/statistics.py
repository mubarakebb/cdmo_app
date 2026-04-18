"""
Statistical Analysis Module
Rigorous statistical comparison of carrier geometry families and materials.

Provides:
- Descriptive statistics per geometry group / material
- ANOVA / Kruskal-Wallis for group differences
- Post-hoc pairwise comparisons
- Effect size calculations (Cohen's d, eta-squared)
- Correlation analysis between geometric and performance metrics
- Regression models for predictive relationships

These analyses underpin the statistical validity of thesis findings.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from scipy import stats
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


@dataclass
class DescriptiveStats:
    """Descriptive statistics for a group."""
    group_name: str = ""
    n: int = 0
    mean: float = 0.0
    std: float = 0.0
    median: float = 0.0
    q1: float = 0.0
    q3: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    cv: float = 0.0   # coefficient of variation


@dataclass
class StatTestResult:
    """Result of a statistical significance test."""
    test_name: str = ""
    statistic: float = 0.0
    p_value: float = 0.0
    significant: bool = False
    alpha: float = 0.05
    interpretation: str = ""
    effect_size: float = 0.0
    effect_magnitude: str = ""   # small / medium / large


@dataclass
class CorrelationResult:
    """Pairwise correlation between two metrics."""
    var1: str = ""
    var2: str = ""
    pearson_r: float = 0.0
    pearson_p: float = 0.0
    spearman_r: float = 0.0
    spearman_p: float = 0.0
    strength: str = ""   # weak / moderate / strong
    direction: str = ""  # positive / negative


@dataclass 
class StatisticalReport:
    """Full statistical analysis report."""
    descriptive: Dict[str, Dict[str, DescriptiveStats]] = field(default_factory=dict)
    anova_results: Dict[str, StatTestResult] = field(default_factory=dict)
    pairwise: Dict[str, List[StatTestResult]] = field(default_factory=dict)
    correlations: List[CorrelationResult] = field(default_factory=list)
    regression_models: Dict[str, dict] = field(default_factory=dict)
    key_findings: List[str] = field(default_factory=list)


def descriptive_stats(values: List[float], group_name: str) -> DescriptiveStats:
    """Compute descriptive statistics for a list of values."""
    arr = np.array(values)
    ds = DescriptiveStats(group_name=group_name)
    ds.n = len(arr)
    if ds.n == 0:
        return ds
    ds.mean = float(np.mean(arr))
    ds.std = float(np.std(arr, ddof=1)) if ds.n > 1 else 0.0
    ds.median = float(np.median(arr))
    ds.q1 = float(np.percentile(arr, 25))
    ds.q3 = float(np.percentile(arr, 75))
    ds.min_val = float(np.min(arr))
    ds.max_val = float(np.max(arr))
    ds.cv = round(ds.std / abs(ds.mean) * 100, 2) if ds.mean != 0 else 0.0
    return ds


def cohens_d(group1: List[float], group2: List[float]) -> float:
    """Cohen's d effect size between two groups."""
    a, b = np.array(group1), np.array(group2)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    pooled_std = np.sqrt(((len(a) - 1) * np.var(a, ddof=1) +
                          (len(b) - 1) * np.var(b, ddof=1)) /
                         (len(a) + len(b) - 2))
    return float(abs(np.mean(a) - np.mean(b)) / pooled_std) if pooled_std > 0 else 0.0


def effect_magnitude(d: float) -> str:
    """Interpret Cohen's d magnitude."""
    d = abs(d)
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"


def eta_squared(f_stat: float, df_between: int, df_within: int) -> float:
    """Eta-squared effect size from ANOVA."""
    ss_between = f_stat * df_between
    ss_total = ss_between + df_within
    return ss_between / ss_total if ss_total > 0 else 0.0


def run_anova(groups: Dict[str, List[float]], metric_name: str,
              alpha: float = 0.05) -> StatTestResult:
    """
    One-way ANOVA (or Kruskal-Wallis if normality assumption violated).
    Automatically selects appropriate test.
    """
    result = StatTestResult(alpha=alpha)
    
    group_arrays = [np.array(v) for v in groups.values() if len(v) >= 2]
    if len(group_arrays) < 2:
        result.test_name = "Insufficient data"
        result.interpretation = "Need at least 2 groups with ≥2 observations each."
        return result
    
    # Test normality (Shapiro-Wilk) for each group
    all_normal = True
    for arr in group_arrays:
        if len(arr) >= 3:
            _, p_norm = stats.shapiro(arr)
            if p_norm < 0.05:
                all_normal = False
                break
    
    # Test homogeneity of variance (Levene)
    _, p_levene = stats.levene(*group_arrays)
    equal_variance = p_levene >= 0.05
    
    if all_normal and equal_variance and len(group_arrays) >= 2:
        # One-way ANOVA
        f_stat, p_val = stats.f_oneway(*group_arrays)
        result.test_name = "One-way ANOVA"
        result.statistic = round(float(f_stat), 4)
        result.p_value = round(float(p_val), 6)
        
        # Effect size (eta-squared)
        n_groups = len(group_arrays)
        n_total = sum(len(a) for a in group_arrays)
        df_between = n_groups - 1
        df_within = n_total - n_groups
        result.effect_size = round(eta_squared(f_stat, df_between, df_within), 4)
        result.effect_magnitude = effect_magnitude(result.effect_size * 2)
    else:
        # Kruskal-Wallis (non-parametric)
        h_stat, p_val = stats.kruskal(*group_arrays)
        result.test_name = "Kruskal-Wallis H-test"
        result.statistic = round(float(h_stat), 4)
        result.p_value = round(float(p_val), 6)
        result.effect_size = round(float(h_stat / (sum(len(a) for a in group_arrays) - 1)), 4)
        result.effect_magnitude = effect_magnitude(result.effect_size * 2)
    
    result.significant = result.p_value < alpha
    
    if result.significant:
        result.interpretation = (
            f"Statistically significant difference in {metric_name} between groups "
            f"(p={result.p_value:.4f} < {alpha}). Effect size: {result.effect_magnitude}.")
    else:
        result.interpretation = (
            f"No statistically significant difference in {metric_name} between groups "
            f"(p={result.p_value:.4f} ≥ {alpha}).")
    
    return result


def pairwise_comparisons(
    groups: Dict[str, List[float]], metric_name: str, alpha: float = 0.05
) -> List[StatTestResult]:
    """
    Pairwise Mann-Whitney U tests with Bonferroni correction.
    """
    results = []
    group_names = list(groups.keys())
    n_comparisons = len(group_names) * (len(group_names) - 1) // 2
    corrected_alpha = alpha / n_comparisons if n_comparisons > 0 else alpha
    
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            g1 = np.array(groups[group_names[i]])
            g2 = np.array(groups[group_names[j]])
            
            if len(g1) < 2 or len(g2) < 2:
                continue
            
            stat, p_val = stats.mannwhitneyu(g1, g2, alternative="two-sided")
            d = cohens_d(g1.tolist(), g2.tolist())
            
            r = StatTestResult(
                test_name=f"Mann-Whitney U ({group_names[i]} vs {group_names[j]})",
                statistic=round(float(stat), 4),
                p_value=round(float(p_val), 6),
                significant=p_val < corrected_alpha,
                alpha=corrected_alpha,
                effect_size=round(d, 4),
                effect_magnitude=effect_magnitude(d)
            )
            
            direction = "higher" if np.mean(g1) > np.mean(g2) else "lower"
            if r.significant:
                r.interpretation = (
                    f"{group_names[i]} has significantly {direction} {metric_name} "
                    f"than {group_names[j]} (p={p_val:.4f}, d={d:.3f}, "
                    f"{r.effect_magnitude} effect, Bonferroni-corrected α={corrected_alpha:.4f}).")
            else:
                r.interpretation = (
                    f"No significant difference in {metric_name} between "
                    f"{group_names[i]} and {group_names[j]} (p={p_val:.4f}).")
            
            results.append(r)
    
    return results


def compute_correlations(
    data: Dict[str, List[float]], alpha: float = 0.05
) -> List[CorrelationResult]:
    """
    Compute pairwise Pearson and Spearman correlations between all metrics.
    """
    results = []
    metric_names = list(data.keys())
    
    for i in range(len(metric_names)):
        for j in range(i + 1, len(metric_names)):
            v1 = np.array(data[metric_names[i]])
            v2 = np.array(data[metric_names[j]])
            
            min_len = min(len(v1), len(v2))
            if min_len < 3:
                continue
            v1, v2 = v1[:min_len], v2[:min_len]
            
            pr, pp = stats.pearsonr(v1, v2)
            sr, sp = stats.spearmanr(v1, v2)
            
            strength = "weak"
            if abs(pr) >= 0.7:
                strength = "strong"
            elif abs(pr) >= 0.4:
                strength = "moderate"
            
            cr = CorrelationResult(
                var1=metric_names[i],
                var2=metric_names[j],
                pearson_r=round(float(pr), 4),
                pearson_p=round(float(pp), 6),
                spearman_r=round(float(sr), 4),
                spearman_p=round(float(sp), 6),
                strength=strength,
                direction="positive" if pr > 0 else "negative"
            )
            results.append(cr)
    
    return sorted(results, key=lambda x: abs(x.pearson_r), reverse=True)


def linear_regression(
    x_vals: List[float], y_vals: List[float],
    x_name: str, y_name: str
) -> dict:
    """Simple linear regression with confidence intervals."""
    x = np.array(x_vals)
    y = np.array(y_vals)
    
    if len(x) < 3:
        return {}
    
    if np.std(x) == 0 or np.std(y) == 0:
        return {
            "x_name": x_name, "y_name": y_name,
            "slope": 0.0, "intercept": float(np.mean(y)),
            "r_squared": 0.0, "p_value": 1.0, "std_error": 0.0,
            "significant": False,
            "equation": f"{y_name} = constant (no variance in {x_name})",
            "interpretation": f"No variance in {x_name} — regression not applicable."
        }
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    return {
        "x_name": x_name,
        "y_name": y_name,
        "slope": round(float(slope), 6),
        "intercept": round(float(intercept), 6),
        "r_squared": round(float(r_value**2), 4),
        "p_value": round(float(p_value), 6),
        "std_error": round(float(std_err), 6),
        "significant": p_value < 0.05,
        "equation": f"{y_name} = {slope:.4f} × {x_name} + {intercept:.4f}",
        "interpretation": (
            f"{'Significant' if p_value < 0.05 else 'Non-significant'} linear relationship "
            f"(R²={r_value**2:.3f}, p={p_value:.4f}). "
            f"{abs(r_value**2)*100:.1f}% of variance in {y_name} explained by {x_name}."
        )
    }


def run_full_statistical_analysis(carriers) -> StatisticalReport:
    """
    Run complete statistical analysis on a population of CarrierScore objects.
    Groups by material and geometry family.
    """
    report = StatisticalReport()
    
    if not carriers:
        return report
    
    # ── Group by material ───────────────────────────────────────────────
    materials = list(set(c.material for c in carriers))
    metrics = {
        "SA/V Ratio": [c.sav_ratio for c in carriers],
        "Porosity": [c.porosity for c in carriers],
        "Flow Efficiency": [c.flow_efficiency for c in carriers],
        "Buoyancy Score": [c.buoyancy_score for c in carriers],
        "Composite Score": [c.composite_score for c in carriers],
        "Specific SA": [c.specific_surface_area for c in carriers],
    }
    
    # Descriptive stats per material
    report.descriptive["by_material"] = {}
    for metric_name, all_values in metrics.items():
        for mat in materials:
            mat_values = [c.__dict__.get(
                {"SA/V Ratio": "sav_ratio",
                 "Porosity": "porosity",
                 "Flow Efficiency": "flow_efficiency",
                 "Buoyancy Score": "buoyancy_score",
                 "Composite Score": "composite_score",
                 "Specific SA": "specific_surface_area"}.get(metric_name, "composite_score"), 0)
                for c in carriers if c.material == mat]
            
            key = f"{metric_name}|{mat}"
            report.descriptive["by_material"][key] = descriptive_stats(mat_values, mat)
    
    # ANOVA across materials for each metric
    for metric_name in metrics:
        attr = {"SA/V Ratio": "sav_ratio", "Porosity": "porosity",
                "Flow Efficiency": "flow_efficiency", "Buoyancy Score": "buoyancy_score",
                "Composite Score": "composite_score", "Specific SA": "specific_surface_area"
                }.get(metric_name, "composite_score")
        
        groups = {mat: [getattr(c, attr, 0) for c in carriers if c.material == mat]
                  for mat in materials}
        groups = {k: v for k, v in groups.items() if len(v) >= 2}
        
        if len(groups) >= 2:
            report.anova_results[metric_name] = run_anova(groups, metric_name)
            report.pairwise[metric_name] = pairwise_comparisons(groups, metric_name)
    
    # Correlation analysis
    corr_data = {
        "SA/V Ratio": [c.sav_ratio for c in carriers],
        "Porosity": [c.porosity for c in carriers],
        "Flow Efficiency": [c.flow_efficiency for c in carriers],
        "Buoyancy Score": [c.buoyancy_score for c in carriers],
        "Composite Score": [c.composite_score for c in carriers],
    }
    report.correlations = compute_correlations(corr_data)
    
    # Key regressions
    sav_vals = [c.sav_ratio for c in carriers]
    por_vals = [c.porosity for c in carriers]
    flow_vals = [c.flow_efficiency for c in carriers]
    comp_vals = [c.composite_score for c in carriers]
    
    report.regression_models["SAV→Composite"] = linear_regression(
        sav_vals, comp_vals, "SA/V Ratio", "Composite Score")
    report.regression_models["Porosity→Flow"] = linear_regression(
        por_vals, flow_vals, "Porosity", "Flow Efficiency")
    report.regression_models["Porosity→Composite"] = linear_regression(
        por_vals, comp_vals, "Porosity", "Composite Score")
    
    # Key findings narrative
    findings = []
    
    # Best material overall
    mat_means = {mat: np.mean([c.composite_score for c in carriers if c.material == mat])
                 for mat in materials}
    best_mat = max(mat_means, key=mat_means.get) if mat_means else "N/A"
    findings.append(
        f"{best_mat} achieves the highest mean composite score "
        f"({mat_means.get(best_mat, 0):.3f}) across all evaluated geometries.")
    
    # ANOVA significance
    comp_anova = report.anova_results.get("Composite Score")
    if comp_anova:
        if comp_anova.significant:
            findings.append(
                f"Material type has a statistically significant effect on composite performance "
                f"({comp_anova.test_name}, p={comp_anova.p_value:.4f}, "
                f"{comp_anova.effect_magnitude} effect).")
        else:
            findings.append(
                f"No statistically significant difference in composite performance "
                f"between materials (p={comp_anova.p_value:.4f}), suggesting geometry "
                f"dominates material choice for this design space.")
    
    # Strongest correlation
    if report.correlations:
        top_corr = report.correlations[0]
        findings.append(
            f"Strongest correlation: {top_corr.var1} vs {top_corr.var2} "
            f"(Pearson r={top_corr.pearson_r:.3f}, {top_corr.strength} {top_corr.direction} "
            f"relationship, p={top_corr.pearson_p:.4f}).")
    
    # Best regression
    best_reg = max(
        [v for v in report.regression_models.values() if v],
        key=lambda x: x.get("r_squared", 0), default=None)
    if best_reg:
        findings.append(
            f"Best predictive model: {best_reg['equation']} "
            f"(R²={best_reg['r_squared']:.3f}).")
    
    report.key_findings = findings
    return report
