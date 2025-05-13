# src/peticionador/agentes/agente_resumidor.py
import logging
from peticionador.servicos.integrador_gemini import ClienteGemini # TipoModeloGemini não é usado aqui diretamente
from typing import Optional # Dict, List, Tuple, Any, Literal não são usados aqui

log = logging.getLogger(__name__)

def gerar_resumo_tecnico(texto_para_resumir: Optional[str]) -> str:
    if not texto_para_resumir or not texto_para_resumir.strip(): # Adicionada checagem de strip
        log.warning("Texto para resumo está vazio ou None. Retornando default.")
        return "[Resumo não gerado - Texto de entrada ausente]"

    log.info("Usando Gemini (Flash por padrão) para resumo técnico.")
    # ClienteGemini usa Flash por padrão, se ClienteGemini.DEFAULT_MODEL_PRO for desejado, precisa especificar.
    # Para resumos, Flash é geralmente suficiente e mais rápido/barato.
    cliente = ClienteGemini() # Modelo padrão (Flash)

    # Verifique se a API Key está configurada e se o modelo foi instanciado
    if cliente.model_instance is None: # <--- MUDANÇA AQUI (se houvesse .chat antes, mas não havia)
         log.error("Cliente Gemini não instanciado corretamente para resumo. Verifique API Key e logs.")
         return "[ERRO: Modelo Gemini não pôde ser inicializado para resumo.]"

    prompt = (
        f"""Sua tarefa é redigir um breve relatório introdutório para uma peça de contrarrazões recursais criminais, seguindo o estilo formal do Ministério Público. O relatório deve ser sucinto, objetivo, impessoal e focado estritamente nos atos processuais relevantes mencionados no texto fornecido (como números de acórdão, datas importantes, artigos de lei e súmulas invocados pelo recorrente, e os fundamentos centrais do recurso). Não emita juízo de valor nem realize análise jurídica. Conclua o relatório obrigatoriamente com a frase: "É o sucinto relatório."

Texto base fornecido (geralmente o recurso da outra parte):
---
{texto_para_resumir}
---

Relatório das Contrarrazões:
"""
    )
    
    # A função resumir() em ClienteGemini agora chama internamente gerar_conteudo().
    # Para resumos, a temperatura padrão do modelo costuma ser adequada.
    resumo = cliente.resumir(prompt)

    if resumo is None:
         log.error(f"Falha ao gerar resumo com {cliente.target_model_name}. A resposta foi None.")
         return "[Resumo não gerado - Falha na API Gemini, resposta None]"
    elif "[ERRO:" in resumo or "[CONTEÚDO BLOQUEADO PELA API:" in resumo or "[RESPOSTA INESPERADA OU VAZIA DA API GEMINI]" in resumo:
        log.error(f"API Gemini retornou erro/bloqueio durante resumo: {resumo}")
        return f"[Falha na geração do resumo pela IA. Detalhe: {resumo}]"


    # Pequena limpeza para garantir que não haja prefixos indesejados da IA
    if resumo.strip().lower().startswith("relatório das contrarrazões:"):
        resumo = resumo.strip()[len("relatório das contrarrazões:"):].strip()
    
    return resumo.strip() if resumo else "[Resumo não gerado - Resposta vazia da API Gemini]"