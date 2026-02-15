# Guide de Configuration des Recommandations IA 🤖

## Vue d'ensemble

Le système de détection de fausses notes peut générer des recommandations personnalisées pour améliorer votre performance musicale en utilisant l'intelligence artificielle via OpenRouter.

## Étapes pour Activer les Recommandations IA

### 1. Créer un compte OpenRouter (Gratuit)

1. Allez sur https://openrouter.ai
2. Créez un compte (c'est gratuit)
3. Connectez-vous à votre compte

### 2. Obtenir une Clé API

1. Une fois connecté, allez sur https://openrouter.ai/keys
2. Cliquez sur "Create Key" ou "Generate Key"
3. Copiez votre clé API (elle commence par `sk-or-v1-...`)

### 3. Configurer la Clé API dans le Projet

#### Option A : Variables d'environnement système (Windows PowerShell)

```powershell
# Définir la variable d'environnement pour la session actuelle
$env:OPENROUTE_API_KEY="sk-or-v1-votre-cle-api-ici"

# Pour la rendre permanente (optionnel)
[System.Environment]::SetEnvironmentVariable('OPENROUTE_API_KEY', 'sk-or-v1-votre-cle-api-ici', 'User')
```

#### Option B : Fichier .env (Recommandé)

1. Créez un fichier `.env` à la racine du projet (`false-note-detection-ai/.env`)
2. Ajoutez votre clé API :

```bash
OPENROUTE_API_KEY=sk-or-v1-votre-cle-api-ici
```

**Note** : Le fichier `.env` est ignoré par Git pour des raisons de sécurité. Ne partagez jamais votre clé API publiquement.

### 4. Redémarrer les Services

Après avoir configuré la clé API, redémarrez le serveur FastAPI :

```bash
# Arrêter les services en cours (Ctrl+C dans les terminaux)
# Puis redémarrer :
python -m uvicorn app.main:app --reload --port 8000
streamlit run frontend/streamlit_app.py
```

### 5. Utiliser les Recommandations dans l'Interface

1. Ouvrez l'interface Streamlit : http://localhost:8501
2. Dans la barre latérale, **cochez la case "Generate practice recommendations"**
3. Uploadez vos fichiers audio et MIDI
4. Cliquez sur "Analyze"
5. Les recommandations IA apparaîtront dans une section dédiée après l'analyse

## Configuration Avancée

Vous pouvez également configurer ces variables d'environnement (optionnel) :

```bash
# Modèle IA à utiliser (par défaut: deepseek/deepseek-chat - gratuit)
DEEPSEEK_MODEL=deepseek/deepseek-chat

# Activer/désactiver les recommandations globalement
ENABLE_RECOMMENDATIONS=true

# URL de l'API OpenRouter (ne pas modifier sauf si vous utilisez un proxy)
OPENROUTE_API_URL=https://openrouter.ai/api/v1/chat/completions
```

## Vérification

Pour vérifier que la configuration fonctionne :

1. Vérifiez les logs du serveur FastAPI - vous ne devriez pas voir d'erreur "no OpenRouter API key configured"
2. Dans l'interface Streamlit, cochez la case des recommandations
3. Après l'analyse, une section "🎯 Practice Recommendations" devrait apparaître avec des conseils personnalisés

## Dépannage

### Les recommandations n'apparaissent pas

1. **Vérifiez que la clé API est correctement configurée** :
   ```python
   # Testez dans Python
   import os
   print(os.getenv("OPENROUTE_API_KEY"))
   ```

2. **Vérifiez que vous avez coché la case** dans l'interface Streamlit

3. **Vérifiez les logs du serveur** pour voir les erreurs éventuelles

4. **Vérifiez que votre clé API est valide** sur https://openrouter.ai/keys

### Erreur "Recommendations disabled: no OpenRouter API key configured"

Cela signifie que la variable d'environnement `OPENROUTE_API_KEY` n'est pas définie. Suivez l'étape 3 ci-dessus.

### Erreur "Failed to generate recommendations"

- Vérifiez votre connexion Internet
- Vérifiez que votre clé API est valide et n'a pas expiré
- Vérifiez que vous avez des crédits disponibles sur OpenRouter (le modèle DeepSeek est généralement gratuit)

## Modèles Disponibles

Par défaut, le système utilise `deepseek/deepseek-chat` qui est gratuit. Vous pouvez utiliser d'autres modèles disponibles sur OpenRouter en modifiant `DEEPSEEK_MODEL` :

- `deepseek/deepseek-chat` (gratuit, recommandé)
- `openai/gpt-3.5-turbo` (payant)
- `anthropic/claude-3-haiku` (payant)
- Et bien d'autres sur https://openrouter.ai/models

## Sécurité

⚠️ **Important** : Ne partagez jamais votre clé API publiquement. Le fichier `.env` est automatiquement ignoré par Git, mais vérifiez qu'il n'est pas commité par accident.

