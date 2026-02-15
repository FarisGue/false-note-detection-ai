"""A simple Streamlit app to interact with the false note detection API."""

import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List
import json

st.set_page_config(page_title="False Note Detector", layout="wide")
st.title("🎵 False Note Detection App")

st.markdown(
    "Upload a performance audio file and a reference MIDI to identify false notes.\n"
    "The analysis is performed by a backend FastAPI service running locally."
)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input("API URL", value="http://localhost:8000/upload/")
    timeout = st.number_input("Timeout (seconds)", min_value=30, max_value=300, value=120)

    # Option to request practice recommendations. When enabled the backend
    # sends analysis metrics to a language model and returns tailored advice.
    enable_recommendations = st.checkbox(
        "Generate practice recommendations",
        value=False,
        help="If checked, the API will attempt to generate practice advice via a language model."
    )

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Upload Files")
    audio_file = st.file_uploader(
        "Performance audio file", 
        type=["wav", "mp3", "flac", "ogg", "m4a"],
        help="Upload your audio performance recording"
    )
    
with col2:
    st.subheader("📁 Upload Files")
    ref_file = st.file_uploader(
        "Reference MIDI file", 
        type=["mid", "midi"],
        help="Upload the reference MIDI file"
    )

if st.button("🔍 Analyze", type="primary", use_container_width=True):
    if not audio_file or not ref_file:
        st.warning("⚠️ Please upload both an audio file and a reference MIDI file.")
    else:
        with st.spinner("🔄 Processing audio and MIDI files... This may take a moment."):
            files = {
                "audio": (audio_file.name, audio_file.getvalue(), audio_file.type),
                "reference": (ref_file.name, ref_file.getvalue(), ref_file.type),
            }
            # Include query parameters for recommendations if requested
            params = {}
            if enable_recommendations:
                params["generate_recommendations_flag"] = "true"
            try:
                response = requests.post(api_url, files=files, timeout=timeout, params=params)
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the API. Make sure the FastAPI server is running on port 8000.")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The analysis is taking too long. Try with shorter files.")
                st.stop()
            except Exception as exc:
                st.error(f"❌ Error contacting backend: {exc}")
                st.stop()
            
            if response and response.status_code == 200:
                result = response.json()
                
                # Store result in session state for download
                st.session_state['last_result'] = result
                st.session_state['audio_filename'] = audio_file.name
                st.session_state['midi_filename'] = ref_file.name
                
                st.success("✅ Analysis complete!")
                
                # Extract metrics from result (using new model fields)
                total_frames = result.get('total_frames', 0)
                correct_frames = result.get('correct_frames', 0)
                incorrect_frames = result.get('incorrect_frames', result.get('total_frames', 0) - result.get('correct_frames', 0))
                accuracy = result.get('accuracy_percent', (correct_frames / total_frames * 100) if total_frames > 0 else 0)
                mean_cents = result.get('mean_cents', 0.0)
                max_cents = result.get('max_cents', 0.0)
                duration = result.get('duration_seconds', total_frames / 100.0)
                threshold_cents = result.get('threshold_cents', 40.0)
                error_indices = result.get('error_indices', [])
                
                # Display metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Accuracy", f"{accuracy:.2f}%")
                
                with col2:
                    st.metric("Correct Frames", f"{correct_frames:,}", delta=f"{total_frames:,} total")
                
                with col3:
                    st.metric("Errors Detected", f"{len(error_indices):,}")
                
                with col4:
                    st.metric("Mean Cents Error", f"{mean_cents:.2f}¢", delta=f"Max: {max_cents:.2f}¢")
                
                # Visualizations
                st.subheader("📊 Visualizations")
                
                # Visualisation des notes avec erreurs en rouge
                pitch_data = result.get('pitch_data')
                if pitch_data:
                    st.markdown("### 🎵 Visualisation des Notes")
                    
                    # Convertir les fréquences en MIDI notes
                    def freq_to_midi(freq):
                        if freq <= 0:
                            return -1
                        return int(round(69 + 12 * np.log2(freq / 440.0)))
                    
                    def midi_to_note_name(midi):
                        if midi < 0:
                            return ""
                        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                        note = note_names[midi % 12]
                        octave = (midi // 12) - 1
                        return f"{note}{octave}"
                    
                    times = np.array(pitch_data.get('times', []))
                    audio_freqs = np.array(pitch_data.get('audio_frequencies', []))
                    ref_freqs = np.array(pitch_data.get('reference_frequencies', []))
                    is_error = np.array(pitch_data.get('is_error', []))
                    
                    if len(times) > 0:
                        # Convertir en MIDI notes
                        ref_midi = np.array([freq_to_midi(f) for f in ref_freqs])
                        audio_midi = np.array([freq_to_midi(f) for f in audio_freqs])
                        
                    # -----------------------------------------------------------------------
                    # Improved visualisation: Musical staff view
                    #
                    # The previous version of this app used horizontal bar charts to
                    # indicate the duration of each note (a piano‑roll style view). While
                    # functional, that layout does not resemble traditional sheet
                    # notation and can feel disconnected from how musicians perceive
                    # melodies. In this revision we instead plot individual note
                    # markers on a simplified "staff". Horizontal grid lines are drawn
                    # at each MIDI note, with thicker lines every octave to aid
                    # orientation. Notes from the reference (MIDI) are shown as light
                    # green dots, correctly performed notes are light blue and
                    # mis‑performed notes (false notes) are highlighted in red. Each
                    # marker is drawn with a border to improve contrast.

                    # Determine the MIDI range to display
                    valid_ref = ref_midi >= 0
                    valid_audio = audio_midi >= 0
                    all_midi_notes = np.concatenate([
                        ref_midi[valid_ref],
                        audio_midi[valid_audio]
                    ])
                    if len(all_midi_notes) > 0:
                        min_midi_note = int(np.max([40, all_midi_notes.min() - 2]))
                        max_midi_note = int(np.min([90, all_midi_notes.max() + 2]))
                    else:
                        min_midi_note, max_midi_note = 40, 80

                    fig_notes, ax_staff = plt.subplots(1, 1, figsize=(14, 6))

                    # Draw horizontal grid lines for each MIDI note in range
                    for midi_val in range(min_midi_note, max_midi_note + 1):
                        linewidth = 0.3
                        color = 'lightgrey'
                        # Emphasise octave (C notes) with thicker line
                        if midi_val % 12 == 0:
                            linewidth = 0.6
                            color = 'grey'
                        ax_staff.axhline(y=midi_val, color=color, linewidth=linewidth, zorder=0)

                    # Plot reference MIDI notes (green)
                    if np.any(valid_ref):
                        ref_times = times[valid_ref]
                        ref_notes = ref_midi[valid_ref]
                        ax_staff.scatter(ref_times, ref_notes, c='lightgreen', edgecolors='green', s=30,
                                         label='Référence MIDI', zorder=3)

                    # Plot audio notes: separate correct and erroneous frames
                    if np.any(valid_audio):
                        audio_times = times[valid_audio]
                        audio_notes = audio_midi[valid_audio]
                        audio_errors = is_error[valid_audio]
                        # Correct notes
                        correct_mask = ~audio_errors
                        if np.any(correct_mask):
                            ax_staff.scatter(
                                audio_times[correct_mask], audio_notes[correct_mask],
                                c='lightblue', edgecolors='blue', s=30, label='Note correcte', zorder=3
                            )
                        # Erroneous notes
                        error_mask = audio_errors
                        if np.any(error_mask):
                            ax_staff.scatter(
                                audio_times[error_mask], audio_notes[error_mask],
                                c='red', edgecolors='darkred', s=40, label='❌ Fausse note', zorder=4
                            )

                    # Configure axes
                    ax_staff.set_xlabel('Temps (secondes)', fontsize=11, fontweight='bold')
                    ax_staff.set_ylabel('Note MIDI', fontsize=11, fontweight='bold')
                    ax_staff.set_title('🎼 Visualisation des notes sur une portée simplifiée', fontsize=13, fontweight='bold', pad=10)
                    ax_staff.set_ylim(min_midi_note - 1, max_midi_note + 1)
                    ax_staff.set_xlim(0, duration)
                    ax_staff.grid(False)
                    # Build legend
                    ax_staff.legend(loc='upper right', fontsize=10)
                    # Improve tick labels: show note names instead of raw MIDI numbers every 2 semitones
                    y_ticks = []
                    y_tick_labels = []
                    for midi_val in range(min_midi_note, max_midi_note + 1):
                        # Only label every other semitone to avoid clutter
                        if (midi_val - min_midi_note) % 2 == 0:
                            y_ticks.append(midi_val)
                            y_tick_labels.append(midi_to_note_name(midi_val))
                    ax_staff.set_yticks(y_ticks)
                    ax_staff.set_yticklabels(y_tick_labels, fontsize=9)

                    plt.tight_layout()
                    st.pyplot(fig_notes)
                    plt.close()
                    
                    st.info("💡 **Légende:** Les points verts représentent la référence MIDI, les bleus les notes correctement jouées et les rouges les fausses notes.")
                
                # Create timeline visualization (ancienne visualisation)
                st.markdown("### 📈 Timeline des Erreurs")
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Create timeline array
                timeline = np.zeros(total_frames)
                timeline[error_indices] = 1
                
                # Plot error timeline
                time_axis = np.arange(total_frames) / 100.0  # Convert to seconds (assuming 100 fps)
                ax.plot(time_axis, timeline, 'r-', linewidth=2, label='Errors', alpha=0.7)
                ax.fill_between(time_axis, 0, timeline, alpha=0.3, color='red')
                ax.set_xlabel('Time (seconds)')
                ax.set_ylabel('Error (1=Error, 0=Correct)')
                ax.set_title('Error Timeline - False Notes Detection')
                ax.set_ylim(-0.1, 1.1)
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                st.pyplot(fig)
                plt.close()
                
                # Error distribution
                if len(error_indices) > 0:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Error rate over time (windowed)
                        window_size = max(100, total_frames // 20)  # Adaptive window size
                        error_rate = []
                        time_points = []
                        
                        for i in range(0, total_frames, window_size):
                            window_end = min(i + window_size, total_frames)
                            window_errors = sum(1 for idx in error_indices if i <= idx < window_end)
                            error_rate.append(window_errors / (window_end - i) * 100)
                            time_points.append((i + window_end) / 2 / 100.0)
                        
                        fig2, ax2 = plt.subplots(figsize=(10, 4))
                        ax2.plot(time_points, error_rate, 'b-', marker='o', markersize=4)
                        ax2.fill_between(time_points, 0, error_rate, alpha=0.3, color='blue')
                        ax2.set_xlabel('Time (seconds)')
                        ax2.set_ylabel('Error Rate (%)')
                        ax2.set_title('Error Rate Over Time (Windowed)')
                        ax2.grid(True, alpha=0.3)
                        st.pyplot(fig2)
                        plt.close()
                    
                    with col2:
                        # Summary statistics
                        st.subheader("📈 Summary Statistics")
                        stats_data = {
                            "Metric": [
                                "Total Duration",
                                "Total Frames",
                                "Correct Frames",
                                "Errors",
                                "Accuracy",
                                "Mean Cents Error",
                                "Max Cents Error",
                                "Threshold Used",
                                "Error Rate"
                            ],
                            "Value": [
                                f"{duration:.2f} s",
                                f"{total_frames:,}",
                                f"{correct_frames:,}",
                                f"{len(error_indices):,}",
                                f"{accuracy:.2f}%",
                                f"{mean_cents:.2f}¢",
                                f"{max_cents:.2f}¢",
                                f"{threshold_cents:.1f}¢",
                                f"{len(error_indices) / total_frames * 100:.2f}%"
                            ]
                        }
                        stats_df = pd.DataFrame(stats_data)
                        st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                # Error details
                if len(error_indices) > 0:
                    st.subheader("🔍 Error Details")
                    
                    # Convert error indices to time
                    error_times = [idx / 100.0 for idx in error_indices[:100]]  # Show first 100
                    error_df = pd.DataFrame({
                        "Frame Index": error_indices[:100],
                        "Time (seconds)": error_times
                    })
                    
                    st.dataframe(error_df, use_container_width=True, hide_index=True)
                    
                    if len(error_indices) > 100:
                        st.info(f"Showing first 100 errors out of {len(error_indices)} total errors.")
                
                # Download results
                st.subheader("💾 Download Results")
                result_json = json.dumps(result, indent=2)
                st.download_button(
                    label="📥 Download Results as JSON",
                    data=result_json,
                    file_name=f"analysis_result_{audio_file.name}_{ref_file.name}.json",
                    mime="application/json"
                )

                # Display practice recommendations if provided
                rec_text = result.get("recommendations")
                if rec_text:
                    st.markdown("### 🎯 Practice Recommendations")
                    st.write(rec_text)
                elif enable_recommendations:
                    # User requested recommendations but none were generated
                    st.warning("⚠️ Recommendations were requested but could not be generated. Check server logs for details.")
                
            elif response is not None:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                st.error(f"❌ Backend returned error ({response.status_code}): {error_detail}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "False Note Detection AI - Built with FastAPI, librosa, and Streamlit"
    "</div>",
    unsafe_allow_html=True
)