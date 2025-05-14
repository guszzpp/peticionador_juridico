# src/peticionador/agentes/agente_estrategista.py
import logging
import json
from typing import Dict, List, Optional
from peticionador.servicos.integrador_gemini import ClienteGemini

log = logging.getLogger(__name__)

def sugerir_teses(
    texto_peticao: str, modelos_existentes: List[str]
) -> Dict[str, List[str]]:
    """
    Sugere teses defensivas com base no conteúdo da petição usando Gemini Flash.

    Parâmetros:
        texto_peticao (str): Texto integral da petição do recorrente.
        modelos_existentes (list): Lista de nomes de modelos/teses já disponíveis.

    Retorna:
        dict: {"presentes": [teses existentes], "sugeridas": [teses novas]}
    """
    teses_sugeridas_api = []

    # Usa Gemini Flash por padrão
    cliente = ClienteGemini() # Padrão Flash

    # Prompt para extrair argumentos e sugerir contra-argumentos/teses    
    prompt = (
        "Você é um Procurador de Justiça especializado em direito penal brasileiro e na elaboração de contrarrazões recursais "
        "para o Ministério Público. Analise o texto da petição de recurso a seguir:\n\n"
        f"--- INÍCIO DO TEXTO DA PETIÇÃO ---\n{texto_peticao}\n--- FIM DO TEXTO DA PETIÇÃO ---\n\n"
        "Com base nos argumentos apresentados pelo recorrente no texto acima, identifique as principais teses ou pontos levantados por ele. "
        "Para cada argumento principal do recorrente, sugira uma ou mais teses de defesa concisas e aplicáveis que o Ministério Público poderia usar nas contrarrazões. "
        "Priorize teses comuns em recursos especiais e extraordinários (ex: ausência de prequestionamento, Súmula 7/STJ, Súmula 284/STF, ausência de repercussão geral, reexame de provas, etc.), mas também sugira teses de mérito pertinentes.\n\n"
        "Liste APENAS as teses de defesa sugeridas para o MP, uma por linha, sem numeração, marcadores ou explicações adicionais. Se nenhuma tese clara puder ser sugerida, retorne uma lista vazia.\n"
        "Exemplo de saída desejada:\n"
        "Ausência de prequestionamento da matéria X\n"
        "Incidência da Súmula 7 do STJ\n"
        "Inépcia da argumentação recursal (Súmula 284/STF)\n"
        "Mérito: Manutenção da decisão por seus próprios fundamentos"        
    )

    resposta = cliente.resumir(prompt)

    if resposta:        
        teses_brutas = [linha.strip() for linha in resposta.splitlines() if linha.strip()]
        if teses_brutas:
             teses_sugeridas_api = teses_brutas
             log.info(f"[INFO GEMINI TESES] Teses sugeridas pela API: {teses_sugeridas_api}")
        else:
             log.warning("[AVISO GEMINI TESES] API retornou resposta vazia ou não formatada como lista de teses.")
    else:
        log.warning("[AVISO GEMINI TESES] API não retornou resposta para sugestão de teses.")
    
    presentes = [t for t in teses_sugeridas_api if t in modelos_existentes]
    return {"presentes": presentes, "sugeridas": teses_sugeridas_api}