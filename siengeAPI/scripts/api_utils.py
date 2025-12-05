import requests, json, os
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


MAX_SIZE_MB = 768
def fetch_limtFull(BASE_URL, SIENGE_USERNAME, SIENGE_PASSWORD, module, json_path_env=None, timeout=300):
    all_data = []
    file_index = 1
    offset = 0

    while True:
        try:
            log_message(module, f"🔗 Conexão com API {module} ... offset={offset}")
            response = requests.get(
                f"{BASE_URL}&offset={offset}",  # ajuste conforme paginação suportada pela API
                auth=(SIENGE_USERNAME, SIENGE_PASSWORD),
                timeout=timeout)
            response.raise_for_status()
            log_message(module, "✅ Dados via API acessados com sucesso")
        except requests.exceptions.RequestException as e:
            log_message(module, f"❌ Erro na requisição: {e}")
            break
        try:
            dados = response.json()
        except Exception:
            log_message(module, f"❌ Resposta não é JSON válido: {response.text}")
            break
        if not dados or "data" not in dados or not dados["data"]:
            log_message(module, "❌ API respondeu, mas não retornou dados.")
            break

        # acumula dados
        all_data.extend(dados["data"])

        # cria DataFrame parcial para medir tamanho
        df = pd.DataFrame(all_data)
        size_mb = df.memory_usage(deep=True).sum() / (1024**2)
        log_message(module, f"📊 Registros acumulados: {len(df)} | Tamanho: {size_mb:.2f} MB")

        # se atingiu limite, salva arquivo e reinicia acumulador
        if size_mb >= MAX_SIZE_MB:
            if json_path_env:
                caminho_base = Path(os.getenv(json_path_env, f"/scripts/{module}.json"))
                caminho = caminho_base.with_name(f"{module}.{file_index}.json")
                try:
                    with open(caminho, "w", encoding="utf-8") as f:
                        json.dump({"data": all_data}, f, ensure_ascii=False)
                    log_message(module, f"Arquivo JSON salvo em: {caminho}")
                except Exception as e:
                    log_message(module, f"⚠️ Falha ao salvar JSON: {e}")
            # prepara para próximo arquivo
            file_index += 1
            offset += len(all_data)
            all_data = []  # limpa acumulador para próximo bloco
            continue
        else:
            # fim dos dados, salva último arquivo
            if json_path_env and all_data:
                caminho_base = Path(os.getenv(json_path_env, f"/scripts/{module}.json"))
                caminho = caminho_base.with_name(f"{module}.{file_index}.json")
                try:
                    with open(caminho, "w", encoding="utf-8") as f:
                        json.dump({"data": all_data}, f, ensure_ascii=False)
                    log_message(module, f"Arquivo JSON salvo em: {caminho}")
                except Exception as e:
                    log_message(module, f"⚠️ Falha ao salvar JSON: {e}")
            break

    # retorna DataFrame consolidado
    return pd.DataFrame(all_data)

