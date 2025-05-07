import pytest
from src.peticionador.agentes import agente_resumidor

# Mock da função gerar_resumo_gemini
@pytest.fixture
def mock_resumidor(monkeypatch):
    def resumo_fake(texto: str) -> str:
        return "Resumo técnico gerado para o texto de entrada."
    
    monkeypatch.setattr("src.peticionador.agentes.agente_resumidor.gerar_resumo_gemini", resumo_fake)


def test_resumo_mockado_completo(mock_resumidor):
    texto = (
        "O recorrente foi condenado em primeira instância. Sustenta que houve nulidade no processo, "
        "ausência de fundamentação e afronta à ampla defesa. Ao final, requer a reforma da sentença."
    )
    resumo = agente_resumidor.gerar_resumo_tecnico(texto)
    assert isinstance(resumo, str)
    assert "Resumo técnico" in resumo


def test_resumo_texto_insuficiente(mock_resumidor):
    texto = "Requer reforma."
    resumo = agente_resumidor.gerar_resumo_tecnico(texto)
    assert isinstance(resumo, str)
    assert len(resumo) > 0
