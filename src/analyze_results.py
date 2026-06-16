"""
Análise pós-processamento da frente de Pareto do NSGA-II.

Uso:
    # análise básica (tabela + gráfico da frente destacada)
    python -m src.analyze_results results-wind/118bus/pareto_nsga2_ieee118_<ts>.csv

    # + perfil de tensão por barra (requer --case)
    python -m src.analyze_results results-wind/118bus/pareto_nsga2_ieee118_<ts>.csv --voltage-profile

    # com vento (para casos rodados com --wind-config)
    python -m src.analyze_results ... --voltage-profile --wind-config wind_scenarios/ieee118_h12.json
"""

from pathlib import Path
import sys
import argparse
import csv
import json
import re

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Carregamento do CSV
# ---------------------------------------------------------------------------

def load_pareto_csv(csv_path: Path):
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    f1 = np.array([float(r["cost_dh"])             for r in rows])
    f2 = np.array([float(r["voltage_deviation_pu"]) for r in rows])
    f3 = np.array([float(r["emissions_ton_h"])      for r in rows])
    F  = np.column_stack([f1, f2, f3])
    return F, rows


# ---------------------------------------------------------------------------
# Pontos especiais
# ---------------------------------------------------------------------------

def find_special_points(F: np.ndarray) -> dict:
    idx_f1 = int(np.argmin(F[:, 0]))
    idx_f2 = int(np.argmin(F[:, 1]))
    idx_f3 = int(np.argmin(F[:, 2]))

    f_min   = F.min(axis=0)
    f_max   = F.max(axis=0)
    f_range = np.where(f_max - f_min > 0, f_max - f_min, 1.0)
    F_norm  = (F - f_min) / f_range
    idx_comp = int(np.argmin(np.linalg.norm(F_norm, axis=1)))

    return {
        "min_cost":      idx_f1,
        "min_vdev":      idx_f2,
        "min_emissions": idx_f3,
        "compromise":    idx_comp,
    }


LABELS = {
    "min_cost":      "Min custo",
    "min_vdev":      "Min desvio tens.",
    "min_emissions": "Min emissões",
    "compromise":    "Compromisso",
}

STYLES = {
    "min_cost":      {"marker": "^", "color": "tab:green",  "zorder": 5, "size": 150},
    "min_vdev":      {"marker": "s", "color": "tab:blue",   "zorder": 5, "size": 150},
    "min_emissions": {"marker": "D", "color": "tab:red",    "zorder": 5, "size": 150},
    "compromise":    {"marker": "*", "color": "tab:orange", "zorder": 6, "size": 220},
}


# ---------------------------------------------------------------------------
# Saídas: tabela, CSV resumo, gráfico da frente
# ---------------------------------------------------------------------------

def print_table(F: np.ndarray, indices: dict):
    header = f"{'Solução':<18}  {'Custo ($/h)':>13}  {'Vdev (pu)':>10}  {'Emissões (ton/h)':>17}  {'Sol #':>6}"
    sep = "=" * len(header)
    print(f"\n{sep}\n{header}\n{sep}")
    for key, idx in indices.items():
        f = F[idx]
        print(f"{LABELS[key]:<18}  {f[0]:>13.1f}  {f[1]:>10.4f}  {f[2]:>17.3f}  {idx+1:>6}")
    print(sep)
    print(f"{'Frente total':<18}  {F.shape[0]} soluções")


def save_summary_csv(F: np.ndarray, indices: dict, out_path: Path):
    with open(out_path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["point", "sol_idx", "cost_dh", "voltage_deviation_pu", "emissions_ton_h"])
        for key, idx in indices.items():
            f = F[idx]
            writer.writerow([key, idx + 1, f"{f[0]:.4f}", f"{f[1]:.6f}", f"{f[2]:.4f}"])
    print(f"CSV resumo salvo: {out_path}")


def plot_pareto_highlighted(F: np.ndarray, indices: dict, out_path: Path, case_name: str = ""):
    f1, f2, f3 = F[:, 0], F[:, 1], F[:, 2]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    title = f"Frente de Pareto NSGA-II — {case_name}" if case_name else "Frente de Pareto NSGA-II"
    fig.suptitle(title, fontsize=13, fontweight="bold")

    for ax, xdata, ydata, xlabel, ylabel, title_str in [
        (axes[0], f1, f3, "Custo de geração ($/h)", "Emissões (ton/h)",      "Custo × Emissões"),
        (axes[1], f1, f2, "Custo de geração ($/h)", "Desvio de tensão (pu)", "Custo × Desvio de Tensão"),
    ]:
        ax.scatter(xdata, ydata, c="lightgray", s=40, edgecolors="gray",
                   linewidths=0.4, zorder=2, label="Frente de Pareto")
        for key, idx in indices.items():
            st = STYLES[key]
            ax.scatter(xdata[idx], ydata[idx],
                       marker=st["marker"], c=st["color"], s=st["size"],
                       edgecolors="black", linewidths=0.6, zorder=st["zorder"],
                       label=LABELS[key])
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(title_str, fontsize=11)
        ax.legend(fontsize=8, loc="best")
        ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Gráfico da frente salvo: {out_path}")


# ---------------------------------------------------------------------------
# Perfil de tensão
# ---------------------------------------------------------------------------

