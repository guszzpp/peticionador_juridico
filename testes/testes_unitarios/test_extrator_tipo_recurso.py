import pytest
from peticionador.agentes.agente_extrator import extrair_info_roberta


@pytest.mark.parametrize(
    "descricao,texto,recorrente_esperado,tipo_esperado",
    [
        (
            "REsp com menção explícita",
            "RECORRENTE: Maria da Silva\nRecurso Especial interposto...",
            "Maria da Silva",
            "REsp"
        ),
        (
            "RE com menção genérica",
            "RECORRENTE: João Pedro\nRecurso extraordinário contra acórdão...",
            "João Pedro",
            "RE"
        ),
        (
            "Agravo identificado",
            "RECORRENTE: Fulano\nTrata-se de agravo interno contra decisão...",
            "Fulano",
            "Agravo"
        ),
        (
            "Texto indefinido",
            "O MP interpõe recurso constitucional sem nomear o recorrente...",
            "Desconhecido",
            "Indeterminado"
        ),
    ]
)
def test_extrair_info_roberta(descricao, texto, recorrente_esperado, tipo_esperado):
    resultado = extrair_info_roberta(texto)
    assert resultado["recorrente"] == recorrente_esperado, f"[{descricao}] Nome incorreto"
    assert resultado["tipo_recurso"] == tipo_esperado, f"[{descricao}] Tipo incorreto"
