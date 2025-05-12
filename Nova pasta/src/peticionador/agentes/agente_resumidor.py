# src/peticionador/agentes/agente_resumidor.py
import logging
from peticionador.servicos.integrador_gemini import ClienteGemini, TipoModeloGemini
from typing import Optional, Dict, List, Tuple, Any, Literal # Adicione os tipos que faltarem

log = logging.getLogger(__name__)

def gerar_resumo_tecnico(texto_para_resumir: Optional[str]) -> str:
    """
    Gera resumo técnico usando Gemini Pro (ou fallback).
    Recebe o texto específico a ser resumido.
    """
    if not texto_para_resumir:
        log.warning("Texto para resumo está vazio ou None. Retornando default.")
        return "[Resumo não gerado - Texto de entrada ausente]"

    # Especifica o modelo PRO para o resumo
    log.info("Usando Gemini (Flash) para resumo.")
    cliente = ClienteGemini()

    prompt = (
    f"""Redija a seção de relatório introdutório de uma peça processual criminal, empregando o estilo padronizado do Ministério Público de Goiás. Use a fórmula consagrada "É o sucinto relatório." no encerramento. Mantenha:
    - Tom impessoal, jurídico e objetivo;
    - Ausência de juízo de valor ou análise jurídica;
    - Foco exclusivo nos atos processuais relevantes (ex: número do acórdão, data, artigos invocados, súmulas citadas, fundamentos recursais);
    - Estruturação sintética, com uso de conectores formais como "nos autos anteriormente mencionados", "interpôs recurso especial", "com fundamento no artigo X, da Constituição da República";
    - Fecho padronizado com "É o sucinto relatório."

    {texto_para_resumir}
    """
    )
    
    resumo = cliente.resumir(prompt)

    if resumo is None:
         log.error(f"Falha ao gerar resumo com {modelo_desejado}. Verifique logs anteriores.")
         # Poderia tentar um fallback para Flash aqui se quisesse
         # log.info("Tentando fallback para resumo com Flash...")
         # cliente_flash = ClienteGemini() # Padrão Flash
         # resumo = cliente_flash.resumir(prompt)
         # if resumo is None:
         #      return "[Resumo não gerado - Falha na API Gemini]"

    return resumo or "[Resumo não gerado - Falha na API Gemini]"

