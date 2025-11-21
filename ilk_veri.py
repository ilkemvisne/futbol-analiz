import streamlit as st
import pandas as pd
import requests

# ---------------- AYARLAR ----------------
# Sizin API Anahtarınız
API_KEY = 'a0280470fe8d45f7a3680c7f3bc7efde'
# Veri çekeceğimiz adres (Premier Lig Puan Durumu)
URL = 'https://api.football-data.org/v4/competitions/PL/standings'

# ---------------- SAYFA BAŞLIĞI ----------------
st.title("⚽ İlk Futbol Verisi Testi")
st.write("Bu uygulama, API anahtarınızı kullanarak canlı puan durumunu çeker.")

# ---------------- VERİ ÇEKME İŞLEMİ ----------------
headers = {'X-Auth-Token': API_KEY}

try:
    # İstek gönderiyoruz
    response = requests.get(URL, headers=headers)
    
    # Eğer hata varsa programı durdur
    response.raise_for_status()
    
    # Gelen cevabı JSON (veri) formatına çevir
    data = response.json()
    
    st.success("✅ Bağlantı Başarılı! Veriler alındı.")

    # JSON içinden sadece 'Total' puan tablosunu alalım
    puan_tablosu = data['standings'][0]['table']
    
    # Verileri düzgün bir listeye dönüştürelim
    takim_listesi = []
    for satir in puan_tablosu:
        takim_listesi.append({
            'Sıra': satir['position'],
            'Takım': satir['team']['name'],
            'Oynanan': satir['playedGames'],
            'Galibiyet': satir['won'],
            'Beraberlik': satir['draw'],
            'Mağlubiyet': satir['lost'],
            'Puan': satir['points']
        })
        
    # Pandas ile tablo oluşturup ekrana basalım
    df = pd.DataFrame(takim_listesi)
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"❌ HATA OLUŞTU: {e}")