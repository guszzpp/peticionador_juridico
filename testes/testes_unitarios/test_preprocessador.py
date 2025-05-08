from peticionador.servicos.preprocessador_pdf import limpar_texto_pdf


def test_limpeza_simples():
    entrada = "Página 1 de 7\nPODER JUDICIÁRIO\nMinuta\n\nConteúdo da peça."
    esperado = "Conteúdo da peça."
    assert limpar_texto_pdf(entrada) == esperado  #  nosec B101
