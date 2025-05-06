from peticionador.agentes.agente_estrategista import sugerir_teses


def test_sugestao_com_modelos_existentes():
    texto = "A peça trata de nulidade absoluta e violação à ampla defesa."
    modelos = ["nulidade processual", "prescrição penal"]

    saida = sugerir_teses(texto, modelos)

    assert "nulidade processual" in saida["presentes"]
    assert "violação à ampla defesa" in saida["sugeridas"]
    assert "prescrição penal" not in saida["sugeridas"]


def test_sugestao_sem_modelos_carregados():
    texto = "A petição sustenta prescrição penal e violação à ampla defesa."
    modelos = []

    saida = sugerir_teses(texto, modelos)

    assert sorted(saida["sugeridas"]) == sorted(["prescrição penal", "violação à ampla defesa"])
    assert saida["presentes"] == []
