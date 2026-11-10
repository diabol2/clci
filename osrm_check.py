"""Реальная сверка с OSRM (нужен интернет).

Запуск:  python osrm_check.py
Берёт время в пути по дорогам хаб -> центр округа из публичного OSRM и
сравнивает с нашими E[T]. OSRM даёт время БЕЗ пробок и перегрузок, поэтому
ожидаем E[T] >= OSRM и тот же порядок территорий (ранговая корреляция).
Координаты приблизительные — проверьте по карте перед использованием.
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from slci.data import BASE_NODES

HUB = ("Нижний Новгород (хаб)", 56.3269, 44.0059)   # (lat, lon) — уточнить под реальный хаб
CENTERS = {
    "Городецкий": (56.6469, 43.4720),
    "Борский": (56.3578, 44.0794),
    "Семеновский": (56.7889, 44.4906),
    "Шахунский": (57.6747, 46.6122),
}
URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"


def osrm(lat2, lon2):
    url = URL.format(lon1=HUB[2], lat1=HUB[1], lon2=lon2, lat2=lat2)
    with urllib.request.urlopen(url, timeout=30) as r:
        route = json.load(r)["routes"][0]
    return route["duration"] / 3600, route["distance"] / 1000  # часы, км


def main():
    rows = []
    for n in BASE_NODES:
        h, km = osrm(*CENTERS[n.name])
        rows.append({"Округ": n.name, "OSRM, ч": round(h, 2), "OSRM, км": round(km, 0),
                     "Наше E[T], ч": n.mean_time_h,
                     "E[T]/OSRM": round(n.mean_time_h / h, 2),
                     "E[T] ≥ OSRM": n.mean_time_h >= h})
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    rho, _ = spearmanr(df["OSRM, ч"], df["Наше E[T], ч"])
    print(f"\nРанговая корреляция Спирмена: {rho:.2f}")
    Path("outputs").mkdir(exist_ok=True)
    df.to_csv("outputs/osrm_check.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
