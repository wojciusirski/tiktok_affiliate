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

# --- FUNKCJA MONTAŻU (ZOPTYMALIZOWANA POD MOVIEPY 2.2.1) ---
def process_video(tiktok_path, start_time):
    # 1. Wczytujemy film z produktem
    # Używamy decode_file=True dla stabilności w nowych wersjach
    clip = VideoFileClip(tiktok_path).with_effects([vfx.Resize(height=1920)])
    
    # 2. Wczytujemy plik 'idle' (potakiwanie)
    # Wyłączamy audio dla idle, żeby nie robiło konfliktów
    idle_path = "assets/idle.mp4"
    if not os.path.exists(idle_path):
        raise FileNotFoundError(f"Nie znaleziono pliku {idle_path}")
        
    idle = VideoFileClip(idle_path, audio=False).with_effects([vfx.Resize(width=450)])
    
    # Zapętlanie (Nowa składnia vfx.Loop)
    idle_loop = idle.with_effects([vfx.Loop(duration=clip.duration)]).with_position(("right", "bottom"))
    
    # 3. Wczytujemy 'reakcja.mp4'
    reakcja_path = "assets/reakcja.mp4"
    if not os.path.exists(reakcja_path):
        raise FileNotFoundError(f"Nie znaleziono pliku {reakcja_path}")

    reakcja = VideoFileClip(reakcja_path).with_effects([vfx.Resize(width=450)])
    reakcja = reakcja.with_start(start_time).with_position(("right", "bottom"))
    
    # 4. Składanie całości
    final = CompositeVideoClip([clip, idle_loop, reakcja])
    
    output_path = "final_output.mp4"
    # Ustawienia zapisu optymalne dla Streamlit Cloud
    final.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        temp_audiofile='temp-audio.m4a', 
        remove_temp=True
    )
    
    # Zamknięcie klipów, żeby zwolnić pamięć RAM serwera
    clip.close()
    idle.close()
    reakcja.close()
    
    return output_path

# --- INTERFEJS STRONY ---
st.set_page_config(page_title="AI Affiliate Creator", layout="centered")
st.title("🤖 AI Affiliate Content Generator")
st.write("Wklej link do TikToka, a ja zmontuję film z Twoim awatarem.")

link = st.text_input("Link do filmu z produktem:")
start_sec = st.slider("W której sekundzie zaczynasz mówić?", 0, 15, 5)

if st.button("🚀 GENERUJ FILM"):
    if link:
        with st.spinner("Pracuję nad filmem... Może to zająć do 3 minut."):
            tiktok_file = download_tiktok(link)
            if tiktok_file:
                try:
                    result_video = process_video(tiktok_file, start_sec)
                    st.video(result_video)
                    with open(result_video, "rb") as file:
                        st.download_button("📥 Pobierz gotowy film", file, file_name="gotowy_tiktok.mp4")
                except Exception as e:
                    st.error(f"Wystąpił błąd: {e}")
            else:
                st.error("Nie udało się pobrać filmu z TikToka.")
    else:
        st.warning("Najpierw wklej link!")