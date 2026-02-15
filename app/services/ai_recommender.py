"""Service for generating AI recommendations using OpenRoute DeepSeek API."""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from ..config import OPENROUTE_API_KEY, OPENROUTE_API_URL, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)


def generate_recommendations(analysis_result: Dict[str, Any]) -> Optional[str]:
    """
    Generate AI recommendations for improving musical performance based on analysis results.
    
    Args:
        analysis_result: Dictionary containing the analysis results (from AnalysisResult model)
    
    Returns:
        Optional[str]: AI-generated recommendations text, or None if API call fails
    """
    if not OPENROUTE_API_KEY:
        logger.warning("OpenRoute API key not configured. Skipping AI recommendations.")
        return None
    
    try:
        # Prepare the prompt with analysis data
        prompt = _create_recommendation_prompt(analysis_result)
        
        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {OPENROUTE_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/FarisGue/false-note-detection-ai",
            "X-Title": "False Note Detection AI"
        }
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un expert en pédagogie musicale et en analyse de performance. Tu fournis des recommandations constructives et pratiques pour aider les musiciens à améliorer leur jeu."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Make the API request
        logger.info("Sending request to OpenRoute DeepSeek API for recommendations...")
        response = requests.post(
            OPENROUTE_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # Extract the recommendation text from the response
            # OpenRoute API typically returns: {"choices": [{"message": {"content": "..."}}]}
            if "choices" in result and len(result["choices"]) > 0:
                recommendation = result["choices"][0]["message"]["content"]
                logger.info("Successfully received AI recommendations")
                return recommendation
            else:
                logger.error(f"Unexpected API response structure: {result}")
                return None
        else:
            logger.error(f"OpenRoute API error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("OpenRoute API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling OpenRoute API: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating recommendations: {e}")
        return None


def _create_recommendation_prompt(analysis_result: Dict[str, Any]) -> str:
    """
    Create a detailed prompt for the AI based on analysis results.
    
    Args:
        analysis_result: Dictionary containing analysis results
    
    Returns:
        str: Formatted prompt for the AI
    """
    accuracy = analysis_result.get("accuracy_percent", 0.0)
    mean_cents = analysis_result.get("mean_cents", 0.0)
    max_cents = analysis_result.get("max_cents", 0.0)
    incorrect_frames = analysis_result.get("incorrect_frames", 0)
    total_frames = analysis_result.get("total_frames", 0)
    duration = analysis_result.get("duration_seconds", 0.0)
    threshold_cents = analysis_result.get("threshold_cents", 40.0)
    error_indices = analysis_result.get("error_indices", [])
    
    # Calculate error rate
    error_rate = (incorrect_frames / total_frames * 100) if total_frames > 0 else 0.0
    
    # Analyze error distribution
    error_times = [idx / 100.0 for idx in error_indices[:50]]  # First 50 errors
    error_pattern = "concentrées" if len(error_indices) > 0 and len(set([int(t) for t in error_times])) < len(error_indices) / 2 else "dispersées"
    
    prompt = f"""Analyse les résultats suivants d'une performance musicale et fournis des recommandations pratiques pour améliorer le jeu de l'artiste.

RÉSULTATS DE L'ANALYSE:
- Précision globale: {accuracy:.2f}%
- Erreur moyenne de hauteur: {mean_cents:.2f} cents
- Erreur maximale de hauteur: {max_cents:.2f} cents
- Nombre d'erreurs détectées: {incorrect_frames} sur {total_frames} frames
- Taux d'erreur: {error_rate:.2f}%
- Durée de la performance: {duration:.2f} secondes
- Seuil de détection utilisé: {threshold_cents} cents
- Distribution des erreurs: {error_pattern}

CONTEXTE:
- Les erreurs sont détectées lorsque la hauteur de la note jouée s'écarte de plus de {threshold_cents} cents de la note de référence.
- Une erreur de 50 cents correspond à environ un quart de ton.
- Une erreur de 100 cents correspond à un demi-ton (un demi-ton).

TÂCHE:
Fournis des recommandations concrètes et actionnables pour améliorer la performance, en te concentrant sur:
1. Les problèmes de justesse (si l'erreur moyenne est élevée)
2. Les problèmes de stabilité (si les erreurs sont dispersées)
3. Les sections problématiques (si les erreurs sont concentrées)
4. Des exercices pratiques spécifiques
5. Des conseils techniques adaptés au niveau de performance

Formatte ta réponse de manière claire et structurée, avec des sections si nécessaire. Sois encourageant et constructif."""

    return prompt

