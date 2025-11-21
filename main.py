import streamlit as st
import pandas as pd
import requests
import json
import random
from datetime import datetime, timedelta
from scipy.stats import poisson

# ---------------- AYARLAR ----------------
FOOTBALL_API_KEY = 'a0280470fe8d45f7a3680c7f3bc7efde'
GEMINI_API_KEY = 'AIzaSyA_FyCVlu0ZVwTeBolhq5DjPa5_xkXk3eA'
BASE_URL = "https://api.football-data.org/v4"

LIGLER = {
    "İngiltere Premier Lig": "PL",
    "İspanya La Liga": "PD",
    "Almanya Bundesliga": "BL1",
    "İtalya Serie A": "SA",
    "Fransa Ligue 1": "FL1",
    "Türkiye Süper Lig": "TR",
    "Hollanda Eredivisie": "DED",
    "Şampiyonlar Ligi": "CL"
}

# Session State Başlatma
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'tablo_verisi' not in st.session_state:
    st.session_state.tablo_verisi = []
if 'secilen_lig_ismi_state' not in st.session_state:
    st.session_state.secilen_lig_ismi_state = None
if 'yorumlar' not in st.session_state: 
    st.session_state.yorumlar = {}

# ---------------- YARDIMCI FONKSİYONLAR ----------------

def get_current_week_dates():
    bugun = datetime.now()
    pazartesi = bugun - timedelta(days=bugun.weekday())
    pazar = pazartesi + timedelta(days=6)
    return pazartesi, pazar

