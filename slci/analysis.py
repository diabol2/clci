"""Проверки модели: Монте-Карло, чувствительность и региональный эффект."""
import numpy as np
import pandas as pd

from .model import DistrictNode, SLCICalculator


def monte_carlo_p(calc: SLCICalculator, node: DistrictNode,
                  n: int = 200_000, seed: int = 42) -> float:
    """Эмпирическая оценка P(T<=SLA) выборкой из логнормального закона."""
    mu, sigma = calc.lognormal_params(node.mean_time_h, node.std_time_h)
    rng = np.random.default_rng(seed)
    return float((rng.lognormal(mu, sigma, n) <= calc.sla_hours).mean())


def validate(calc: SLCICalculator, nodes) -> pd.DataFrame:
    """Сравнение аналитического Φ(z) с Монте-Карло."""
    rows = []
    for nd in nodes:
        a = calc.sla_probability(nd.mean_time_h, nd.std_time_h)
        m = monte_carlo_p(calc, nd)
        rows.append({"Округ": nd.name, "Аналитика": round(a, 4),
                     "Монте-Карло": round(m, 4), "|Δ|": round(abs(a - m), 4)})
    return pd.DataFrame(rows)


def sensitivity(calc: SLCICalculator, node: DistrictNode, rel: float = 0.2) -> pd.DataFrame:
    """Изменение SLCI при улучшении каждого параметра на rel (20%)
    — численная оценка «частных производных» индекса."""
    base = calc.components(node)["SLCI"]
    trials = {
        "E[T] −20%": dict(mean_time_h=node.mean_time_h * (1 - rel)),
        "σ_T −20%": dict(std_time_h=node.std_time_h * (1 - rel)),
        "Частота +20%": dict(freq_per_day=node.freq_per_day * (1 + rel)),
        "B −20%": dict(bridge_vulnerability=node.bridge_vulnerability * (1 - rel)),
        "Перегрузка k −1": dict(transfers_k=max(node.transfers_k - 1, 0)),
    }
    rows = [{"Параметр": k,
             "ΔSLCI": round(calc.components(node.with_changes(**v))["SLCI"] - base, 3)}
            for k, v in trials.items()]
    return pd.DataFrame(rows).sort_values("ΔSLCI", ascending=False).reset_index(drop=True)


def sla_robustness(nodes, slas=(8, 10, 12, 16, 24)) -> pd.DataFrame:
    """Как меняется индекс и ранжирование при другом окне SLA."""
    out = {}
    for s in slas:
        c = SLCICalculator(sla_hours=s)
        out[f"SLA={s}ч"] = [round(c.components(n)["SLCI"], 2) for n in nodes]
    return pd.DataFrame(out, index=[n.name for n in nodes])


def sector_impact(calc: SLCICalculator, base_nodes: list[DistrictNode],
                  scenario_changes: dict[str, dict]) -> pd.DataFrame:
    """Расчёт взвешенного по населению и числу ПВЗ индекса для всего сектора."""
    def _aggregate(nodes_list: list[DistrictNode], label: str) -> dict:
        total_pop = sum(n.population for n in nodes_list)
        total_pvz = sum(n.pvz_count for n in nodes_list)
        scores = [calc.components(n)["SLCI_exact"] for n in nodes_list]

        w_pop = sum(s * n.population for s, n in zip(scores, nodes_list)) / total_pop
        w_pvz = sum(s * n.pvz_count for s, n in zip(scores, nodes_list)) / total_pvz
        critical_pop = sum(n.population for s, n in zip(scores, nodes_list) if s < 0.50)

        return {
            "Состояние": label,
            "SLCI (взвеш. по населению)": round(w_pop, 3),
            "SLCI (взвеш. по ПВЗ)": round(w_pvz, 3),
            "Население в критич. зоне": critical_pop,
            "Всего населения": total_pop,
            "Всего ПВЗ": total_pvz,
        }

    updated_nodes = [
        n.with_changes(**scenario_changes[n.name]) if n.name in scenario_changes else n
        for n in base_nodes
    ]
    return pd.DataFrame([
        _aggregate(base_nodes, "Базовое состояние"),
        _aggregate(updated_nodes, "С3: Северный кросс-док"),
    ])
