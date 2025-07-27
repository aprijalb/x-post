def scrape_trends_from_trends24():
    """Mengambil 4 tren teratas dari trends24.in untuk United States."""
    url = "https://trends24.in/united-states/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8' # Pastikan encoding sudah benar
        soup = BeautifulSoup(response.text, 'html.parser')

        # --- SELEKTOR YANG BENAR (DARI SCRIPT ANDA) ---
        # Menggunakan 'ol.trend-card__list li' untuk mendapatkan elemen list-nya
        trend_items = soup.select('ol.trend-card__list li')

        if not trend_items:
            print("❌ Error: Tidak dapat menemukan daftar tren. Struktur HTML mungkin berubah.")
            return None

        # Mengambil teks dari tag 'a' di dalam setiap 'li'
        trends = []
        for item in trend_items[:4]: # Batasi hanya 4 tren teratas
            link = item.find('a')
            if link:
                # Menjaga format asli (teks atau hashtag)
                trend_text = link.get_text(strip=True)
                trends.append(trend_text)

        print(f"✅ Tren yang ditemukan: {trends}")
        return trends

    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses trends24.in: {e}")
        return None
    except Exception as e:
        print(f"Terjadi error: {e}")
        return None
