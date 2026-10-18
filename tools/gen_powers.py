#!/usr/bin/env python3
"""
gen_powers.py — генерирует игровой реестр великих держав из канона Кенорландии.

Источник: ~/kenorlandia/ru/Кенорландия/страны.md (секция «Великие Державы»)
          + существа.md, Альянс.md (народа/валюта державы).

Выход:
  1) powers.json    — машинный реестр (для инструментов и ~/states)
  2) powers_data.sk — данные для Skript (сервер малины)

Использование:
    python3 gen_powers.py            # в текущий каталог
    python3 gen_powers.py --out DIR  # в каталог DIR

После генерации:
    scp powers_data.sk raspi:~/minecraft/plugins/Skript/scripts/
    ssh raspi 'tmux send-keys -t mc "sk reload all" Enter'

Правила (решения Матвея, 2026-10-16):
  - Поселения линуксоидов и монкехов в игре не участвуют.
  - ВСП — человеческая держава, но её мобы — чешуйницы.
  - Поселения желеек — желейки: слаймы и магма-кубы.
  - Остальные державы человеческие: жители, големы, торговцы, разбойники, разорители.
  - Флаги, гербы и гимны не берём (это арт, отдельная задача).
  - Юсиксландия и Балбесия — анклавы из ~/states, добавляются поверх канона.
"""
import argparse
import json
import os
import re
import sys

CANON = os.path.expanduser("~/kenorlandia/ru/Кенорландия")
DROP = {"Поселения линуксоидов", "Поселения монкехов"}
ANCADS = ["Юсиксландия", "Балбесия"]          # анклавы из ~/states

