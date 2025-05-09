from peticionador.servicos.integrador_gemini import ClienteGemini

def gerar_resumo_tecnico(texto: str) -> str:
    cliente = ClienteGemini()
    resumo = cliente.resumir(texto)
    return resumo or "[Resumo não disponível]"
