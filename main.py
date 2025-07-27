import os
import random
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import tweepy
import urllib.parse

# --- FUNGSI UNTUK SCRAPING (TELAH DIPERBAIKI TOTAL) ---
def scrape_trends_from_trends24():
    """
    Mengambil tren dari trends24.in untuk United States.
    Fungsi ini telah diperbarui dengan selector yang benar dan penanganan error yang lebih baik.
    """
    url = "https://trends24.in/united-states/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print("Mencoba mengambil tren dari trends24.in...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8' # Memastikan encoding benar untuk karakter spesial
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ---SELECTOR YANG BENAR---
        # Mencari semua elemen 'li' di dalam 'ol' dengan kelas 'trend-list'
        trend_elements = soup.select('ol.trend-list li a')
        
        # Jika selector utama gagal, coba selector cadangan
        if not trend_elements:
            print("Selector utama tidak menemukan apa pun. Mencoba selector cadangan...")
            trend_elements = soup.select('div.trend-card li a')

        # Memproses teks dari elemen yang ditemukan
        trends = [trend.get_text(strip=True) for trend in trend_elements]
        
        if not trends:
            print("❌ Error: Tidak ada tren yang bisa diambil. Struktur website kemungkinan besar telah berubah total.")
            return None
        
        # Mengambil 4 tren teratas dan memastikan tidak ada duplikat atau entri kosong
        final_trends = []
        for trend in trends:
            if trend and trend not in final_trends:
                # Menghapus karakter '#' jika ada agar konsisten
                final_trends.append(trend.replace('#', ''))
            if len(final_trends) == 4:
                break
        
        print(f"✅ Tren berhasil ditemukan: {final_trends}")
        return final_trends

    except requests.exceptions.RequestException as e:
        print(f"❌ Error kritis saat mengakses trends24.in: {e}")
        return None
    except Exception as e:
        print(f"❌ Terjadi error tak terduga saat scraping: {e}")
        return None

# --- FUNGSI UNTUK GENERASI KONTEN (TETAP SAMA) ---
def generate_post_with_gemini(trend, link):
    """Membuat konten post dengan Gemini API berdasarkan satu tren, menyertakan CTA dan link."""
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables!")
        
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = (
        f"You are a social media expert creating a post for X.com. "
        f"Write a short, engaging post in English about this topic: '{trend}'. The post MUST include a strong Call to Action {link}"
        f"Do NOT add any hashtags in your response. Just provide the main text with the CTA and the link."
    )
    
    try:
        response = model.generate_content(prompt)
        print("Konten berhasil dibuat oleh Gemini.")
        return response.text.strip()
    except Exception as e:
        print(f"Error saat menghubungi Gemini API: {e}")
        return None

# --- FUNGSI UNTUK MENDAPATKAN LINK (TETAP SAMA) ---
def get_random_link(filename="links.txt"):
    """Membaca file dan memilih satu link secara acak."""
    try:
        with open(filename, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
        return random.choice(links) if links else None
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None

# --- FUNGSI UNTUK POSTING KE X.COM (TETAP SAMA) ---
def post_to_x(text_to_post, image_url=None):
    """Memposting teks dan gambar (opsional) ke X.com."""
    try:
        media_ids = []
        if image_url:
            # Untuk upload media, kita perlu menggunakan API v1.1 dari Tweepy
            auth = tweepy.OAuth1UserHandler(
                os.getenv('X_API_KEY'), os.getenv('X_API_SECRET'),
                os.getenv('X_ACCESS_TOKEN'), os.getenv('X_ACCESS_TOKEN_SECRET')
            )
            api = tweepy.API(auth)
            
            # Download gambar dari URL
            filename = 'temp_image.jpg'
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as image_file:
                    for chunk in response.iter_content(1024):
                        image_file.write(chunk)
                
                # Upload gambar ke Twitter untuk mendapatkan media_id
                media = api.media_upload(filename=filename)
                media_ids.append(media.media_id_string)
                print("Gambar berhasil di-upload.")
            else:
                print(f"Gagal mengunduh gambar. Status code: {response.status_code}")

        # Gunakan Client API v2 untuk memposting tweet
        client = tweepy.Client(
            bearer_token=os.getenv('X_BEARER_TOKEN'),
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET')
        )
        
        # Buat tweet dengan atau tanpa media
        if media_ids:
            response = client.create_tweet(text=text_to_post, media_ids=media_ids)
        else:
            response = client.create_tweet(text=text_to_post)
            
        print(f"Berhasil memposting tweet ID: {response.data['id']}")
        
    except Exception as e:
        print(f"Error saat memposting ke X.com: {e}")

# --- FUNGSI UTAMA (TETAP SAMA) ---
if __name__ == "__main__":
    print("Memulai proses auto-posting...")
    
    top_trends = scrape_trends_from_trends24()
    
    if top_trends:
        # Memilih satu tren secara acak untuk dijadikan konten
        selected_trend = random.choice(top_trends)
        print(f"Tren yang dipilih untuk konten: {selected_trend}")
        
        random_link = get_random_link()
        
        if random_link:
            # Membuat konten (teks) berdasarkan tren yang dipilih
            gemini_text = generate_post_with_gemini(selected_trend, random_link)
            
            if gemini_text:
                print(f"Teks dari Gemini: {gemini_text}")

                # Membuat string hashtag dari SEMUA tren yang ditemukan
                # untuk jangkauan yang lebih luas
                hashtags_string = " ".join([f"#{trend.replace(' ', '')}" for trend in top_trends])
                print(f"Hashtag yang dibuat (dari 4 tren): {hashtags_string}")
                
                # Membuat URL gambar dari tren yang dipilih untuk konten
                image_url = f"https://tse1.mm.bing.net/th?q={urllib.parse.quote(selected_trend)}"
                print(f"URL Gambar: {image_url}")

                # Menggabungkan teks AI dan semua hashtag
                final_post = f"{gemini_text}\n\n{hashtags_string}"
                
                print("--- POSTINGAN FINAL ---")
                print(final_post)
                print("-----------------------")
                
                # Posting ke X.com dengan gambar
                post_to_x(final_post, image_url)
    else:
        print("Proses auto-posting berhenti karena tidak ada tren yang berhasil didapatkan.")

    print("Proses selesai.")
