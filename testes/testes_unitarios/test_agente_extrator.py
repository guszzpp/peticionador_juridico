import pytest
from peticionador.agentes.agente_extrator import extrair_info_roberta


@pytest.mark.skip(reason="Teste de integração com modelo RoBERTa — requer GPU ou tempo.")
def test_roberta_extrai_dados():
    texto = "RECORRENTE: João da Silva\nTrata-se de Agravo Interno..."
    saida = extrair_info_roberta(texto)
    assert "João" in saida["recorrente"]
    assert "Agravo" in saida["tipo_recurso"]
