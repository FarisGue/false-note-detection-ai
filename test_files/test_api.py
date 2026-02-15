"""Script pour tester l'API avec les fichiers de test."""

import sys
import requests
import json
from pathlib import Path

# Configurer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

test_dir = Path(__file__).parent
audio_path = test_dir / "test_guitar.wav"
midi_path = test_dir / "test_guitar.mid"

print("=" * 60)
print("TEST DE L'API - False Note Detection")
print("=" * 60)

# Vérifier que les fichiers existent
if not audio_path.exists():
    print(f"[ERREUR] Fichier audio non trouve: {audio_path}")
    sys.exit(1)

if not midi_path.exists():
    print(f"[ERREUR] Fichier MIDI non trouve: {midi_path}")
    sys.exit(1)

print(f"\nFichiers de test:")
print(f"  - Audio: {audio_path.name} ({audio_path.stat().st_size / 1024:.1f} KB)")
print(f"  - MIDI: {midi_path.name} ({midi_path.stat().st_size / 1024:.1f} KB)")

# Préparer la requête
api_url = "http://localhost:8000/upload/"
print(f"\nEnvoi vers l'API: {api_url}")

try:
    with open(audio_path, 'rb') as audio_file, open(midi_path, 'rb') as midi_file:
        files = {
            'audio': (audio_path.name, audio_file, 'audio/wav'),
            'reference': (midi_path.name, midi_file, 'audio/midi')
        }
        
        params = {
            'threshold_cents': 40.0,
            'ignore_silence': True
        }
        
        print("\n[INFO] Envoi de la requete...")
        response = requests.post(api_url, files=files, params=params, timeout=60)
        
        print(f"[INFO] Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "=" * 60)
            print("RESULTATS DE L'ANALYSE")
            print("=" * 60)
            
            print(f"\nDuree: {result.get('duration_seconds', 0):.2f} secondes")
            print(f"Frames totales: {result.get('total_frames', 0):,}")
            print(f"Frames correctes: {result.get('correct_frames', 0):,}")
            print(f"Frames incorrectes: {result.get('incorrect_frames', 0):,}")
            print(f"Precision: {result.get('accuracy_percent', 0):.2f}%")
            print(f"Erreur moyenne (cents): {result.get('mean_cents', 0):.2f}¢")
            print(f"Erreur maximale (cents): {result.get('max_cents', 0):.2f}¢")
            print(f"Seuil utilise: {result.get('threshold_cents', 0):.1f}¢")
            print(f"Nombre d'erreurs detectees: {len(result.get('error_indices', []))}")
            
            if len(result.get('error_indices', [])) > 0:
                print(f"\nPremieres erreurs (indices): {result['error_indices'][:10]}")
                if len(result['error_indices']) > 10:
                    print(f"... et {len(result['error_indices']) - 10} autres")
            
            # Sauvegarder les résultats
            result_path = test_dir / "test_results.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n[OK] Resultats sauvegardes dans: {result_path}")
            
            print("\n" + "=" * 60)
            print("[OK] TEST REUSSI!")
            print("=" * 60)
            
        else:
            print(f"\n[ERREUR] L'API a retourne une erreur:")
            print(f"Status: {response.status_code}")
            print(f"Reponse: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("\n[ERREUR] Impossible de se connecter a l'API.")
    print("Assurez-vous que le serveur FastAPI est demarre sur http://localhost:8000")
    sys.exit(1)
    
except requests.exceptions.Timeout:
    print("\n[ERREUR] Timeout - L'analyse prend trop de temps.")
    sys.exit(1)
    
except Exception as e:
    print(f"\n[ERREUR] Erreur inattendue: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

