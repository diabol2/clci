"""Запуск: python run.py -> таблицы в консоль, CSV и графики в outputs/."""
from pathlib import Path

import pandas as pd

from slci import SLCICalculator
from slci.analysis import sector_impact, sensitivity, sla_robustness, validate
from slci.data import BASE_NODES, SCENARIOS

OUT = Path("outputs")
pd.set_option("display.width", 200)


def main():
    OUT.mkdir(exist_ok=True)
    calc = SLCICalculator(sla_hours=12.0)
    by_name = {n.name: n for n in BASE_NODES}

    base = calc.evaluate_network(BASE_NODES)
    base["Зона"] = base["SLCI"].map(calc.zone)
    print("=== 1. БАЗОВЫЙ РАСЧЁТ ===")
    print(base.to_string(index=False))
    base.to_csv(OUT / "base.csv", index=False, encoding="utf-8-sig")

    nodes, base_val = [], {}
    for district, title, chg in SCENARIOS:
        nodes.append(by_name[district].with_changes(name=f"{district}: {title}", **chg))
    scen = calc.evaluate_network(nodes)
    for i, (district, title, _) in enumerate(SCENARIOS):
        if title == "Базовый":
            base_val[district] = scen.loc[i, "SLCI"]
    scen["Прирост"] = [round(scen.loc[i, "SLCI"] - base_val[d], 2)
                       for i, (d, _, _) in enumerate(SCENARIOS)]
    scen["Зона"] = scen["SLCI"].map(calc.zone)
    print("\n=== 2. СЦЕНАРИИ (What-If) ===")
    print(scen.to_string(index=False))
    scen.to_csv(OUT / "scenarios.csv", index=False, encoding="utf-8-sig")

    print("\n=== 3. РЕГИОНАЛЬНЫЙ ЭФФЕКТ (население и ПВЗ) ===")
    c3_changes = {
        district: chg for district, title, chg in SCENARIOS
        if "С3:" in title
    }
    sector = sector_impact(calc, BASE_NODES, c3_changes)
    print(sector.to_string(index=False))
    sector.to_csv(OUT / "sector_impact.csv", index=False, encoding="utf-8-sig")

    print("\n=== 4. ПРОВЕРКА: аналитика vs Монте-Карло (2·10^5 выборок) ===")
    print(validate(calc, BASE_NODES).to_string(index=False))

    print("\n=== 5. ЧУВСТВИТЕЛЬНОСТЬ: Шахунский округ ===")
    print(sensitivity(calc, by_name["Шахунский"]).to_string(index=False))

    print("\n=== 6. УСТОЙЧИВОСТЬ К ВЫБОРУ SLA ===")
    rob = sla_robustness(BASE_NODES)
    print(rob)
    rob.to_csv(OUT / "sla_robustness.csv", encoding="utf-8-sig")

    from slci.plots import make_all
    shah_nodes = [n for n, (d, _, _) in zip(nodes, SCENARIOS) if d == "Шахунский"]
    make_all(calc, BASE_NODES, shah_nodes, OUT, focus_node=by_name["Шахунский"])
    print(f"\nГрафики и CSV сохранены в {OUT}/")


if __name__ == "__main__":
    main()
