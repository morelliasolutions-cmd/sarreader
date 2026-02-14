# SAR Address Extraction API

Service d'extraction automatique d'adresses depuis les fichiers SAR PDF (Swisscom).

## 📋 Description

Ce service analyse les fichiers PDF SAR pour extraire automatiquement :
- L'adresse complète
- Le code postal (NPA)
- La commune

Il recherche le pattern "Libellé d'adresse :" dans le PDF et extrait les informations structurées qui suivent.

## 🚀 Démarrage rapide

### Avec Docker

```bash
docker build -t sar-extractor .
docker run -p 5001:5001 sar-extractor
```

### En développement local

```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer .env
cp .env.example .env

# Lancer le serveur
python extract_sar_address.py
```

## 📡 API

### `GET /`
Documentation de l'API avec exemples d'utilisation.

### `GET /api/health`
Vérification de l'état du service.

**Réponse :**
```json
{
  "status": "healthy",
  "service": "SAR Address Extraction",
  "version": "1.0.0",
  "max_upload_mb": 50,
  "extraction_timeout_seconds": 60
}
```

### `POST /api/extract-sar-address`
Extraction d'adresse depuis un ou plusieurs PDF SAR.

**Requête :**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Field name: `pdfs` (un ou plusieurs fichiers)

**Exemple avec curl :**
```bash
curl -X POST http://localhost:5001/api/extract-sar-address \
  -F "pdfs=@document_sar.pdf"
```

**Réponse :**
```json
{
  "success": true,
  "results": [
    {
      "success": true,
      "file_name": "document_sar.pdf",
      "data": {
        "address": "av. du Simplon 4A",
        "npa": "1870",
        "commune": "Monthey"
      },
      "page": 1
    }
  ],
  "count": 1,
  "success_count": 1
}
```

## ⚙️ Configuration

Créez un fichier `.env` basé sur `.env.example` :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `PORT` | Port du serveur | `5001` |
| `SAR_EXTRACTION_HOST` | Hôte d'écoute | `0.0.0.0` |
| `ALLOWED_ORIGINS` | CORS origins (séparés par virgule) | `*` |
| `MAX_UPLOAD_SIZE_MB` | Taille max des uploads | `50` |
| `LOG_LEVEL` | Niveau de log (DEBUG, INFO, etc.) | `INFO` |

## 🔧 Déploiement sur EasyPanel

1. Créer une nouvelle application sur EasyPanel
2. Connecter ce repository GitHub
3. Configurer les variables d'environnement :
   - `PORT` → Automatique (EasyPanel)
   - `ALLOWED_ORIGINS` → Votre domaine frontend
4. Déployer

## 📦 Dépendances

- **Flask 3.0** : Framework web
- **pdfplumber 0.11** : Extraction de texte depuis PDF
- **flask-cors** : Gestion CORS
- **gunicorn** : Serveur WSGI production

## 🔒 Sécurité

- Pas d'authentification requise (service d'extraction uniquement)
- CORS configurable pour limiter les origines
- Limite de taille de fichiers configurable
- Aucune donnée sensible stockée

## 📝 Format PDF attendu

Le service recherche le pattern suivant dans les PDF :

```
Libellé d'adresse :
av. du Simplon 4A
1870 Monthey
```

## 🛠️ Développement

```bash
# Tests manuels
python extract_sar_address.py

# Le service est accessible sur http://localhost:5001
```

## 📄 Licence

ConnectFiber / Morellia © 2026
