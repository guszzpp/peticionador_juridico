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

    texto_lower = texto_pagina.lower()

    if "recurso extraordinário" in texto_lower:
        tipo = "RE"
    elif "recurso especial" in texto_lower:
        tipo = "REsp"
    elif "extraordinário" in texto_lower:
        tipo = "RE"
    elif "especial" in texto_lower:
        tipo = "REsp"
    elif "agravo" in texto_lower:
        tipo = "Agravo"
    else:
        tipo = "Indeterminado"

    return {"recorrente": nome, "tipo_recurso": tipo}
