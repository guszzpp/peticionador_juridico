from src.peticionador.agentes import agente_estrategista

def test_sugerir_teses_identifica_e_classifica():
    texto = (
        "O acusado alega nulidade processual e afronta ao princípio da ampla defesa. "
        "Sustenta ainda a ocorrência de prescrição retroativa."
    )
    modelos_existentes = ["nulidade processual"]

    resultado = agente_estrategista.sugerir_teses(texto, modelos_existentes)

    assert isinstance(resultado, dict)
    assert "sugeridas" in resultado
    assert "presentes" in resultado

    assert "nulidade processual" in resultado["presentes"]
    assert "prescrição penal" in resultado["sugeridas"]
    assert "violação à ampla defesa" in resultado["sugeridas"]
