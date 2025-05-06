from peticionador.agentes.agente_resumidor import gerar_resumo_tecnico


def test_resumo_mockado_completo():
    texto = (
        "O recorrente foi condenado em primeira instância. Sustenta que houve nulidade no processo, "
        "ausência de fundamentação e afronta à ampla defesa. Ao final, requer a reforma da sentença."
    )
    resumo = gerar_resumo_tecnico(texto)
    assert "recurso interposto" in resumo.lower()
    assert "fundamentos jurídicos" in resumo.lower()
    assert "requer-se a reforma" in resumo.lower()


def test_resumo_texto_insuficiente():
    texto = "Requer reforma."
    resumo = gerar_resumo_tecnico(texto)
    assert "insuficiente" in resumo.lower()
