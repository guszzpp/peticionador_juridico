# src/peticionador/agentes/agente_extrator.py

import logging
import json
import re # Mantenha se for usar extrair_numero_processo_cnj depois
from typing import Dict, Optional

# Importa o cliente Gemini que já configuramos para usar Flash por padrão
from peticionador.servicos.integrador_gemini import ClienteGemini

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def extrair_dados_iniciais_gemini(texto_pagina: Optional[str]) -> Dict[str, str]:
    """
    Usa Gemini (Flash) para extrair 'recorrente' e 'tipo_recurso' da primeira página.

    Parâmetros:
        texto_pagina (Optional[str]): Texto da primeira página da petição.

    Retorna:
        dict: {"recorrente": str, "tipo_recurso": str}
              com valores padrão "Desconhecido" e "Indeterminado" em caso de falha.
    """
    # Valores padrão caso a extração falhe
    dados_padrao = {"recorrente": "Desconhecido", "tipo_recurso": "Indeterminado"}

    if not texto_pagina:
        log.warning("Texto da primeira página ausente. Retornando dados padrão.")
        return dados_padrao

    # Instancia o cliente Gemini (usará Flash por padrão, conforme configurado)
    cliente = ClienteGemini()
    if cliente.chat is None: # Verifica se o cliente inicializou corretamente
         log.error("Cliente Gemini (Flash) não inicializado. Não é possível extrair dados iniciais.")
         return dados_padrao


    # Criar o prompt para o Gemini
    prompt = (
        "Você é um assistente jurídico eficiente. Analise o texto da primeira página de um recurso judicial brasileiro abaixo:\n\n"
        "--- TEXTO DA PRIMEIRA PÁGINA ---\n"
        f"{texto_pagina}\n"
        "--- FIM DO TEXTO ---\n\n"
        "Sua tarefa é extrair DUAS informações:\n"
        "1. Verificar quantos RECORRENTES existem (a parte que interpôs o recurso).\n"
        "2. O nome completo do RECORRENTE (a parte que interpôs o recurso).\n"
        "3. O TIPO DE RECURSO principal mencionado (identifique como 'RE', 'REsp', 'Agravo' ou 'Indeterminado' se não for claro).\n\n"
        "Responda APENAS no formato JSON, como no exemplo abaixo:\n"
        "{\n"
        '  "recorrente": "Nome Completo do Recorrente Encontrado",\n'
        '  "tipo_recurso": "REsp"\n'
        "}\n\n"
        'Se não conseguir encontrar o nome do recorrente, use o valor "Desconhecido".\n'
        'Se não conseguir identificar o tipo de recurso claramente como RE, REsp ou Agravo, use o valor "Indeterminado".\n'
        "Não inclua nenhuma outra informação ou explicação na sua resposta, apenas o JSON."
    )

    log.info("Enviando prompt para Gemini (Flash) para extração inicial...")
    resposta_api = cliente.resumir(prompt) # Usamos 'resumir' para enviar o prompt

    if resposta_api:
        log.info("Resposta recebida da API Gemini para extração.")
        try:
            # Limpa a resposta removendo cercas de markdown e espaços extras
            resposta_limpa = resposta_api.strip()
            if resposta_limpa.startswith("```json"):
                resposta_limpa = resposta_limpa[7:] # Remove ```json
            if resposta_limpa.endswith("```"):
                resposta_limpa = resposta_limpa[:-3] # Remove ```
            resposta_limpa = resposta_limpa.strip() # Remove espaços em branco

            dados_extraidos = json.loads(resposta_limpa)

            # Valida se o dicionário tem as chaves esperadas
            if isinstance(dados_extraidos, dict) and "recorrente" in dados_extraidos and "tipo_recurso" in dados_extraidos:
                # Limita os tipos de recurso válidos que aceitamos da IA
                tipos_validos = ["RE", "REsp", "Agravo", "Indeterminado", "Desconhecido"] # Aceita Desconhecido vindo da IA
                if dados_extraidos.get("tipo_recurso") not in tipos_validos:
                    log.warning(f"Tipo de recurso '{dados_extraidos.get('tipo_recurso')}' não reconhecido. Usando 'Indeterminado'.")
                    dados_extraidos["tipo_recurso"] = "Indeterminado"

                log.info(f"Dados extraídos com sucesso pelo Gemini: {dados_extraidos}")
                return dados_extraidos
            else:
                log.warning(f"Formato JSON da resposta da API Gemini inesperado: {resposta_api}")

        except json.JSONDecodeError as e:
            log.error(f"Falha ao decodificar JSON da resposta da API Gemini: {e}\nResposta recebida:\n{resposta_api}")
        except Exception as e:
             log.error(f"Erro inesperado ao processar resposta da API Gemini: {e}\nResposta recebida:\n{resposta_api}")
    else:
        log.warning("API Gemini não retornou resposta para extração inicial.")

    # Se chegou aqui, algo falhou, retorna o padrão
    log.warning("Retornando dados padrão devido a falha na extração Gemini.")
    return dados_padrao

# Mantenha a função extrair_numero_processo_cnj se você a adicionou antes
# def extrair_numero_processo_cnj(texto: str) -> Optional[str]:
#    # ... (código da função) ...
#    pass