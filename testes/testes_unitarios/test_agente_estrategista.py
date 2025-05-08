from peticionador.agentes import agente_estrategista


def test_sugerir_teses_identifica_e_classifica():
    texto = (
        "O acusado alega nulidade processual e afronta ao princípio da ampla defesa. "
        "Sustenta ainda a ocorrência de prescrição retroativa."
    )
    modelos_existentes = ["nulidade processual"]

    resultado = agente_estrategista.sugerir_teses(texto, modelos_existentes)

    assert isinstance(resultado, dict)  #  nosec B101
    assert "sugeridas" in resultado  #  nosec B101
    assert "presentes" in resultado  #  nosec B101

    assert "nulidade processual" in resultado["presentes"]  #  nosec B101
    assert "prescrição penal" in resultado["sugeridas"]  #  nosec B101
    assert "violação à ampla defesa" in resultado["sugeridas"]  #  nosec B101
