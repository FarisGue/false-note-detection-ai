"""A simple Streamlit app to interact with the false note detection API."""

import streamlit as st
import requests
from typing import List

st.set_page_config(page_title="False Note Detector")
st.title("🎵 False Note Detection App")

st.markdown(
    "Upload a performance audio file and a reference MIDI to identify false notes.\n"
    "The analysis is performed by a backend FastAPI service running locally."
)

audio_file = st.file_uploader("Performance audio file", type=["wav", "mp3", "flac"])
ref_file = st.file_uploader("Reference MIDI file", type=["mid", "midi"])

if st.button("Analyze"):
    if not audio_file or not ref_file:
        st.warning("Please upload both an audio file and a reference MIDI file.")
    else:
        with st.spinner("Processing..."):
            files = {
                "audio": (audio_file.name, audio_file.getvalue(), audio_file.type),
                "reference": (ref_file.name, ref_file.getvalue(), ref_file.type),
            }
            try:
                response = requests.post("http://localhost:8000/upload/", files=files, timeout=120)
            except Exception as exc:
                st.error(f"Error contacting backend: {exc}")
                response = None
            if response and response.status_code == 200:
                result = response.json()
                st.success("Analysis complete!")
                st.write(f"Total frames analyzed: {result['total_frames']}")
                st.write(f"Correct frames: {result['correct_frames']}")
                st.write(f"Mean cents error estimate: {result['mean_cents']:.2f}")
                st.write(f"Indices of false notes: {result['error_indices']}")
            elif response is not None:
                st.error(f"Backend returned error: {response.status_code} {response.text}")