SLUG = {
    "Альянс": "alliance", "США": "usa", "Франция": "france", "Великобритания": "uk",
    "Германия": "germany", "Россия": "russia", "Китай": "china", "Кенорландия": "kenorlandia",
    "Бобия": "bobia", "Иран": "iran", "Турция": "turkey", "Курдистан": "kurdistan",
    "Саудовская Аравия": "saudi", "ОАЭ": "uae", "Катар": "qatar", "Израиль": "israel",
    "Марокко": "morocco", "Нигерия": "nigeria", "Эфиопия": "ethiopia", "Габон": "gabon",
    "Пакистан": "pakistan", "Индия": "india", "Бразилия": "brazil", "Япония": "japan",
    "Индонезия": "indonesia", "Южная Африка": "southafrica", "ДР Конго": "drcongo",
    "ВСП": "vsp", "Поселения желеек": "jelly",
    "Юсиксландия": "yusixland", "Балбесия": "balbesia",
}
ICON = {
    "Альянс": "⬛", "США": "🦅", "Франция": "🥐", "Великобритания": "🎩", "Германия": "🍺",
    "Россия": "🐻", "Китай": "🐉", "Кенорландия": "🏰", "Бобия": "🐒", "Иран": "🕌",
    "Турция": "🇹🇷", "Курдистан": "☀️", "Саудовская Аравия": "🕋", "ОАЭ": "🏙️", "Катар": "💎",
    "Израиль": "✡️", "Марокко": "🏜️", "Нигерия": "🥁", "Эфиопия": "🦁", "Габон": "🌴",
    "Пакистан": "🌙", "Индия": "🪷", "Бразилия": "⚽", "Япония": "🗾", "Индонезия": "🌋",
    "Южная Африка": "🦒", "ДР Конго": "💎", "ВСП": "🌭", "Поселения желеек": "🫠",
    "Юсиксландия": "🫠", "Балбесия": "⚡",
}
CURRENCY = {
    "США": "доллар (USD)", "Франция": "евро (EUR)", "Великобритания": "фунт (GBP)",
    "Германия": "евро (EUR)", "Россия": "рубль (RUB)", "Китай": "юань (CNY)", "Иран": "риал (IRR)",
    "Турция": "лира (TRY)", "Курдистан": "курдский динар (KRD)", "Саудовская Аравия": "риял (SAR)",
    "ОАЭ": "дирхам (AED)", "Катар": "риял (QAR)", "Израиль": "шекель (ILS)",
    "Марокко": "дирхам (MAD)", "Нигерия": "найра (NGN)", "Эфиопия": "быр (ETB)",
    "Габон": "франк КФА (XAF)", "Пакистан": "рупия (PKR)", "Индия": "рупия (INR)",
    "Бразилия": "реал (BRL)", "Япония": "иена (JPY)", "Индонезия": "рупия (IDR)",
    "Южная Африка": "рэнд (ZAR)", "ДР Конго": "конголезский франк (CDF)",
    "Альянс": "кредиты (CMBCRD)", "Кенорландия": "кенорский еллейдж (ELJ)",
    "Бобия": "бобийский рубль (BRB)", "ВСП": "жёльки (JLY)",
    "Юсиксландия": "жёльки (JLY)",
    "Балбесия": "жёльки (JLY)",
}
LOCATION = {
    "США": "Северная Америка", "Франция": "Западная Европа", "Великобритания": "Западная Европа",
    "Германия": "Западная Европа", "Россия": "Северная Евразия", "Китай": "Восточная Азия",
    "Иран": "Ближний Восток", "Турция": "Малая Азия", "Курдистан": "Ближний Восток",
    "Саудовская Аравия": "Аравия", "ОАЭ": "Аравия", "Катар": "Аравия", "Израиль": "Левант",
    "Марокко": "Северная Африка", "Нигерия": "Западная Африка", "Эфиопия": "Африканский Рог",
    "Габон": "Центральная Африка", "Пакистан": "Южная Азия", "Индия": "Южная Азия",
    "Бразилия": "Южная Америка", "Япония": "Восточная Азия", "Индонезия": "Юго-Восточная Азия",
    "Южная Африка": "Юг Африки", "ДР Конго": "Центральная Африка",
    "Альянс": "везде (цитадели)", "Бобия": "Кавказ", "Юсиксландия": "Кавказ", "Балбесия": "Кавказ",
    "ВСП": "Ближний Восток, Кавказ", "Поселения желеек": "везде, кроме тундр",
}
HUMAN_MOBS = ["villager", "iron_golem", "wandering_trader", "pillager", "vindicator", "ravager"]


def parse(path):
    """Вытаскивает из канона параметры блоков вида '## Имя' / '- **Имя**'."""
    blocks = {}
    for f in sorted(os.listdir(path)):
        if not f.endswith(".md"):
            continue
        lines = open(os.path.join(path, f), encoding="utf-8").read().split("\n")
        cur = f[:-3]
        for ln in lines:
            h = re.match(r'^#{2,4}\s+(.+?)\s*$', ln)
            if h:
                cur = h.group(1)
                blocks.setdefault(cur, {"file": f, "params": {}})
                continue
            b = re.match(r'^-\s+\*\*(.+?)\*\*(\s*\(.*)?$', ln)
            if b:
                cur = b.group(1).strip()
                blocks.setdefault(cur, {"file": f, "params": {}})
                continue
            m = re.match(r'^\s*-\s+\*\*(.+?)\*\*:\s*(.+?)\s*$', ln)
            if m:
                blocks.setdefault(cur, {"file": f, "params": {}})
                blocks[cur]["params"][m.group(1).strip()] = m.group(2).strip()
    return blocks


def independent_states(path):
    """Секция «Новые независимые государства»: имя -> {валюта, столица, iso, домен}."""
    lines = open(os.path.join(path, "страны.md"), encoding="utf-8").read().split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip() == "## Новые независимые государства"), None)
    if start is None:
        return {}
    out, cur = {}, None
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        m = re.match(r'^-\s+\*\*(.+?)\*\*(\s*\(.*)?$', ln)
        if m:
            cur = m.group(1).strip()
            out[cur] = {}
            continue
        m = re.match(r'^\s*-\s+(Валюта|Столица|ISO|Домен|Телефонный код):\s*(.+?)\s*$', ln)
        if m and cur:
            out[cur][m.group(1)] = m.group(2).strip().strip("`")
    return out