def veri_cek(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Veri hatası: {e}")
        return None

def gemini_yorumla(prompt, mac_adi):
    if mac_adi in st.session_state.yorumlar:
        return st.session_state.yorumlar[mac_adi]
        
    modeller = ["gemini-2.5-flash-preview-09-2025", "gemini-flash-lite-latest", "gemini-pro-latest"]
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    son_hata = ""
    for model in modeller:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                yorum = response.json()['candidates'][0]['content']['parts'][0]['text']
                st.session_state.yorumlar[mac_adi] = yorum 
                return yorum
            else:
                hata_mesaji = response.json().get('error', {}).get('message', response.text)
                son_hata = f"Model: {model} | Kod: {response.status_code} | Mesaj: {hata_mesaji}"
                continue 
        except Exception as e:
            son_hata = str(e)
            continue
    return f"⚠️ Yapay zeka yanıt veremedi. (Hata: {son_hata})"

def lig_istatistiklerini_getir(lig_kodu):
    data = veri_cek(f"competitions/{lig_kodu}/standings")
    if data: return data['standings'][0]['table']
    return []

def takim_gucunu_hesapla(takim_adi, puan_tablosu):
    toplam_mac = sum(t['playedGames'] for t in puan_tablosu)
    toplam_gol = sum(t['goalsFor'] for t in puan_tablosu)
    if toplam_mac == 0: return 1.0, 1.0
    lig_gol_ort = toplam_gol / toplam_mac
    takim = next((t for t in puan_tablosu if t['team']['name'] == takim_adi), None)
    if not takim or takim['playedGames'] == 0: return 1.0, 1.0
    saldiri = (takim['goalsFor'] / takim['playedGames']) / lig_gol_ort
    savunma = (takim['goalsAgainst'] / takim['playedGames']) / lig_gol_ort
    return saldiri, savunma

def poisson_oran_hesapla(ev_sahibi, deplasman, puan_tablosu):
    ev_sald, ev_sav = takim_gucunu_hesapla(ev_sahibi, puan_tablosu)
    dep_sald, dep_sav = takim_gucunu_hesapla(deplasman, puan_tablosu)
    LIG_ORT = 1.4 
    ev_xg = ev_sald * dep_sav * LIG_ORT
    dep_xg = dep_sald * ev_sav * LIG_ORT * 0.85
    
    ev_kazanma = 0
    beraberlik = 0
    dep_kazanma = 0
    for i in range(6):
        for j in range(6):
            olasilik = poisson.pmf(i, ev_xg) * poisson.pmf(j, dep_xg)
            if i > j: ev_kazanma += olasilik
            elif i == j: beraberlik += olasilik
            else: dep_kazanma += olasilik
            
    oran_1 = round(1 / ev_kazanma, 2) if ev_kazanma > 0 else 1.0
    oran_x = round(1 / beraberlik, 2) if beraberlik > 0 else 1.0
    oran_2 = round(1 / dep_kazanma, 2) if dep_kazanma > 0 else 1.0
    return oran_1, oran_x, oran_2, ev_xg, dep_xg

def rastgele_form_uret():
    return [random.choice(["G", "B", "M"]) for _ in range(5)]

def get_form_html(form_list):
    html = ""
    for sonuc in form_list:
        if sonuc == "G": color = "#38c172"
        elif sonuc == "B": color = "#ffed4a"
        else: color = "#e3342f"
        html += f'<span style="background-color: {color}; color: #111; padding: 2px 6px; border-radius: 4px; margin-right: 2px; font-weight: bold;">{sonuc}</span>'
    return html

def simulate_match_info(ev_sahibi):
    stadlar = {
        "Arsenal FC": "Emirates Stadyumu", "Chelsea FC": "Stamford Bridge",
        "Manchester United": "Old Trafford", "Galatasaray": "RAMS Park",
        "Fenerbahçe": "Şükrü Saraçoğlu", "FC Bayern München": "Allianz Arena",
        "Liverpool FC": "Anfield", "Manchester City FC": "Etihad Stadium"
    }
    stad = stadlar.get(ev_sahibi, f"{ev_sahibi} Stadyumu")
    hava = random.choice(["Açık, 15°C", "Parçalı Bulutlu, 12°C", "Yağmurlu, 9°C"])
    return stad, hava

# ---------------- ARAYÜZ ----------------
st.set_page_config(page_title="Futbol Analiz", layout="wide")
st.title("⚽ Haftalık Futbol Bülteni")

# Filtreler
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    secilen_lig = st.selectbox("Lig", list(LIGLER.keys()))
    secilen_lig_kodu = LIGLER[secilen_lig]
pts, pzr = get_current_week_dates()
with c2: baslangic = st.date_input("Başlangıç", pts)
with c3: bitis = st.date_input("Bitiş", pzr)
with c4: 
    st.write("")
    # Buton state'i eski sürümlerde sorunlu olabilir, session state ile kontrol
    if st.button("🔍 Bülteni Getir"):
        st.session_state.tetiklendi = True
    else:
        st.session_state.tetiklendi = False

# Veri Çekme İşlemi
if st.session_state.get('tetiklendi'):
    st.session_state.data_loaded = False
    st.session_state.secilen_lig_ismi_state = secilen_lig
    st.session_state.tablo_verisi = []
    st.session_state.yorumlar = {}
    
    with st.spinner("Veriler çekiliyor..."):
        maclar_data = veri_cek(f"competitions/{secilen_lig_kodu}/matches", {
            'dateFrom': baslangic.strftime('%Y-%m-%d'),
            'dateTo': bitis.strftime('%Y-%m-%d')
        })
        puan_tablosu = lig_istatistiklerini_getir(secilen_lig_kodu)
        
        if maclar_data and 'matches' in maclar_data and puan_tablosu:
            ham_veri = []
            for mac in maclar_data['matches']:
                ev, dep = mac['homeTeam']['name'], mac['awayTeam']['name']
                tarih = mac['utcDate'][:10] + " " + mac['utcDate'][11:16]
                o1, ox, o2, exg, dxg = poisson_oran_hesapla(ev, dep, puan_tablosu)
                ev_form, dep_form = rastgele_form_uret(), rastgele_form_uret()
                
                ham_veri.append({
                    "Tarih": tarih, "Ev Sahibi": ev, "Deplasman": dep,
                    "Maç ID": f"{ev} vs {dep} ({tarih})",
                    "1": o1, "X": ox, "2": o2,
                    "Ev xG": round(exg, 2), "Dep xG": round(dxg, 2),
                    "Ev Form List": ev_form, "Dep Form List": dep_form,
                    "Ev Form": " ".join(ev_form), 
                    "Dep Form": " ".join(dep_form)
                })
            st.session_state.tablo_verisi = ham_veri
            st.session_state.data_loaded = True
        else:
            st.error("Maç bulunamadı veya veri çekilemedi.")

# Tablo ve Detay Gösterimi
if st.session_state.data_loaded:
    st.success(f"✅ {st.session_state.secilen_lig_ismi_state} Bülteni")
    
    # 1. Tabloyu Göster (En sade hali - HATASIZ)
    df = pd.DataFrame(st.session_state.tablo_verisi)
    gosterilecek = ["Tarih", "Ev Sahibi", "Deplasman", "1", "X", "2", "Ev xG", "Dep xG", "Ev Form", "Dep Form"]
    # ÖNEMLİ: key ve column_config parametrelerini sildik
    st.dataframe(df[gosterilecek]) 
    
    st.divider()
    
    # 2. Maç Seçimi
    st.subheader("🔎 Detaylı Analiz")
    secenekler = [row['Maç ID'] for row in st.session_state.tablo_verisi]
    secilen_mac_id = st.selectbox("Analiz etmek istediğiniz maçı seçiniz:", secenekler)
    
    if secilen_mac_id:
        veri = next(item for item in st.session_state.tablo_verisi if item['Maç ID'] == secilen_mac_id)
        
        st.markdown(f"### 🏟️ {veri['Ev Sahibi']} - {veri['Deplasman']}")
        
        # Tabs (Sekme) - Hata korumalı
        try:
            t1, t2, t3 = st.tabs(["📝 Özet", "🤖 Yorum AI", "📊 İstatistik"])
        except:
            # Tabs desteklenmiyorsa alt alta göster
            t1 = st.container()
            t1.markdown("#### 📝 Özet")
            t2 = st.container()
            t2.markdown("#### 🤖 Yorum AI")
            t3 = st.container()
            t3.markdown("#### 📊 İstatistik")
            
        with t1:
            stad, hava = simulate_match_info(veri['Ev Sahibi'])
            col1, col2 = st.columns(2)
            col1.info(f"**Stad:** {stad}\n\n**Hava:** {hava}")
            col2.markdown(f"**🏠 {veri['Ev Sahibi']} Form:** {get_form_html(veri['Ev Form List'])}", unsafe_allow_html=True)
            col2.markdown(f"**✈️ {veri['Deplasman']} Form:** {get_form_html(veri['Dep Form List'])}", unsafe_allow_html=True)
            
        with t2:
            # Benzersiz key olmadan buton oluşturuyoruz
            if st.button("✨ Yapay Zeka Yorumlasın"):
                with st.spinner("Analiz yapılıyor..."):
                    prompt = f"Maç: {veri['Ev Sahibi']} vs {veri['Deplasman']}. Oranlar: 1({veri['1']}), X({veri['X']}), 2({veri['2']}). xG: {veri['Ev xG']} - {veri['Dep xG']}. Formlar: Ev {veri['Ev Form']}, Dep {veri['Dep Form']}. Yorumla."
                    yorum = gemini_yorumla(prompt, secilen_mac_id)
                    st.markdown(f"### 🎙️ Analist Yorumu:\n{yorum}")
            elif secilen_mac_id in st.session_state.yorumlar:
                st.markdown(f"### 🎙️ Analist Yorumu (Kayıtlı):\n{st.session_state.yorumlar[secilen_mac_id]}")
                
        with t3:
            c1, c2 = st.columns(2)
            c1.metric("Ev xG", veri['Ev xG'])
            c2.metric("Dep xG", veri['Dep xG'])