def _bus_number(bus_name: str) -> int:
    m = re.match(r"(\d+)", bus_name)
    return int(m.group(1)) if m else 999


def run_and_read_voltages(config, rows, idx, wind_config=None):
    from src.opendss.opendss_interface import (
        create_dss, compile_circuit, solve_power_flow,
        get_all_bus_names, get_bus_voltage_pu_by_name,
        add_wind_generators, apply_wind_scenario,
        set_generator_kw,
    )

    dss = create_dss(allow_forms=config["allow_forms"])
    compile_circuit(dss, config["circuit_path"])
    if wind_config:
        add_wind_generators(dss, wind_config)
        apply_wind_scenario(dss, wind_config)
    solve_power_flow(dss)

    row = rows[idx]
    for gen in config["generators"]:
        col = f"{gen['name']}_kw"
        if col in row:
            set_generator_kw(dss, gen["name"], float(row[col]))
    solve_power_flow(dss)

    bus_names = get_all_bus_names(dss)
    bus_voltages = {}
    for name in bus_names:
        v_list = get_bus_voltage_pu_by_name(dss, name)
        if v_list:
            bus_voltages[name] = sum(v_list) / len(v_list)
    return bus_voltages


def plot_voltage_profile(profiles: dict, v_lower: float, v_upper: float,
                         out_path: Path, case_name: str = ""):
    all_buses = sorted(
        set(b for vdict in profiles.values() for b in vdict),
        key=_bus_number,
    )
    x = np.arange(len(all_buses))

    fig, ax = plt.subplots(figsize=(16, 5))
    title = f"Perfil de Tensão por Barra — {case_name}" if case_name else "Perfil de Tensão por Barra"
    ax.set_title(title, fontsize=13, fontweight="bold")

    for key, vdict in profiles.items():
        st = STYLES[key]
        y = [vdict.get(b, np.nan) for b in all_buses]
        ax.plot(x, y, marker=st["marker"], color=st["color"],
                markersize=4, linewidth=1.2, label=LABELS[key], zorder=st["zorder"])

    ax.axhline(v_lower, color="red", linestyle="--", linewidth=1.2,
               label=f"Lim. inferior ({v_lower} pu)")
    ax.axhline(v_upper, color="red", linestyle=":",  linewidth=1.2,
               label=f"Lim. superior ({v_upper} pu)")
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8, alpha=0.5, label="1.0 pu")

    tick_step = max(1, len(all_buses) // 20)
    ax.set_xticks(x[::tick_step])
    ax.set_xticklabels([all_buses[i] for i in range(0, len(all_buses), tick_step)],
                       rotation=45, ha="right", fontsize=7)
    ax.set_xlabel("Barra", fontsize=10)
    ax.set_ylabel("Tensão média (pu)", fontsize=10)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Gráfico de tensão salvo: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _detect_case(csv_path: Path) -> str:
    from src.configs import CONFIGS
    for case_key in CONFIGS:
        if case_key in csv_path.stem:
            return case_key
    return None


def main():
    parser = argparse.ArgumentParser(description="Análise da frente de Pareto NSGA-II")
    parser.add_argument("csv", type=Path, help="CSV da frente de Pareto (saída do nsga2.py)")
    parser.add_argument("--voltage-profile", action="store_true",
                        help="Gera perfil de tensão barra-a-barra para os 4 pontos especiais")
    parser.add_argument("--wind-config", type=Path, metavar="JSON",
                        help="JSON de vento usado na rodada (necessário para perfil de tensão com vento)")
    args = parser.parse_args()

    csv_path = args.csv
    if not csv_path.exists():
        print(f"Erro: arquivo não encontrado: {csv_path}")
        sys.exit(1)

    case_key  = _detect_case(csv_path)
    out_dir   = csv_path.parent
    stem_base = csv_path.stem.replace("pareto_nsga2_", "analysis_")

    print(f"\nAnálise: {csv_path.name}")
    print(f"Caso detectado: {case_key or '(desconhecido)'}")

    F, rows = load_pareto_csv(csv_path)
    print(f"Soluções carregadas: {len(F)}")

    indices = find_special_points(F)
    print_table(F, indices)

    save_summary_csv(F, indices, out_dir / f"{stem_base}.csv")
    plot_pareto_highlighted(F, indices, out_dir / f"{stem_base}.png", case_name=case_key or "")

    if args.voltage_profile:
        if not case_key:
            print("\nErro: caso não detectado no nome do arquivo. Informe o caso manualmente.")
            sys.exit(1)

        from src.configs import CONFIGS
        config = CONFIGS[case_key]

        wind_config = None
        if args.wind_config:
            with open(args.wind_config) as f:
                wind_config = json.load(f)

        profiles = {}
        for key, idx in indices.items():
            print(f"  Calculando tensões para '{LABELS[key]}' (sol #{idx+1})...")
            profiles[key] = run_and_read_voltages(config, rows, idx, wind_config)

        plot_voltage_profile(
            profiles,
            v_lower=config["voltage_lower_limit"],
            v_upper=config["voltage_upper_limit"],
            out_path=out_dir / f"{stem_base}_voltages.png",
            case_name=case_key,
        )


if __name__ == "__main__":
    main()
