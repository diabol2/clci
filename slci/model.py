"""Математическая модель индекса SLCI."""
from dataclasses import dataclass, replace
import math
import pandas as pd
from scipy.stats import norm


@dataclass(frozen=True)
class DistrictNode:
    """Узел территории (муниципальный округ) с параметрами доставки."""
    name: str
    mean_time_h: float          # E[T], среднее время доставки, ч
    std_time_h: float           # sigma_T, стандартное отклонение времени, ч
    transfers_k: int            # k, число перегрузок/сортировок
    freq_per_day: float         # f_act, фактическая частота рейсов в сутки
    bridge_vulnerability: float # B, доля безальтернативных рёбер [0, 1]
    population: int = 0         # численность населения округа, чел. (Росстат)
    pvz_count: int = 0         # количество ПВЗ в округе, шт.
    def __post_init__(self):
        if self.mean_time_h <= 0 or self.std_time_h <= 0:
            raise ValueError("Время доставки и разброс должны быть > 0.")
        if self.transfers_k < 0:
            raise ValueError("Число перегрузок k не может быть отрицательным.")
        if self.freq_per_day <= 0:
            raise ValueError("Частота рейсов f_act должна быть > 0.")
        if not (0.0 <= self.bridge_vulnerability <= 1.0):
            raise ValueError("Доля безальтернативных рёбер B должна быть в [0, 1].")


    def with_changes(self, **kwargs) -> "DistrictNode":
        """Возвращает копию узла с изменёнными параметрами для сценариев."""
        return replace(self, **kwargs)


class SLCICalculator:
    """Калькулятор стохастического индекса логистической связанности."""

    def __init__(
        self,
        sla_hours: float = 12.0,
        f_req: float = 2.0,
        alpha: float = 0.15,
        beta: float = 0.20,
        gamma: float = 0.35,
    ):
        self.sla_hours = sla_hours
        self.f_req = f_req
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    @staticmethod
    def lognormal_params(mean_h: float, std_h: float) -> tuple[float, float]:
        """Перевод E[T] и sigma_T в параметры (mu, sigma) логнормального закона."""
        if mean_h <= 0 or std_h <= 0:
            raise ValueError("E[T] и sigma_T должны быть положительными.")
        var_rel = (std_h / mean_h) ** 2
        sigma2 = math.log(1.0 + var_rel)
        sigma = math.sqrt(sigma2)
        mu = math.log(mean_h) - 0.5 * sigma2
        return mu, sigma

    def sla_probability(self, mean_h: float, std_h: float) -> float:
        """Вероятность уложиться в окно SLA: P(T <= T_SLA)."""
        mu, sigma = self.lognormal_params(mean_h, std_h)
        z = (math.log(self.sla_hours) - mu) / sigma
        return float(norm.cdf(z))

    @staticmethod
    def zone(slci_value: float) -> str:
        """Классификация территории по уровню связанности."""
        if slci_value >= 0.75:
            return "высокая"
        if slci_value >= 0.50:
            return "умеренная"
        return "критическая"

    def components(self, node: DistrictNode) -> dict:
        """Полный расчёт компонентов и итогового значения SLCI для узла."""
        p_sla = self.sla_probability(node.mean_time_h, node.std_time_h)
        freq_penalty = math.exp(
            -self.alpha * node.transfers_k - self.beta * (self.f_req / node.freq_per_day)
        )
        bridge_factor = 1.0 - self.gamma * node.bridge_vulnerability
        slci = max(0.0, min(1.0, p_sla * freq_penalty * bridge_factor))

        return {
            "Округ": node.name,
            "Население": node.population,
            "ПВЗ": node.pvz_count,
            "P_SLA": round(p_sla, 3),
            "Penalty": round(freq_penalty, 3),
            "Topology": round(bridge_factor, 3),
            "SLCI": round(slci, 2),
            "SLCI_exact": slci,
            "Зона": self.zone(round(slci, 2)),
        }



    def evaluate_network(self, nodes: list[DistrictNode]) -> pd.DataFrame:
        """Сводная таблица расчёта по списку узлов."""
        rows = []
        for nd in nodes:
            comp = self.components(nd)
            comp.pop("SLCI_exact", None)
            rows.append(comp)
        return pd.DataFrame(rows)
