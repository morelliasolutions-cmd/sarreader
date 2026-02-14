# Déploiement sur EasyPanel

## 📦 Étapes de déploiement

### 1. Créer l'application sur EasyPanel

1. Se connecter sur EasyPanel
2. Créer une nouvelle application :
   - Type : **App**
   - Name : `sar-extractor` (ou autre nom)
   - Source : **GitHub Repository**

### 2. Connecter le repository GitHub

1. Sélectionner le repository : `morelliasolutions-cmd/sarreader`
2. Branch : `main`
3. Build method : **Dockerfile**
4. Dockerfile path : `Dockerfile` (racine du projet)

### 3. Configurer les variables d'environnement

Dans les settings de l'app, ajouter :

| Variable | Valeur recommandée |
|----------|-------------------|
| `PORT` | Laissez vide (EasyPanel configure automatiquement) |
| `ALLOWED_ORIGINS` | `https://agtelecom.connectfiber.ch,*` |
| `MAX_UPLOAD_SIZE_MB` | `50` |
| `LOG_LEVEL` | `INFO` |

### 4. Configurer le domaine

Option 1 : **Sous-domaine EasyPanel**
- Utiliser : `sar-extractor.yhmr4j.easypanel.host`
- HTTPS automatique ✅

Option 2 : **Domaine personnalisé**
- Configurer votre domaine (ex: `sar.connectfiber.ch`)
- Ajouter le CNAME pointant vers EasyPanel

### 5. Déployer

1. Cliquer sur **Deploy**
2. Attendre la fin du build (2-3 minutes)
3. Vérifier le health check : `https://[votre-domaine]/api/health`

### 6. Tester l'API

```bash
# Health check
curl https://sar-extractor.yhmr4j.easypanel.host/api/health

# Test extraction
curl -X POST https://sar-extractor.yhmr4j.easypanel.host/api/extract-sar-address \
  -F "pdfs=@votre_document_sar.pdf"
```

## 🔧 Mise à jour du frontend

Une fois l'application déployée, mettre à jour les URLs dans le frontend :

### Fichier : `js/webhook-config.js`

```javascript
const API_ENDPOINTS = {
    dev: 'http://localhost:5001',
    prod: 'https://sar-extractor.yhmr4j.easypanel.host'  // ⬅️ Mettre à jour ici
};
```

### Fichier : `mandats.html`

Rechercher et remplacer les URLs hardcodées :
- Ancien : `https://velox-sarpdf.yhmr4j.easypanel.host`
- Nouveau : `https://sar-extractor.yhmr4j.easypanel.host`

## 📊 Monitoring

Dans EasyPanel, vous pouvez :
- Voir les logs en temps réel
- Monitorer l'utilisation CPU/RAM
- Voir les requêtes HTTP

## 🔄 Redéploiement

Pour toute modification du code :
```bash
git add .
git commit -m "Description des changements"
git push origin main
```

EasyPanel redéploiera automatiquement.

## ⚠️ Troubleshooting

### Build failed
- Vérifier que `Dockerfile` est bien à la racine
- Vérifier que `requirements.txt` et `extract_sar_address.py` existent

### CORS errors
- Ajouter votre domaine frontend dans `ALLOWED_ORIGINS`
- Format : `https://domain1.com,https://domain2.com`

### 502 Bad Gateway
- Vérifier que le port configuré est correct
- EasyPanel utilise la variable `PORT` automatiquement

### Fichiers PDF non acceptés
- Vérifier `MAX_UPLOAD_SIZE_MB`
- Augmenter si nécessaire (default: 50MB)
