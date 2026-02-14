import requests, time
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def log_message(module: str, message: str):
    timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{module}] {message}", flush=True)

def fetch_limt200(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD, limit=200, module="apiCall"):
    """
    Busca dados de uma API Sienge com paginação.
    - BASE_URL: endpoint da API (sem parâmetros de paginação)
    - SIENGE_USERNAME / SIENGE_PASSWORD: credenciais de autenticação
    - limit: quantidade de registros por página
    - module: nome do módulo para logs
    Retorna um DataFrame com todos os registros.
    """
    all_data, offset = [], 0
    log_message(module, "Download API ")
    while True:
        url = f"{BASE_URL}?limit={limit}&offset={offset}"
        try:
            response = requests.get(url, auth=(SIENGE_USERNAME, SIENGE_PASSWORD), timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log_message(module, f"❌ Erro na requisição: {e}")
            break
        try:
            dados = response.json()
        except Exception:
            log_message(module, f"❌ Resposta não é JSON válido: {response.text}")
            break
        results = dados.get("results", [])
        if not results:
            break

        all_data.extend(results)
        offset += limit
    df = pd.DataFrame(all_data)
    return df


def fetch_limtFull(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD, module="apiCall", timeout=300):
    """
    - BASE_URL: endpoint da API (sem parâmetros de offset)
    - SIENGE_USERNAME / SIENGE_PASSWORD: credenciais
    - module: nome para logs
    - timeout: tempo máximo da requisição
    Retorna um DataFrame com todos os registros.
    """
    start_time = time.time()
    all_data = []
    offset = 0

    try:
        log_message(module, "Download API ")
        log_message(module, f"🔗 Conexão com API {module} ... offset={offset}")
        response = requests.get(f"{BASE_URL}&offset={offset}", auth=(SIENGE_USERNAME, SIENGE_PASSWORD), timeout=timeout)
        response.raise_for_status()
        elapsed = time.time() - start_time
        log_message(module, f"✅ Dados via API acessados com sucesso | Tempo: {elapsed:.2f}s")
    except requests.exceptions.RequestException as e:
        log_message(module, f"❌ Erro na requisição: {e}")
        return pd.DataFrame()
    try:
        dados = response.json()
    except Exception:
        log_message(module, f"❌ Resposta não é JSON válido: {response.text}")
        return pd.DataFrame()
    if not dados or "data" not in dados or not dados["data"]:
        log_message(module, "⚠️ API respondeu sem campo 'data'. Encerrando coleta.")
        return pd.DataFrame()
    all_data.extend(dados["data"])
    elapsed = time.time() - start_time
    log_message(module, f"📊 Registros acumulados: {len(all_data)} | Tempo total: {elapsed:.2f}s")

    return pd.DataFrame({"data": all_data})
