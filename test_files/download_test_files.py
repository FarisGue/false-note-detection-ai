"""Script pour télécharger des fichiers de test audio et MIDI."""

import sys
import requests
import os
from pathlib import Path

# Configurer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Créer le dossier de test
test_dir = Path(__file__).parent
test_dir.mkdir(exist_ok=True)

# URLs de fichiers de test publics (exemples)
# Note: Ces URLs peuvent ne pas être disponibles, on utilisera une approche alternative
test_urls = {
    "guitar_audio": None,  # À remplir si on trouve une source
    "guitar_midi": None
}

print("Recherche de fichiers de test...")

# Alternative: Créer des fichiers de test synthétiques
# Pour un vrai test, on peut utiliser pretty_midi pour créer un MIDI simple
# et générer un audio correspondant

try:
    import pretty_midi
    import numpy as np
    import soundfile as sf
    
    print("Création de fichiers de test synthétiques...")
    
    # Créer un MIDI simple avec quelques notes de guitare
    midi = pretty_midi.PrettyMIDI()
    guitar = pretty_midi.Instrument(program=24)  # Program 24 = Acoustic Guitar (nylon)
    
    # Ajouter quelques notes (gamme de Do majeur)
    notes = [
        (60, 0.0, 1.0),   # C4
        (64, 1.0, 2.0),   # E4
        (67, 2.0, 3.0),   # G4
        (72, 3.0, 4.0),   # C5
        (64, 4.0, 5.0),   # E4
    ]
    
    for pitch, start, end in notes:
        note = pretty_midi.Note(velocity=100, pitch=pitch, start=start, end=end)
        guitar.notes.append(note)
    
    midi.instruments.append(guitar)
    
    # Sauvegarder le MIDI
    midi_path = test_dir / "test_guitar.mid"
    midi.write(str(midi_path))
    print(f"✅ MIDI créé: {midi_path}")
    
    # Générer un audio synthétique correspondant
    # On crée un signal audio simple avec les fréquences des notes
    sample_rate = 22050
    duration = 5.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.zeros(int(sample_rate * duration))
    
    for pitch, start, end in notes:
        freq = pretty_midi.note_number_to_hz(pitch)
        start_idx = int(start * sample_rate)
        end_idx = int(end * sample_rate)
        if end_idx <= len(audio):
            # Créer une onde sinusoïdale avec enveloppe ADSR
            note_duration = end - start
            note_samples = end_idx - start_idx
            note_t = np.linspace(0, note_duration, note_samples)
            
            # Enveloppe ADSR simple
            attack = 0.05
            decay = 0.1
            sustain_level = 0.7
            release = 0.2
            
            envelope = np.ones(note_samples)
            attack_samples = int(attack * sample_rate)
            decay_samples = int(decay * sample_rate)
            release_samples = int(release * sample_rate)
            
            if attack_samples > 0:
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
            if decay_samples > 0 and attack_samples + decay_samples < note_samples:
                envelope[attack_samples:attack_samples+decay_samples] = np.linspace(1, sustain_level, decay_samples)
            if release_samples > 0 and note_samples - release_samples > 0:
                envelope[-release_samples:] = np.linspace(sustain_level, 0, release_samples)
            
            # Signal sinusoïdal avec enveloppe
            note_signal = np.sin(2 * np.pi * freq * note_t) * envelope * 0.3
            audio[start_idx:end_idx] += note_signal[:min(len(note_signal), len(audio) - start_idx)]
    
    # Normaliser
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    # Sauvegarder en WAV (plus compatible que MP3)
    audio_path = test_dir / "test_guitar.wav"
    sf.write(str(audio_path), audio, sample_rate)
    print(f"✅ Audio créé: {audio_path}")
    
    print(f"\n✅ Fichiers de test créés avec succès!")
    print(f"   - MIDI: {midi_path}")
    print(f"   - Audio: {audio_path}")
    
except ImportError as e:
    print(f"[ERREUR] Bibliotheque manquante: {e}")
    print("Installation des dépendances nécessaires...")
    import subprocess
    subprocess.check_call(["pip", "install", "soundfile"])
    print("Réessayez après l'installation.")

