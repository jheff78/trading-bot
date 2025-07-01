from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import requests
import csv
import random

# === TELEGRAM ===
TELEGRAM_TOKEN = 'SEU_TOKEN_AQUI'
CHAT_ID = 'SEU_CHAT_ID_AQUI'

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.get(url, params={'chat_id': CHAT_ID, 'text': msg})
    except:
        print("❌ Telegram falhou.")

# === METAS DIÁRIAS ===
meta_lucro = 5.0
meta_perda = -3.0
banca_inicial = 100.0
banca_atual = banca_inicial
valor_entrada = 5.0

def calcular_resultado():
    global banca_atual
    resultado = random.choice(["WIN", "LOSS"])
    if resultado == "WIN":
        banca_atual += valor_entrada * 0.85
    else:
        banca_atual -= valor_entrada
    return resultado

def verificar_metas():
    lucro_pct = ((banca_atual - banca_inicial) / banca_inicial) * 100
    if lucro_pct >= meta_lucro:
        enviar_telegram(f"✅ Meta de LUCRO atingida: +{lucro_pct:.2f}%\nEncerrando o bot.")
        return True
    elif lucro_pct <= meta_perda:
        enviar_telegram(f"🛑 Meta de PERDA atingida: {lucro_pct:.2f}%\nEncerrando o bot.")
        return True
    return False

def detectar_pullback(df):
    if df["close"].iloc[-2] < df["ema"].iloc[-2] and df["close"].iloc[-1] > df["ema"].iloc[-1]:
        return "PULLBACK_COMPRA"
    elif df["close"].iloc[-2] > df["ema"].iloc[-2] and df["close"].iloc[-1] < df["ema"].iloc[-1]:
        return "PULLBACK_VENDA"
    return None

def analisar_confluencias(closes):
    df = pd.DataFrame()
    df["close"] = closes
    df["rsi"] = RSIIndicator(df["close"]).rsi()
    df["ema"] = EMAIndicator(df["close"], window=5).ema_indicator()

    rsi_oversold = df["rsi"].iloc[-1] < 30
    rsi_overbought = df["rsi"].iloc[-1] > 70
    ema_cima = df["close"].iloc[-1] > df["ema"].iloc[-1]
    ema_baixo = df["close"].iloc[-1] < df["ema"].iloc[-1]
    tendencia_alta = df["close"].iloc[-1] > df["close"].iloc[-2]
    tendencia_baixa = df["close"].iloc[-1] < df["close"].iloc[-2]
    pullback = detectar_pullback(df)

    confluencias_compra = [rsi_oversold, ema_cima, tendencia_alta, pullback == "PULLBACK_COMPRA"]
    confluencias_venda = [rsi_overbought, ema_baixo, tendencia_baixa, pullback == "PULLBACK_VENDA"]

    if sum(confluencias_compra) >= 3:
        return "COMPRA"
    elif sum(confluencias_venda) >= 3:
        return "VENDA"
    return "AGUARDAR"

def executar_entrada(tipo):
    hora = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        if tipo == "COMPRA":
            driver.find_element(By.XPATH, "//button[contains(text(),'COMPRAR')]").click()
        elif tipo == "VENDA":
            driver.find_element(By.XPATH, "//button[contains(text(),'VENDER')]").click()
        print(f"🎯 Entrada realizada: {tipo}")

        resultado = calcular_resultado()
        lucro_pct = ((banca_atual - banca_inicial) / banca_inicial) * 100

        with open("log_operacoes.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([hora, tipo, resultado, f"{banca_atual:.2f}", f"{lucro_pct:.2f}%"])

        enviar_telegram(f"📈 Entrada: {tipo}\n🎯 Resultado: {resultado}\n💰 Banca: {banca_atual:.2f}\n📊 Lucro: {lucro_pct:.2f}%")
    except Exception as e:
        print("❌ Erro na entrada:", e)

def capturar_precos_mock():
    return pd.Series([1.1670, 1.1672, 1.1675, 1.1673, 1.1676, 1.1679, 1.1680])

# === Início ===
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
driver.get("https://trade.avalonbroker.com")
input("⚠️ Faça login e pressione ENTER para iniciar...")

while True:
    if verificar_metas():
        break

    closes = capturar_precos_mock()
    acao = analisar_confluencias(closes)

    if acao != "AGUARDAR":
        executar_entrada(acao)
    else:
        print("🔍 Aguardando confluência...")

    time.sleep(60)
