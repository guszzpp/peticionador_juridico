# src/peticionador/agentes/agente_extrator.py

from typing import Dict


def extrair_info_roberta(texto_pagina: str) -> Dict[str, str]:
    """
    Mock de extração com RoBERTa: identifica nome do recorrente e tipo de recurso.

    Parâmetros:
        texto_pagina (str): Texto da primeira página da petição.

    Retorna:
        dict: {
            "recorrente": str,
            "tipo_recurso": str
        }
    """
    nome = "Desconhecido"
    for linha in texto_pagina.splitlines():
        if "recorrente" in linha.lower():
            partes = linha.split(":")
            if len(partes) > 1:
                nome = partes[1].strip()
                break

    tipo = "Agravo" if "agravo" in texto_pagina.lower() else "Indeterminado"

    return {
        "recorrente": nome,
        "tipo_recurso": tipo
    }
