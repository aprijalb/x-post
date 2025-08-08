import os
import random
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import tweepy
import urllib.parse

# --- FUNGSI UNTUK SCRAPING (DIPERBARUI) ---
def scrape_trends_from_getdaytrends():
    """Mengambil 10 tren teratas dari getdaytrends.com untuk United States."""
    # URL diubah ke sumber yang baru
    url = "https://getdaytrends.com/united-states/"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Selector diubah untuk menyesuaikan dengan struktur HTML getdaytrends.com
        # Website ini menggunakan tabel untuk menampilkan tren
        trend_list = soup.select('table.table-hover td a')
        
        # Mengambil 10 tren teratas
        trends = [trend.text.strip().replace('#', '') for trend in trend_list[:10]]
        
        if not trends:
            print("Peringatan: Tidak ada tren yang ditemukan. Mungkin struktur website berubah.")
            return None
            
        # Langsung memilih satu tren secara acak dari 10 teratas
        selected_trend = random.choice(trends)
        print(f"Ditemukan {len(trends)} tren, memilih satu secara acak: {selected_trend}")
        return selected_trend

    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses getdaytrends.com: {e}")
        return None

# --- FUNGSI UNTUK GENERASI KONTEN ---
def generate_post_with_gemini(trend):
    """Membuat konten post dengan Gemini API berdasarkan satu tren."""
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables!")
        
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = (
        f"You are a social media expert. Write a short, engaging post in English about this topic: '{trend}'. "
        f"The post MUST have a strong Call to Action to encourage clicks. "
        f"Do NOT add any links or hashtags in your response. Just provide the main text."
    )
    
    try:
        response = model.generate_content(prompt)
        print("Konten berhasil dibuat oleh Gemini.")
        return response.text.strip()
    except Exception as e:
        print(f"Error saat menghubungi Gemini API: {e}")
        return None

# --- FUNGSI UNTUK MENDAPATKAN LINK ---
def get_random_link(filename="links.txt"):
    """Membaca file dan memilih satu link secara acak."""
    try:
        with open(filename, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
        return random.choice(links) if links else None
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None

# --- FUNGSI UNTUK POSTING KE X.COM ---
def post_to_x(text_to_post, image_url=None):
    """Memposting teks dan gambar (opsional) ke X.com."""
    try:
        media_ids = []
        if image_url:
            auth = tweepy.OAuth1UserHandler(
                os.getenv('X_API_KEY'), os.getenv('X_API_SECRET'),
                os.getenv('X_ACCESS_TOKEN'), os.getenv('X_ACCESS_TOKEN_SECRET')
            )
            api = tweepy.API(auth)
            
            filename = 'temp_image.jpg'
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as image_file:
                    for chunk in response.iter_content(1024):
                        image_file.write(chunk)
                
                media = api.media_upload(filename=filename)
                media_ids.append(media.media_id_string)
                print("Gambar berhasil di-upload.")
            else:
                print(f"Gagal mengunduh gambar. Status code: {response.status_code}")

        client = tweepy.Client(
            bearer_token=os.getenv('X_BEARER_TOKEN'),
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET')
        )
        
        if media_ids:
            response = client.create_tweet(text=text_to_post, media_ids=media_ids)
        else:
            response = client.create_tweet(text=text_to_post)
            
        print(f"Berhasil memposting tweet ID: {response.data['id']}")
        
    except Exception as e:
        print(f"Error saat memposting ke X.com: {e}")

# --- FUNGSI UTAMA (DIPERBAIKI) ---
if __name__ == "__main__":
    print("Memulai proses auto-posting...")
    
    # Memanggil fungsi scrape yang baru
    selected_trend = scrape_trends_from_getdaytrends()
    
    if selected_trend:
        random_link = get_random_link()
        
        if random_link:
            gemini_text = generate_post_with_gemini(selected_trend)
            
            if gemini_text:
                print(f"Teks dari Gemini: {gemini_text}")

                image_url = f"https://tse1.mm.bing.net/th?q={urllib.parse.quote(selected_trend)}"
                print(f"URL Gambar: {image_url}")

                # Gabungkan teks dan link dengan spasi, tanpa enter dan tanpa hashtag
                final_post_text = f"{gemini_text} {random_link}"
                
                print("--- POSTINGAN FINAL ---")
                print(f"Teks: {final_post_text}")
                print("-----------------------")
                
                # Kirim teks gabungan dan URL gambar ke fungsi posting
                post_to_x(final_post_text, image_url)
    
    print("Proses selesai.")