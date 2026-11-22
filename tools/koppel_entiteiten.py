#!/usr/bin/env python3
"""Vervang placeholder-entiteiten in packages/ en dashboards/ door je echte entity_ids.

Gebruik (vanuit de root van de config-map):
    python3 tools/koppel_entiteiten.py --check          # toon wat (nog niet) gekoppeld is
    python3 tools/koppel_entiteiten.py                  # voer de vervanging uit
    python3 tools/koppel_entiteiten.py --verify http://homeassistant.local:8123 <TOKEN>
                                                        # controleer of de echte entiteiten bestaan

Enkel standaardbibliotheek, draait dus ook in de Terminal/SSH add-on van HAOS.
De mapping staat in entiteiten.yaml (formaat: 'placeholder: echte_id  # commentaar').
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPING_FILE = ROOT / "entiteiten.yaml"
TARGET_DIRS = ("packages", "dashboards")
ENTITY_RE = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")


def lees_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for nr, regel in enumerate(MAPPING_FILE.read_text(encoding="utf-8").splitlines(), 1):
        regel = regel.split("#", 1)[0].strip()
        if not regel:
            continue
        if ":" not in regel:
            sys.exit(f"entiteiten.yaml regel {nr}: verwacht 'placeholder: echte_id'")
        sleutel, waarde = (d.strip() for d in regel.split(":", 1))
        for naam in (sleutel, waarde):
            if naam and not ENTITY_RE.match(naam):
                sys.exit(f"entiteiten.yaml regel {nr}: '{naam}' is geen geldige entity_id")
        mapping[sleutel] = waarde
    return mapping


def bestanden() -> list[Path]:
    return sorted(p for d in TARGET_DIRS for p in (ROOT / d).rglob("*.yaml"))


def patroon(placeholder: str) -> re.Pattern[str]:
    # Hele entity_id: niet voorafgegaan door [\w.] en niet gevolgd door \w
    return re.compile(rf"(?<![\w.]){re.escape(placeholder)}(?!\w)")


def tel_voorkomens(mapping: dict[str, str]) -> dict[str, int]:
    teksten = [p.read_text(encoding="utf-8") for p in bestanden()]
    return {ph: sum(len(patroon(ph).findall(t)) for t in teksten) for ph in mapping}


def check(mapping: dict[str, str]) -> None:
    voorkomens = tel_voorkomens(mapping)
    open_ = [ph for ph, echt in mapping.items() if not echt and voorkomens[ph]]
    klaar = [ph for ph, echt in mapping.items() if echt and voorkomens[ph]]
    print(f"Te vervangen ({len(klaar)}):")
    for ph in klaar:
        print(f"  {ph:34} -> {mapping[ph]:40} ({voorkomens[ph]}x)")
    print(f"\nNog niet gekoppeld ({len(open_)}):")
    for ph in open_:
        print(f"  {ph:34} ({voorkomens[ph]}x)")
    weg = [ph for ph in mapping if not voorkomens[ph]]
    if weg:
        print(f"\nAl vervangen of niet (meer) gebruikt ({len(weg)}): {', '.join(weg)}")


def vervang(mapping: dict[str, str]) -> None:
    actief = {ph: echt for ph, echt in mapping.items() if echt and echt != ph}
    totaal = 0
    for pad in bestanden():
        tekst = oud = pad.read_text(encoding="utf-8")
        for ph, echt in actief.items():
            tekst, n = patroon(ph).subn(echt, tekst)
            totaal += n
        if tekst != oud:
            pad.write_text(tekst, encoding="utf-8")
            print(f"  aangepast: {pad.relative_to(ROOT)}")
    print(f"{totaal} vervangingen uitgevoerd.")
    print("Controleer daarna: Ontwikkelhulpmiddelen > YAML > Configuratie controleren, en herlaad.")


def verify(mapping: dict[str, str], url: str, token: str) -> None:
    req = urllib.request.Request(
        url.rstrip("/") + "/api/states",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        bestaand = {s["entity_id"] for s in json.load(resp)}
    fout = 0
    for ph, echt in mapping.items():
        doel = echt or ph
        if doel.startswith("notify."):
            continue  # notify is een actie, geen entiteit
        if doel not in bestaand:
            fout += 1
            print(f"  ONTBREEKT: {doel}" + ("" if echt else "  (nog niet gekoppeld)"))
    print("Alles gevonden." if not fout else f"{fout} entiteit(en) niet gevonden.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="enkel tonen, niets wijzigen")
    ap.add_argument("--verify", nargs=2, metavar=("URL", "TOKEN"), help="controleer entiteiten via REST API")
    args = ap.parse_args()

    mapping = lees_mapping()
    if args.verify:
        verify(mapping, *args.verify)
    elif args.check:
        check(mapping)
    else:
        vervang(mapping)


if __name__ == "__main__":
    main()
