#  src/peticionador/agentes/agente_gemini.py

from typing import Dict


def verificar_extracao_gemini(
    texto_pagina: str, dados_extraidos: Dict[str, str]
) -> Dict[str, str]:
    """
    MOCK: Verifica e corrige os dados extraídos, simulando uma resposta do Gemini.

    Parâmetros:
        texto_pagina (str): Primeira página da petição.
        dados_extraidos (dict): Saída original do RoBERTa.

    Retorna:
        dict: Dicionário validado (ou corrigido) com 'recorrente' e 'tipo_recurso'.
    """
    #  Simula uma verificação e correção
    if "agravo" in texto_pagina.lower():
        tipo = "Agravo"
    elif "apelação" in texto_pagina.lower():
        tipo = "Apelação"
    elif "mandado de segurança" in texto_pagina.lower():
        tipo = "Mandado de Segurança"
    else:
        tipo = dados_extraidos.get("tipo_recurso", "Indeterminado")

    if "recorrente" in texto_pagina.lower():
        nome_linha = next(
            (
                linha
                for linha in texto_pagina.splitlines()
                if "recorrente" in linha.lower()
            ),
            "",
        )
        nome = nome_linha.split(":")[-1].strip()
    else:
        nome = dados_extraidos.get("recorrente", "Desconhecido")

    return {"recorrente": nome, "tipo_recurso": tipo}
