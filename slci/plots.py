"""Графики для презентации (matplotlib)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .analysis import sensitivity

COLORS = {"высокая": "#2e9e5b", "умеренная": "#f0b429", "критическая": "#d64545"}
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 11})


def _zone_lines(ax, horizontal=False):
    for v in (0.50, 0.75):
        (ax.axvline if horizontal else ax.axhline)(v, ls="--", lw=1, color="gray", alpha=.7)


def plot_territories(calc, nodes, out: Path):
    data = sorted(((n.name, calc.components(n)["SLCI"]) for n in nodes), key=lambda x: x[1])
    names, vals = zip(*data)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.barh(names, vals, color=[COLORS[calc.zone(v)] for v in vals])
    _zone_lines(ax, horizontal=True)
    for b, v in zip(bars, vals):
        ax.text(v + 0.01, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center")
    ax.set_xlim(0, 1)
    ax.set_xlabel("SLCI (0 — критическая, 1 — высокая связанность)")
    ax.set_title("Сравнение территорий: базовое состояние")
    fig.tight_layout(); fig.savefig(out / "territories.png", dpi=200); plt.close(fig)


def plot_components(calc, nodes, out: Path):
    """Из-за чего именно теряется индекс."""
    import numpy as np
    comps = [calc.components(n) for n in nodes]
    labels = [n.name for n in nodes]
    keys = [("P_SLA", "P(уложиться в SLA)"), ("Penalty", "Штраф k и частоты"),
            ("Topology", "Топология (мосты)")]
    x = np.arange(len(nodes)); w = 0.26
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, (k, lab) in enumerate(keys):
        ax.bar(x + (i - 1) * w, [c[k] for c in comps], w, label=lab)
    ax.set_xticks(x, labels); ax.set_ylim(0, 1.05)
    ax.set_title("Компоненты индекса по территориям"); ax.legend(frameon=False, loc="lower left")
    fig.tight_layout(); fig.savefig(out / "components.png", dpi=200); plt.close(fig)


def plot_scenarios(calc, scen_nodes, out: Path):
    vals = [calc.components(n)["SLCI"] for n in scen_nodes]
    names = [n.name for n in scen_nodes]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.bar(names, vals, color=[COLORS[calc.zone(v)] for v in vals])
    _zone_lines(ax)
    for b, v in zip(bars, vals):
        d = round(v, 2) - round(vals[0], 2)
        txt = f"{v:.2f}" + (f"\n(+{d:.2f})" if d > 0.001 else "")
        ax.text(b.get_x() + b.get_width() / 2, v + 0.015, txt, ha="center")
    ax.set_ylim(0, 1); ax.set_ylabel("SLCI")
    ax.set_title("Шахунский округ: сравнение вариантов улучшения")
    plt.setp(ax.get_xticklabels(), rotation=12, ha="right")
    fig.tight_layout(); fig.savefig(out / "scenarios.png", dpi=200); plt.close(fig)


def plot_sensitivity(calc, node, out: Path):
    df = sensitivity(calc, node).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(df["Параметр"], df["ΔSLCI"], color="#3b6fd4")
    for y, v in enumerate(df["ΔSLCI"]):
        ax.text(v + 0.002, y, f"+{v:.3f}", va="center")
    ax.set_xlabel("Прирост SLCI")
    ax.set_title(f"Что даст больше всего: {node.name} округ")
    fig.tight_layout(); fig.savefig(out / "sensitivity.png", dpi=200); plt.close(fig)


def make_all(calc, base_nodes, scen_nodes, out: Path, focus_node=None):
    out.mkdir(exist_ok=True)
    plot_territories(calc, base_nodes, out)
    plot_components(calc, base_nodes, out)
    plot_scenarios(calc, scen_nodes, out)
    if focus_node is not None:
        plot_sensitivity(calc, focus_node, out)
