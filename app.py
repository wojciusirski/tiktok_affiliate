import streamlit as st
import requests
import os
from moviepy import VideoFileClip, CompositeVideoClip, vfx

# --- FUNKCJA POBIERANIA FILMU Z TIKTOKA ---
def download_tiktok(url):
    # Korzystamy z publicznego API tikwm do pobrania wideo bez znaku wodnego
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
        st.error(f"Błąd pobierania wideo: {e}")
    return None

# --- FUNKCJA MONTAŻU Z USUWANIEM CZARNEGO TŁA ---
def process_video(tiktok_path, start_time):
    # 1. Wczytujemy tło (film z produktem) i ustawiamy pionowy format HD
    clip = VideoFileClip(tiktok_path).with_effects([vfx.Resize(height=1920)])
    
    # 2. Wczytujemy Twój awatar 'idle' (pętla)
    idle_path = "assets/idle.mp4"
    if not os.path.exists(idle_path):
        raise FileNotFoundError(f"Nie znaleziono pliku: {idle_path}")
    
    idle = VideoFileClip(idle_path, audio=False).with_effects([vfx.Resize(width=450)])
    
    # KLUCZOWY MOMENT: Zamieniamy czarny kolor [0,0,0] na przezroczystość
    # thr=60 to tolerancja, s=5 to wygładzenie krawędzi postaci
    idle = idle.with_effects([vfx.MaskColor(color=[0, 0, 0], thr=60, s=5)])
    
    # Zapętlamy awatar na całą długość filmu i ustawiamy w prawym dolnym rogu
    idle_loop = idle.with_effects([vfx.Loop(duration=clip.duration)]).with_position(("right", "bottom"))
    
    # 3. Wczytujemy Twoją 'reakcję' (moment mówiony)
    reakcja_path = "assets/reakcja.mp4"
    if not os.path.exists(reakcja_path):
        raise FileNotFoundError(f"Nie znaleziono pliku: {reakcja_path}")
    
    reakcja = VideoFileClip(reakcja_path).with_effects([vfx.Resize(width=450)])
    # Tutaj również usuwamy czarny prostokąt
    reakcja = reakcja.with_effects([vfx.MaskColor(color=[0, 0, 0], thr=60, s=5)])
    
    # Ustawiamy moment startu reakcji wybrany suwakiem
    reakcja = reakcja.with_start(start_time).with_position(("right", "bottom"))
    
    # 4. Składamy warstwy: Produkt -> Zapętlony awatar -> Aktywna reakcja
    final = CompositeVideoClip([clip, idle_loop, reakcja])
    
    output_path = "final_output.mp4"
    # Renderowanie - fps=24 jest optymalne dla szybkości i jakości w chmurze
    final.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        temp_audiofile='temp-audio.m4a', 
        remove_temp=True
    )
    
    # Zwalniamy pamięć RAM serwera
    clip.close()
    idle.close()
    reakcja.close()
    
    return output_path

# --- INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="AI Affiliate Creator", layout="centered")
st.title("🤖 AI Affiliate Content Generator")
st.write("Wklej link, a ja wyetnę czarne tło i nałożę Twojego awatara na film.")

link = st.text_input("Link do TikToka:")
start_sec = st.slider("W której sekundzie ma wystąpić Twoja reakcja?", 0, 15, 5)

if st.button("🚀 GENERUJ FILM"):
    if link:
        with st.spinner("Przetwarzam... Usuwam czarne tło i montuję film."):
            tiktok_file = download_tiktok(link)
            if tiktok_file:
                try:
                    result_video = process_video(tiktok_file, start_sec)
                    st.video(result_video)
                    with open(result_video, "rb") as file:
                        st.download_button("📥 Pobierz gotowy film", file, file_name="tiktok_final.mp4")
                except Exception as e:
                    st.error(f"Błąd podczas montażu: {e}")
            else:
                st.error("Nie udało się pobrać filmu. Sprawdź link.")
    else:
        st.warning("Proszę wkleić link do TikToka.")
