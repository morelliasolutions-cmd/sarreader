#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service d'extraction d'adresse depuis les fichiers SAR PDF
Utilise pdfplumber pour extraire les informations d'adresse structurées

Format attendu dans le PDF :
  Libellé d'adresse :
  av. du Simplon 4A
  1870 Monthey

Auteur: ConnectFiber / Morellia
Date: 2026-02-14
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import re
import io
import logging
import os
from typing import Dict
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration du logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logging.basicConfig(
    level=getattr(logging, log_level),
    format=log_format
)
logger = logging.getLogger(__name__)

# Initialisation Flask
app = Flask(__name__)

# Configuration CORS depuis .env
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins)

# Configuration depuis .env
SAR_PORT = int(os.getenv('PORT', os.getenv('SAR_EXTRACTION_PORT', 5001)))
SAR_HOST = os.getenv('SAR_EXTRACTION_HOST', '0.0.0.0')
SAR_DEBUG = os.getenv('SAR_EXTRACTION_DEBUG', 'False').lower() == 'true'
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 50))
EXTRACTION_TIMEOUT = int(os.getenv('EXTRACTION_TIMEOUT_SECONDS', 60))

# Configuration taille max des uploads
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE_MB * 1024 * 1024

logger.info(f"🔧 Configuration chargée")
logger.info(f"   Port: {SAR_PORT}")
logger.info(f"   Host: {SAR_HOST}")
logger.info(f"   Debug: {SAR_DEBUG}")
logger.info(f"   CORS origins: {allowed_origins}")
logger.info(f"   Max upload: {MAX_UPLOAD_SIZE_MB}MB")


def extract_address_from_sar_pdf(pdf_bytes: bytes, filename: str) -> Dict:
    """
    Extrait l'adresse, le NPA et la commune depuis un fichier SAR PDF
    Version robuste avec plusieurs stratégies d'extraction
    
    Args:
        pdf_bytes: Contenu du PDF en bytes
        filename: Nom du fichier pour le logging
        
    Returns:
        Dict avec success, data (address, npa, commune) ou error
    """
    try:
        logger.info(f"📄 Traitement du fichier: {filename}")
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            # Parcourir toutes les pages
            for page_num, page in enumerate(pdf.pages, 1):
                logger.info(f"  📖 Analyse de la page {page_num}")
                
                # Extraire le texte de la page
                text = page.extract_text()
                
                if not text:
                    logger.warning(f"  ⚠️ Page {page_num} vide ou illisible")
                    continue
                
                lines = text.split('\n')
                
                # STRATÉGIE 1 : Chercher "Libellé d'adresse" et analyser les lignes suivantes
                for i, line in enumerate(lines):
                    # Chercher le pattern (insensible à la casse, accepte différents apostrophes)
                    # Unicode \u2019 = ', \u0027 = '
                    match = re.search(r"libell[eé]\s+d[\'\u2019]adresse\s*:\s*(.+)", line, re.IGNORECASE)
                    if match:
                        logger.info(f"  ✅ Pattern 'Libellé d'adresse' trouvé à la ligne {i}")
                        logger.info(f"  📍 Contenu de la ligne: {line}")
                        
                        # Extraire l'adresse sur la même ligne (après ":")
                        address_on_same_line = match.group(1).strip() if match.group(1) else None
                        
                        if address_on_same_line:
                            logger.info(f"  📍 Adresse sur même ligne: {address_on_same_line}")
                        
                        # Chercher dans les 5 lignes suivantes
                        address_line = address_on_same_line
                        npa = None
                        commune = None
                        
                        for j in range(1, min(6, len(lines) - i)):
                            candidate = lines[i + j].strip()
                            
                            # Ignorer les lignes vides ou trop courtes
                            if not candidate or len(candidate) < 3:
                                continue
                            
                            # Chercher un pattern NPA (4-6 chiffres) + Commune
                            npa_match = re.match(r'^(\d{4,6})\s+(.+)$', candidate)
                            if npa_match and not npa:
                                npa = npa_match.group(1).strip()
                                commune = npa_match.group(2).strip()
                                # Nettoyer le NPA (garder 4 chiffres)
                                if len(npa) > 4:
                                    npa = npa[:4]
                                logger.info(f"  📍 NPA+Commune trouvés: {npa} {commune}")
                                continue
                            
                            # Si pas encore d'adresse et que ce n'est pas un NPA, c'est l'adresse
                            if not address_line and not re.match(r'^\d{4,6}\s', candidate):
                                # Ignorer certains patterns communs non-adresses
                                if not re.match(r'^(données|contact|client|swisscom)', candidate.lower()):
                                    address_line = candidate
                                    logger.info(f"  📍 Adresse trouvée: {address_line}")
                        
                        # Si on a au moins le NPA/Commune, on retourne
                        if npa and commune:
                            result = {
                                'success': True,
                                'data': {
                                    'address': address_line or 'Non spécifiée',
                                    'npa': npa,
                                    'commune': commune
                                },
                                'page': page_num
                            }
                            logger.info(f"  ✅ Extraction réussie: {result['data']}")
                            return result
                
                # STRATÉGIE 2 : Chercher directement des patterns d'adresse suisse dans tout le texte
                logger.info(f"  🔍 Stratégie 2: recherche globale de NPA+Commune")
                for i, line in enumerate(lines):
                    # Chercher format: 1234 Ville ou 123456 Ville
                    npa_match = re.search(r'(\d{4,6})\s+([A-Z][a-zàâäéèêëïôùûü\-\s]+)', line)
                    if npa_match:
                        npa = npa_match.group(1)
                        commune = npa_match.group(2).strip()
                        
                        # Nettoyer le NPA
                        if len(npa) > 4:
                            npa = npa[:4]
                        
                        # Chercher une adresse dans les lignes précédentes (rue + numéro)
                        address_line = None
                        for j in range(max(0, i-3), i):
                            candidate = lines[j].strip()
                            # Pattern adresse: commence par mot + possiblement numéro
                            if re.match(r'^[A-Za-zàâäéèêëïôùûü].+\d+[A-Za-z]?$', candidate):
                                address_line = candidate
                                break
                        
                        logger.info(f"  📍 Trouvé (stratégie 2): NPA={npa}, Commune={commune}")
                        if address_line:
                            logger.info(f"  📍 Adresse associée: {address_line}")
                        
                        result = {
                            'success': True,
                            'data': {
                                'address': address_line or 'Non spécifiée',
                                'npa': npa,
                                'commune': commune
                            },
                            'page': page_num
                        }
                        return result
        
        # Si on arrive ici, aucune extraction n'a réussi
        logger.error(f"  ❌ Impossible d'extraire l'adresse de {filename}")
        return {
            'success': False,
            'error': 'Impossible d\'extraire l\'adresse du PDF. Format non reconnu.'
        }
        
    except Exception as e:
        logger.error(f"  ❌ Erreur lors de l'extraction: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Erreur lors de l\'extraction: {str(e)}'
        }


