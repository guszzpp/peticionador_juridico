import pytest
from peticionador.agentes.agente_resumidor_gemini_vertex import gerar_resumo_gemini

def test_resumo_gerado_gemini_vertex():
    texto = (
        "Trata-se de recurso interposto pelo Ministério Público do Estado de Goiás, "
        "com o objetivo de reformar decisão de absolvição sumária proferida em audiência de custódia. "
        "A defesa alega ausência de justa causa para a ação penal."
    )

    resumo = gerar_resumo_gemini(texto)
    assert isinstance(resumo, str)
    assert len(resumo.strip()) > 50
