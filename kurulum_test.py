import streamlit as st
import pandas as pd
import requests
import scipy
import time

print("--------------------------------------------------")
print("Sistem Kontrolü Başlatılıyor...")
print("--------------------------------------------------")

try:
    print(f"1. Pandas (Veri İşleme): {pd.__version__}")
    print(f"2. Requests (İnternet): {requests.__version__}")
    print(f"3. Scipy (İstatistik): {scipy.__version__}")
    print(f"4. Streamlit (Arayüz): {st.__version__}")
    print("\nTEBRİKLER! Her şey doğru yüklenmiş.")
except Exception as e:
    print(f"HATA: {e}")