@app.route('/', methods=['GET'])
def home():
    """Page d'accueil avec documentation basique"""
    return jsonify({
        'service': 'SAR Address Extraction API',
        'version': '1.0.0',
        'endpoints': {
            '/': 'Cette page',
            '/api/health': 'Health check',
            '/api/extract-sar-address': 'Extraire une adresse depuis un PDF SAR (POST multipart/form-data avec fichier "pdfs")'
        },
        'usage': {
            'method': 'POST',
            'endpoint': '/api/extract-sar-address',
            'content_type': 'multipart/form-data',
            'field_name': 'pdfs',
            'response': {
                'success': True,
                'results': [
                    {
                        'success': True,
                        'file_name': 'exemple.pdf',
                        'data': {
                            'address': 'av. du Simplon 4A',
                            'npa': '1870',
                            'commune': 'Monthey'
                        },
                        'page': 1
                    }
                ],
                'count': 1,
                'success_count': 1
            }
        }
    })


@app.route('/api/extract-sar-address', methods=['POST'])
def extract_sar_address():
    """
    Endpoint pour extraire les adresses depuis un ou plusieurs fichiers SAR PDF
    
    Accepte multipart/form-data avec un ou plusieurs fichiers PDF sous la clé 'pdfs'
    
    Returns:
        JSON avec success, results (liste des extractions) et count
    """
    try:
        logger.info("🔄 Nouvelle requête d'extraction SAR")
        
        # Vérifier qu'il y a des fichiers
        if 'pdfs' not in request.files:
            logger.error("❌ Aucun fichier fourni")
            return jsonify({
                'success': False,
                'error': 'Aucun fichier fourni. Utilisez le champ "pdfs" pour envoyer vos fichiers PDF.'
            }), 400
        
        files = request.files.getlist('pdfs')
        
        if not files or len(files) == 0:
            logger.error("❌ Liste de fichiers vide")
            return jsonify({
                'success': False,
                'error': 'Liste de fichiers vide'
            }), 400
        
        logger.info(f"📥 {len(files)} fichier(s) reçu(s)")
        
        results = []
        
        # Traiter chaque fichier
        for file in files:
            filename = file.filename
            logger.info(f"--- Traitement de {filename} ---")
            
            # Lire le contenu du fichier
            pdf_bytes = file.read()
            
            # Extraire l'adresse
            extraction_result = extract_address_from_sar_pdf(pdf_bytes, filename)
            
            # Ajouter le nom du fichier au résultat
            extraction_result['file_name'] = filename
            
            results.append(extraction_result)
        
        # Compter les succès
        success_count = sum(1 for r in results if r.get('success', False))
        
        logger.info(f"✅ Extraction terminée: {success_count}/{len(results)} réussies")
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'success_count': success_count
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur serveur: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de santé pour vérifier que le service est actif"""
    return jsonify({
        'status': 'healthy',
        'service': 'SAR Address Extraction',
        'version': '1.0.0',
        'max_upload_mb': MAX_UPLOAD_SIZE_MB,
        'extraction_timeout_seconds': EXTRACTION_TIMEOUT
    })


if __name__ == '__main__':
    logger.info(f"🚀 Démarrage du service SAR Address Extraction sur {SAR_HOST}:{SAR_PORT}")
    app.run(
        host=SAR_HOST,
        port=SAR_PORT,
        debug=SAR_DEBUG
    )
