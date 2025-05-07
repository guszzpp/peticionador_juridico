from peticionador.modelos.estado_peticao import EstadoPeticao

def test_estado_peticao_inicial():
    estado = EstadoPeticao()
    assert estado.estrutura_base == {}
    assert estado.resumo == ""
    assert estado.argumentos_reutilizaveis == []
    assert estado.modelos_usados == []
    assert estado.nome_arquivo_pdf == ""
    assert estado.tempo_processamento == 0.0
