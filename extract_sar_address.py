#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service simple d'extraction d'adresse depuis SAR PDF
Retourne juste: address, npa, commune en JSON
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import re
import io

app = Flask(__name__)
CORS(app)

def extract_address_from_sar_pdf(pdf_bytes: bytes, filename: str) -> dict:
    """Extrait adresse, NPA et commune depuis un PDF SAR"""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                # Chercher "Libellé d'adresse : xxxx"
                for i, line in enumerate(lines):
                    match = re.search(r"libell[eé]\s+d[\'\u2019]adresse\s*:\s*(.+)", line, re.IGNORECASE)
                    if match:
                        address = match.group(1).strip()
                        npa = None
                        commune = None
                        
                        # Chercher NPA+Commune dans les lignes suivantes
                        for j in range(1, min(6, len(lines) - i)):
                            candidate = lines[i + j].strip()
                            npa_match = re.match(r'^(\d{4,6})\s+(.+)$', candidate)
                            if npa_match:
                                npa = npa_match.group(1)[:4]  # Garder 4 chiffres
                                commune = npa_match.group(2).strip()
                                break
                        
                        if npa and commune:
                            return {
                                'success': True,
                                'data': {'address': address, 'npa': npa, 'commune': commune},
                                'file_name': filename
                            }
        
        return {'success': False, 'error': 'Format PDF non reconnu'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'SAR Address Extraction',
        'endpoint': '/api/extract-sar-address (POST multipart/form-data, field: pdfs)'
    })


@app.route('/api/extract-sar-address', methods=['POST'])
def extract_sar_address():
    """Reçoit PDF, retourne {address, npa, commune}"""
    try:
        if 'pdfs' not in request.files:
            return jsonify({'success': False, 'error': 'Aucun fichier fourni'}), 400
        
        files = request.files.getlist('pdfs')
        results = []
        
        for file in files:
            pdf_bytes = file.read()
            result = extract_address_from_sar_pdf(pdf_bytes, file.filename)
            results.append(result)
        
        success_count = sum(1 for r in results if r.get('success'))
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'success_count': success_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'SAR Extraction'})


if __name__ == '__main__':
    print("🚀 SAR Extraction Service starting on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
