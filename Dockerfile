# Image de base Python
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY extract_sar_address.py .

# Exposer le port (EasyPanel utilise PORT env var)
EXPOSE 5001

# Variables d'environnement par défaut
ENV PORT=5001
ENV SAR_EXTRACTION_HOST=0.0.0.0
ENV ALLOWED_ORIGINS=*
ENV MAX_UPLOAD_SIZE_MB=50
ENV LOG_LEVEL=INFO

# Lancer avec gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 2 --timeout 120 --access-logfile - --error-logfile - extract_sar_address:app
