#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script de test pour analyser la structure du SAR.pdf"""

import pdfplumber

pdf_path = r"c:\Users\etien\OneDrive\Morellia\connectfiber\agtelecom\SAR.pdf"

print("=" * 80)
print("ANALYSE DU PDF SAR")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        print(f"\n{'='*80}")
        print(f"PAGE {page_num}")
        print(f"{'='*80}")
        
        text = page.extract_text()
        
        if text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                print(f"{i:3d}: {line}")
        else:
            print("(page vide)")

print("\n" + "=" * 80)
print("FIN DE L'ANALYSE")
print("=" * 80)
