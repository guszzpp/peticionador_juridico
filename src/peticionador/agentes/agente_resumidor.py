# src/peticionador/agentes/agente_resumidor.py

from typing import Optional


def gerar_resumo_tecnico(texto_peticao: str) -> Optional[str]:
    """
    Gera um resumo técnico e impessoal da petição.

    Parâmetros:
        texto_peticao (str): Corpo completo da petição (sem a primeira página).

    Retorna:
        str: Resumo narrativo, técnico e estruturado.
    """
    if len(texto_peticao.strip()) < 100:
        return "Resumo não gerado: texto insuficiente para análise."

    # MOCK: versão inicial para testes sem Gemini
    return (
        "Trata-se de recurso interposto em razão de decisão desfavorável ao recorrente. "
        "No corpo da peça, são apresentados os fundamentos jurídicos, precedentes pertinentes "
        "e a exposição dos fatos que embasam o pedido. Ao final, requer-se a reforma da decisão recorrida, "
        "com base nos argumentos expostos."
    )