def powers_list(path):
    lines = open(os.path.join(path, "страны.md"), encoding="utf-8").read().split("\n")
    i0 = next(i for i, l in enumerate(lines) if l.strip() == "## Великие Державы")
    i1 = next(i for i, l in enumerate(lines) if i > i0 and l.startswith("## "))
    names = [re.sub(r'^-\s+', '', l).strip() for l in lines[i0 + 1:i1] if l.startswith("-")]
    return [n for n in names if n not in DROP]


def build(canon):
    blocks = parse(canon)
    indep = independent_states(canon)
    powers = []
    for name in powers_list(canon) + ANCADS:
        best = None
        for k, d in blocks.items():
            if k == name and (best is None or len(d["params"]) > len(best[1]["params"])):
                best = (k, d)
        pr = best[1]["params"] if best else {}
        ind = indep.get(name, {})
        kind = {"Поселения желеек": "jelly", "ВСП": "sausage"}.get(name, "human")
        mobs = {"jelly": ["slime", "magma_cube"], "sausage": ["silverfish"]}.get(kind, HUMAN_MOBS)
        powers.append({
            "name": name, "slug": SLUG[name], "icon": ICON[name], "kind": kind, "mobs": mobs,
            "ideology": pr.get("Идеология") or "канон молчит",
            "languages": pr.get("Официальные языки") or pr.get("Язык") or
                         ("желейный" if kind == "jelly" else
                          "колбаситский креольский" if kind == "sausage" else "английский"),
            "location": pr.get("Местоположение") or LOCATION.get(name, "—"),
            # валюта: канон -> реальная -> дефолт жёльки (решение Матвея)
            "currency": pr.get("Валюта") or ind.get("Валюта") or CURRENCY.get(name) or "жёльки (JLY)",
            "capital": pr.get("Столица") or ind.get("Столица") or "",
            "iso": (pr.get("ISO") or pr.get("ISO 3166-1") or ind.get("ISO") or "").strip("`"),
            "domain": (pr.get("Домен верхнего уровня страны") or ind.get("Домен") or "").strip("`"),
            "treasury": 200, "income": 3, "aggression": 1, "lands": 0,
        })
    return powers


def skript(powers):
    out = ["# powers_data.sk — АВТОГЕНЕРАЦИЯ из канона ~/kenorlandia (gen_powers.py).",
           "# Руками не править: меняй канон и перегенерируй.", "", "on script load:",
           "    set {p::count} to %d" % len(powers)]
    for p in powers:
        s = p["slug"]
        for k in ("name", "icon", "kind", "ideology", "languages", "location", "currency", "capital"):
            out.append(f'    set {{p::{s}::{k}}} to "{str(p[k]).replace(chr(34), chr(39))}"')
        out.append(f'    set {{p::{s}::mobs}} to "{" ".join(p["mobs"])}"')
        out.append(f'    add "{s}" to {{p::list::*}}')
        for k in ("treasury", "income", "aggression", "lands"):
            out.append(f'    set {{p::{s}::{k}}} to {p[k]}')
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    ap.add_argument("--canon", default=CANON)
    a = ap.parse_args()
    if not os.path.isdir(a.canon):
        sys.exit(f"нет канона: {a.canon}")
    powers = build(a.canon)
    os.makedirs(a.out, exist_ok=True)
    json.dump(powers, open(os.path.join(a.out, "powers.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(a.out, "powers_data.sk"), "w", encoding="utf-8").write(skript(powers))
    print(f"готово: {len(powers)} держав")
    for p in powers:
        print(f"  {p['icon']} {p['name']:22s} {p['slug']:12s} {p['kind']:8s} {p['currency']}")


if __name__ == "__main__":
    main()
