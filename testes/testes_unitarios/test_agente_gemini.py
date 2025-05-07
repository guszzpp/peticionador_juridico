# testes/testes_unitarios/test_agente_gemini.py

from src.peticionador.agentes.agente_gemini import verificar_extracao_gemini

def test_verifica_tipo_recurso_por_palavra_chave():
    texto = "Trata-se de Agravo interposto contra decisão liminar."
    dados = {"recorrente": "Fulano", "tipo_recurso": "Indeterminado"}
    resultado = verificar_extracao_gemini(texto, dados)
    assert resultado["tipo_recurso"] == "Agravo"
    assert resultado["recorrente"] == "Fulano"

def test_verifica_nome_do_recorrente():
    texto = "Nome do Recorrente: João da Silva"
    dados = {"recorrente": "Desconhecido", "tipo_recurso": "Apelação"}
    resultado = verificar_extracao_gemini(texto, dados)
    assert resultado["recorrente"] == "João da Silva"
    assert resultado["tipo_recurso"] == "Apelação"

def test_retorna_valores_originais_quando_nao_encontra_nada():
    texto = "Texto irrelevante"
    dados = {"recorrente": "XYZ", "tipo_recurso": "Habeas Corpus"}
    resultado = verificar_extracao_gemini(texto, dados)
    assert resultado == dados
