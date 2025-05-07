# src/peticionador/agentes/agente_resumidor.py

from src.peticionador.servicos.resumidor_gemini import gerar_resumo_gemini

def gerar_resumo_tecnico(texto: str) -> str:
    """
    Gera um resumo técnico da petição com o agente oficial de IA Gemini.

    :param texto: Texto da petição.
    :return: Resumo técnico em linguagem formal.
    """
    return gerar_resumo_gemini(texto)
