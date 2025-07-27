import os
import random
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import tweepy
import urllib.parse
import time

# Import Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# --- FUNGSI UNTUK SCRAPING (DIROMBAK TOTAL MENGGUNAKAN SELENIUM) ---
def scrape_trends_with_selenium():
    """
    Mengambil tren dari trends24.in menggunakan Selenium untuk menangani JavaScript.
    Fungsi ini dirancang untuk berjalan di lingkungan server seperti GitHub Actions.
    """
    print("Memulai proses scraping dengan Selenium...")
    
    # Konfigurasi opsi untuk Chrome agar berjalan di server (headless)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless") # Berjalan tanpa membuka jendela browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = None
    try:
        # Menginstal dan mengelola driver Chrome secara otomatis
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = "https://trends24.in/united-states/"
        print(f"Membuka URL: {url}")
        driver.get(url)
        
        # MENUNGGU HINGGA ELEMEN SPESIFIK MUNCUL (KUNCI UTAMA)
        # Kita tunggu hingga elemen 'ol' dengan class 'trend-list' dimuat, maksimal 20 detik.
        print("Menunggu konten dinamis (JavaScript) selesai dimuat...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ol.trend-list li a")))
        print("Konten berhasil dimuat.")

        # Setelah konten dimuat, ambil source HTML halamannya
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Selector tetap sama, tapi sekarang diaplikasikan ke HTML yang sudah dirender
        trend_elements = soup.select('ol.trend-list li a')
        
        trends = [trend.get_text(strip=True).replace('#', '') for trend in trend_elements[:4]]
        
        if not trends or len(trends) < 4:
            print(f"❌ Peringatan: Hanya ditemukan {len(trends)} tren. Mungkin ada sedikit perubahan pada situs.")
            if not trends: return None # Jika benar-benar kosong, gagal.
        
        print(f"✅ Tren berhasil diambil: {trends}")
        return trends

    except TimeoutException:
        print("❌ Error Kritis: Waktu tunggu habis. Elemen tren tidak ditemukan di halaman.")
        print("Ini berarti struktur HTML situs telah berubah. Selector CSS perlu diperbarui.")
        return None
    except Exception as e:
        print(f"❌ Terjadi error tak terduga saat proses Selenium: {e}")
        return None
    finally:
        if driver:
            print("Menutup driver Selenium.")
            driver.quit()

# --- FUNGSI GENERASI KONTEN (TIDAK BERUBAH) ---
def generate_post_with_gemini(trend, link):
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

# --- FUNGSI GET LINK (TIDAK BERUBAH) ---
def get_random_link(filename="links.txt"):
    try:
        with open(filename, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
        return random.choice(links) if links else None
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None

# --- FUNGSI POST KE X (TIDAK BERUBAH) ---
def post_to_x(text_to_post, image_url=None):
    try:
        client = tweepy.Client(
            bearer_token=os.getenv('X_BEARER_TOKEN'),
            consumer_key=os.getenv('X_API_KEY'),
            consumer_secret=os.getenv('X_API_SECRET'),
            access_token=os.getenv('X_ACCESS_TOKEN'),
            access_token_secret=os.getenv('X_ACCESS_TOKEN_SECRET')
        )
        media_ids = []
        if image_url:
            auth_v1 = tweepy.OAuth1UserHandler(
                os.getenv('X_API_KEY'), os.getenv('X_API_SECRET'),
                os.getenv('X_ACCESS_TOKEN'), os.getenv('X_ACCESS_TOKEN_SECRET')
            )
            api_v1 = tweepy.API(auth_v1)
            filename = 'temp_image.jpg'
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as image_file:
                    for chunk in response.iter_content(1024):
                        image_file.write(chunk)
                media = api_v1.media_upload(filename=filename)
                media_ids.append(media.media_id_string)
                print("Gambar berhasil di-upload.")
            else:
                print(f"Gagal mengunduh gambar. Status code: {response.status_code}")
        response = client.create_tweet(text=text_to_post, media_ids=media_ids if media_ids else None)
        print(f"Berhasil memposting tweet ID: {response.data['id']}")
    except Exception as e:
        print(f"Error saat memposting ke X.com: {e}")

# --- FUNGSI UTAMA ---
if __name__ == "__main__":
    print("Memulai proses auto-posting...")
    top_trends = scrape_trends_with_selenium()
    if top_trends:
        selected_trend = random.choice(top_trends)
        print(f"Tren yang dipilih untuk konten: {selected_trend}")
        random_link = get_random_link()
        if random_link:
            gemini_text = generate_post_with_gemini(selected_trend, random_link)
            if gemini_text:
                print(f"Teks dari Gemini: {gemini_text}")
                hashtags_string = " ".join([f"#{trend.replace(' ', '')}" for trend in top_trends])
                print(f"Hashtag yang dibuat (dari 4 tren): {hashtags_string}")
                image_url = f"https://tse1.mm.bing.net/th?q={urllib.parse.quote(selected_trend)}"
                print(f"URL Gambar: {image_url}")
                final_post = f"{gemini_text}\n\n{hashtags_string}"
                print("--- POSTINGAN FINAL ---")
                print(final_post)
                print("-----------------------")
                post_to_x(final_post, image_url)
    else:
        print("Proses auto-posting berhenti karena tidak ada tren yang berhasil didapatkan.")
    print("Proses selesai.")
