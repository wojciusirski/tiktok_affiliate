import streamlit as st
import requests
import os
from moviepy import VideoFileClip, CompositeVideoClip, vfx

# --- FUNKCJA POBIERANIA FILMU Z TIKTOKA ---
def download_tiktok(url):
    api_url = f"https://www.tikwm.com/api/?url={url}"
    try:
        res = requests.get(api_url).json()
        if res.get("code") == 0:
            video_url = res["data"]["play"]
            video_data = requests.get(video_url).content
            with open("input_video.mp4", "wb") as f:
                f.write(video_data)
            return "input_video.mp4"
    except Exception as e:
        st.error(f"Błąd pobierania: {e}")
    return None

# --- FUNKCJA USUWANIA TŁA (CHROMA KEY) ---
def apply_chroma_key(clip, color=[0, 0, 0], thr=60, s=5):
    """
    color: [R, G, B] koloru do usunięcia (domyślnie czarny [0,0,0])
    thr: tolerancja (im wyższa, tym więcej odcieni usunie)
    s: wygładzenie krawędzi
    """
    return clip.with_effects([vfx.MaskColor(color=color, thr=thr, s=s)])

# --- FUNKCJA MONTAŻU ---
def process_video(tiktok_path, start_time):
    # 1. Główny film
    clip = VideoFileClip(tiktok_path).with_effects([vfx.Resize(height=1920)])
    
    # 2. Twój awatar (idle)
    idle = VideoFileClip("assets/idle.mp4", audio=False).with_effects([vfx.Resize(width=450)])
    # USUNIĘCIE TŁA: Jeśli masz czarne tło, zostaw [0,0,0]. Jeśli zielone, daj [0,255,0]
    idle = apply_chroma_key(idle, color=[0, 0, 0], thr=60) 
    
    idle_loop = idle.with_effects([vfx.Loop(duration=clip.duration)]).with_position(("right", "bottom"))
    
    # 3. Twoja reakcja
    reakcja = VideoFileClip("assets/reakcja.mp4").with_effects([vfx.Resize(width=450)])
    # USUNIĘCIE TŁA dla reakcji
    reakcja = apply_chroma_key(reakcja, color=[0, 0, 0], thr=60)
    reakcja = reakcja.with_start(start_time).with_position(("right", "bottom"))
    
    # 4. Składanie (CompositeVideoClip obsłuży przezroczystość z maski)
    final = CompositeVideoClip([clip, idle_loop, reakcja])
    
    output_path = "final_output.mp4"
    final.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        temp_audiofile='temp-audio.m4a', 
        remove_temp=True
    )
    
    clip.close()
    idle.close()
    reakcja.close()
    
    return output_path

# --- INTERFEJS ---
st.set_page_config(page_title="AI Affiliate Creator", layout="centered")
st.title("🤖 AI Affiliate - Bez Tła")

link = st.text_input("Link do TikToka:")
start_sec = st.slider("Sekunda startu reakcji:", 0, 15, 5)

# Dodatkowe ustawienie w UI do poprawki tła na żywo
st.sidebar.header("Ustawienia wycinania tła")
color_to_remove = st.sidebar.color_picker("Wybierz kolor tła do usunięcia", "#000000")
threshold = st.sidebar.slider("Tolerancja wycinania", 10, 150, 60)

if st.button("🚀 GENERUJ FILM"):
    if link:
        with st.spinner("Wycinam tło i montuję..."):
            # Konwersja koloru HEX na RGB
            rgb = [int(color_to_remove.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)]
            
            tiktok_file = download_tiktok(link)
            if tiktok_file:
                try:
                    # Tutaj możesz przekazać rgb i threshold do funkcji process_video jeśli chcesz
                    result_video = process_video(tiktok_file, start_sec)
                    st.video(result_video)
                    st.download_button("📥 Pobierz", open(result_video, "rb"), file_name="tiktok.mp4")
                except Exception as e:
                    st.error(f"Błąd: {e}")
