# src/peticionador/agentes/agente_extrator.py
import logging
import json
# import re # Mantenha se for usar extrair_numero_processo_cnj depois
from typing import Dict, Optional

from peticionador.servicos.integrador_gemini import ClienteGemini

logging.basicConfig(level=logging.INFO) # Considere mover para um config central de logging
log = logging.getLogger(__name__)

def extrair_dados_iniciais_gemini(texto_pagina: Optional[str]) -> Dict[str, str]:
    dados_padrao = {"recorrente": "Desconhecido", "tipo_recurso": "Indeterminado"}

    if not texto_pagina:
        log.warning("Texto da primeira página ausente para extração inicial. Retornando dados padrão.")
        return dados_padrao

    cliente = ClienteGemini() # Usa o modelo FLASH por padrão
    
    # Verifique se a API Key está configurada e se o modelo foi instanciado
    if cliente.model_instance is None: # <--- MUDANÇA AQUI (de cliente.chat para cliente.model_instance)
         log.error("Cliente Gemini (Flash) não instanciado corretamente. Verifique API Key e logs. Não é possível extrair dados iniciais.")
         return dados_padrao # Retorna padrão para evitar mais erros

    prompt = (
        "Você é um assistente jurídico eficiente. Analise o texto da primeira página de um recurso judicial brasileiro abaixo:\n\n"
        "--- TEXTO DA PRIMEIRA PÁGINA ---\n"
        f"{texto_pagina}\n"
        "--- FIM DO TEXTO ---\n\n"
        "Sua tarefa é extrair DUAS informações:\n"
        "1. O nome completo do RECORRENTE (a parte que interpôs o recurso).\n"
        "2. O TIPO DE RECURSO principal mencionado (identifique como 'RE', 'REsp', 'Agravo' ou 'Indeterminado' se não for claro).\n\n"
        "Responda APENAS no formato JSON, como no exemplo abaixo:\n"
        "{\n"
        '  "recorrente": "Nome Completo do Recorrente Encontrado",\n'
        '  "tipo_recurso": "REsp"\n'
        "}\n\n"
        'Se não conseguir encontrar o nome do recorrente, use o valor "Desconhecido".\n'
        'Se não conseguir identificar o tipo de recurso claramente como RE, REsp ou Agravo, use o valor "Indeterminado".\n'
        "Não inclua nenhuma outra informação ou explicação na sua resposta, apenas o JSON."
    )

    log.info("Enviando prompt para Gemini (Flash) para extração inicial de dados...")
    # A função resumir() agora chama internamente gerar_conteudo()
    # Para esta tarefa, a temperatura padrão do modelo flash deve ser suficiente.
    resposta_api = cliente.resumir(prompt) 

    if resposta_api:
        log.debug(f"Resposta recebida da API Gemini para extração: {resposta_api[:200]}...") # Log truncado
        if "[ERRO:" in resposta_api or "[CONTEÚDO BLOQUEADO PELA API:" in resposta_api or "[RESPOSTA INESPERADA OU VAZIA DA API GEMINI]" in resposta_api:
            log.error(f"API Gemini retornou erro/bloqueio durante extração inicial: {resposta_api}")
            return dados_padrao # Retorna padrão em caso de erro da API

        try:
            resposta_limpa = resposta_api.strip()
            if resposta_limpa.startswith("```json"):
                resposta_limpa = resposta_limpa[7:] 
            if resposta_limpa.endswith("```"):
                resposta_limpa = resposta_limpa[:-3] 
            resposta_limpa = resposta_limpa.strip()

            if not resposta_limpa: # Checa se a string ficou vazia após limpeza
                log.warning("Resposta da API Gemini para extração inicial ficou vazia após limpeza.")
                return dados_padrao

            dados_extraidos = json.loads(resposta_limpa)

            if isinstance(dados_extraidos, dict) and "recorrente" in dados_extraidos and "tipo_recurso" in dados_extraidos:
                tipos_validos = ["RE", "REsp", "Agravo", "Indeterminado", "Desconhecido"]
                if dados_extraidos.get("tipo_recurso") not in tipos_validos:
                    log.warning(f"Tipo de recurso '{dados_extraidos.get('tipo_recurso')}' não reconhecido pela IA. Usando 'Indeterminado'.")
                    dados_extraidos["tipo_recurso"] = "Indeterminado"
                
                # Garante que o recorrente não seja uma string vazia se a IA retornar assim
                if not dados_extraidos.get("recorrente", "").strip():
                    dados_extraidos["recorrente"] = "Desconhecido"

                log.info(f"Dados extraídos com sucesso pelo Gemini: {dados_extraidos}")
                return dados_extraidos
            else:
                log.warning(f"Formato JSON da resposta da API Gemini inesperado (extração inicial): {resposta_api}")
        except json.JSONDecodeError as e:
            log.error(f"Falha ao decodificar JSON da resposta da API Gemini (extração inicial): {e}\nResposta recebida:\n{resposta_api}")
        except Exception as e:
             log.error(f"Erro inesperado ao processar resposta da API Gemini (extração inicial): {e}\nResposta recebida:\n{resposta_api}")
    else:
        log.warning("API Gemini não retornou resposta para extração inicial.")

    log.warning("Retornando dados padrão devido a falha na extração Gemini (extração inicial).")
    return dados_padrao