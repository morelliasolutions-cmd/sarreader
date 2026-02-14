#!/usr/bin/env python3
import re

# Test de la ligne réelle du PDF
line = "Réseau de raccordement : 69MOH/Los17 Libellé d'adresse : av. du Simplon 4A "

print(f"Ligne testée: {line}")
print(f"Représentation bytes: {line.encode('utf-8')}")
print()

# Test différents regex
patterns = [
    r"libell[eé]\s+d['\u2019\u0027]adresse\s*:\s*(.+)",
    r"libell[eé] d.adresse\s*:\s*(.+)",
    r"libell.{1,2} d.adresse\s*:\s*(.+)",
    r"Libellé d'adresse\s*:\s*(.+)",
]

for i, pattern in enumerate(patterns, 1):
    print(f"Pattern {i}: {pattern}")
    match = re.search(pattern, line, re.IGNORECASE)
    if match:
        print(f"  ✅ MATCH! Groupes: {match.groups()}")
        print(f"  Adresse extraite: '{match.group(1).strip()}'")
    else:
        print(f"  ❌ Pas de match")
    print()
