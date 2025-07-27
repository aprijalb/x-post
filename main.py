import requests
from bs4 import BeautifulSoup

def get_trending_topics(country="united-states"):
    """
    Mengambil daftar trending topic dari trends24.in untuk negara tertentu.
    """
    url = f"https://trends24.in/{country}/"
    try:
        response = requests.get(url)
        # Mengatasi masalah encoding dengan menyetelnya secara eksplisit ke UTF-8
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Mencari semua elemen 'li' di dalam div dengan kelas 'trend-card'
        trend_list = soup.select('div.trend-card ol li')

        trends = []
        for trend_item in trend_list:
            # Mengambil teks dari tag 'a' di dalam 'li'
            topic = trend_item.find('a').get_text(strip=True)
            trends.append(topic)

        return trends

    except requests.exceptions.RequestException as e:
        print(f"Error saat mengambil data: {e}")
        return []

def format_post(trends, limit=4):
    """
    Memformat daftar tren menjadi sebuah string untuk postingan,
    dengan batasan jumlah tren.
    """
    if not trends:
        return "Tidak ada tren yang ditemukan."

    # Ambil 4 tren teratas
    top_trends = trends[:limit]

    post_content = []
    for trend in top_trends:
        # Jika sudah berupa hashtag, biarkan. Jika tidak, tambahkan '#'
        if trend.startswith('#'):
            post_content.append(trend)
        else:
            # Mengganti spasi dengan underscore untuk hashtag yang lebih baik
            # dan membersihkan karakter yang tidak diinginkan
            cleaned_trend = ''.join(e for e in trend if e.isalnum() or e == ' ')
            hashtag = "#" + cleaned_trend.replace(' ', '')
            post_content.append(hashtag)
    
    # Gabungkan semua hashtag menjadi satu string, dipisahkan oleh spasi
    return ' '.join(post_content)

# --- Contoh Penggunaan ---
if __name__ == "__main__":
    # Ganti "united-states" dengan negara lain jika diperlukan
    trending_topics = get_trending_topics("united-states")

    if trending_topics:
        post = format_post(trending_topics, limit=4)
        print("Hasil Postingan:")
        print(post)
    else:
        print("Gagal mendapatkan trending topics.")