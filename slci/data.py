"""Входные данные.

ВНИМАНИЕ: значения E[T], sigma_T, k, f_act, B — экспертные (синтетические)
допущения команды. Население и число ПВЗ добавлены для оценки регионального
бизнес-эффекта.
"""
from .model import DistrictNode

BASE_NODES = [
    DistrictNode("Городецкий", 4.5, 1.2, 1, 4, 0.20, population=83000, pvz_count=32),
    DistrictNode("Борский", 3.8, 1.8, 1, 5, 0.45, population=120000, pvz_count=50),
    DistrictNode("Семеновский", 6.2, 2.1, 1, 2, 0.40, population=45000, pvz_count=16),
    DistrictNode("Шахунский", 10.4, 3.5, 2, 1, 0.50, population=36000, pvz_count=12),
]

# (округ, название сценария, изменённые параметры)
SCENARIOS = [
    ("Шахунский", "Базовый", {}),
    ("Шахунский", "С1: частота 2 р/сут",
     dict(mean_time_h=9.2, std_time_h=3.0, freq_per_day=2)),
    ("Шахунский", "С2: прямой рейс (k=1)",
     dict(mean_time_h=7.8, std_time_h=2.2, transfers_k=1)),
    ("Шахунский", "С3: Северный кросс-док",
     dict(mean_time_h=6.8, std_time_h=1.6, transfers_k=1,
          freq_per_day=3, bridge_vulnerability=0.25)),
    # Семёнов — сам становится кросс-доком (перегрузка уходит, k=0)
    ("Семеновский", "Базовый", {}),
    ("Семеновский", "С3: Северный кросс-док",
     dict(mean_time_h=4.2, std_time_h=1.2, transfers_k=0,
          freq_per_day=3, bridge_vulnerability=0.25)),
]
