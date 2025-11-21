import requests
import json

# Sizin Anahtarınız
API_KEY = 'AIzaSyA_FyCVlu0ZVwTeBolhq5DjPa5_xkXk3eA'

print("\n🔍 GEMINI API TEŞHİS ARACI")
print("==========================================")

# TEST 1: Anahtar Geçerli mi? (Model Listesini Çekme)
print("\n1. ADIM: Anahtar Kontrolü Yapılıyor...")
url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

try:
    response = requests.get(url_list)
    
    if response.status_code == 200:
        print("✅ BAŞARILI! Anahtar çalışıyor.")
        print("Kullanabileceğiniz Modeller:")
        data = response.json()
        if 'models' in data:
            for m in data['models']:
                # Sadece metin üretebilen modelleri göster
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(f"   - {m['name']}")
    else:
        print(f"❌ HATA: Anahtar reddedildi!")
        print(f"Hata Kodu: {response.status_code}")
        print(f"Google Mesajı: {response.text}")

except Exception as e:
    print(f"❌ Bağlantı Hatası: {e}")

print("\n" + "-"*30)

# TEST 2: Doğrudan İstek Gönderme
print("\n2. ADIM: Örnek Mesaj Gönderiliyor...")
url_generate = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
headers = {'Content-Type': 'application/json'}
payload = { "contents": [{ "parts": [{"text": "Merhaba, nasılsın?"}] }] }

try:
    response = requests.post(url_generate, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print("✅ BAŞARILI! Cevap alındı:")
        print(response.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        print(f"❌ HATA: İstek başarısız oldu.")
        print(f"Hata Kodu: {response.status_code}")
        print(f"Google Mesajı: {response.text}")

except Exception as e:
    print(f"❌ Bağlantı Hatası: {e}")

print("\n==========================================")