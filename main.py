import requests
from bs4 import BeautifulSoup

def get_trending_topics(country="united-states"):
    """
    Mengambil daftar trending topic dari trends24.in untuk negara tertentu.
    Versi ini telah diperbarui dengan selector HTML yang benar.
    """
    url = f"https://trends24.in/{country}/"
    headers = {
        # Menambahkan User-Agent agar terlihat seperti browser biasa
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # Menambahkan headers ke dalam request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Ini akan memberikan error jika request gagal (misal: 404, 500)
        
        # Mengatasi masalah encoding
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Selector yang Diperbarui ---
        # Mencari semua elemen 'li' di dalam 'ol' dengan kelas 'trend-list'
        trend_list = soup.select('ol.trend-list li')
        
        if not trend_list:
            # Jika selector di atas gagal, coba cari di dalam div.trend-card
            trend_list = soup.select('div.trend-card li')

        trends = []
        for trend_item in trend_list:
            topic_element = trend_item.find('a')
            if topic_element:
                topic = topic_element.get_text(strip=True)
                trends.append(topic)
        
        # Jika setelah semua usaha trends masih kosong, beri pesan
        if not trends:
            print("Tidak dapat menemukan elemen tren di halaman. Mungkin struktur situs telah berubah lagi.")
            return []

        return trends

    except requests.exceptions.RequestException as e:
        print(f"Error saat melakukan request ke situs: {e}")
        return []
    except Exception as e:
        print(f"Terjadi error yang tidak terduga: {e}")
        return []

def format_post(trends, limit=4):
    """
    Memformat daftar tren menjadi sebuah string untuk postingan,
    dengan batasan jumlah tren.
    """
    if not trends:
        return "Tidak ada tren yang ditemukan."

    top_trends = trends[:limit]

    post_content = []
    for trend in top_trends:
        if trend.startswith('#'):
            post_content.append(trend)
        else:
            # Membersihkan dan mengubah menjadi format hashtag
            cleaned_trend = ''.join(e for e in trend if e.isalnum() or e.isspace())
            hashtag = "#" + cleaned_trend.replace(' ', '')
            post_content.append(hashtag)
    
    return ' '.join(post_content)

# --- Contoh Penggunaan ---
if __name__ == "__main__":
    trending_topics = get_trending_topics("united-states")

    if trending_topics:
        post = format_post(trending_topics, limit=4)
        print("✅ Berhasil mendapatkan tren!")
        print("Hasil Postingan:")
        print(post)
    else:
        print("❌ Gagal mendapatkan trending topics setelah perbaikan.")
