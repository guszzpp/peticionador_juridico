from peticionador.modelos.estado_peticao import EstadoPeticao


def test_estado_peticao_inicial():
    estado = EstadoPeticao()
    assert estado.estrutura_base == {}  #  nosec B101
    assert estado.resumo == ""  #  nosec B101
    assert estado.argumentos_reutilizaveis == []  #  nosec B101
    assert estado.modelos_usados == []  #  nosec B101
    assert estado.nome_arquivo_pdf == ""  #  nosec B101
    assert estado.tempo_processamento == 0.0  #  nosec B101
