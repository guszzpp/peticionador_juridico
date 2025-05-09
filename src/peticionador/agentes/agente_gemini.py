from peticionador.servicos.integrador_gemini import ClienteGemini

def verificar_extracao_gemini(texto: str, dados_extraidos: dict) -> dict:
    """
    Usa Gemini para validar ou complementar informações extraídas da petição.

    Parâmetros:
        texto (str): Texto base da petição (ex: primeira página).
        dados_extraidos (dict): Dados previamente extraídos por RoBERTa.

    Retorna:
        dict: Novo dicionário de dados, complementado ou corrigido.
    """
    cliente = ClienteGemini()

    # Prepare o prompt
    prompt = (
        "Você é um assistente jurídico. Com base no trecho abaixo, verifique e complemente "
        "as seguintes informações:\n\n"
        f"{texto}\n\n"
        f"Dados atuais extraídos:\n{dados_extraidos}\n\n"
        "Retorne apenas os dados relevantes no formato JSON:"
    )

    resposta = cliente.resumir(prompt)

    try:
        import json
        dados_corrigidos = json.loads(resposta)
        if isinstance(dados_corrigidos, dict):
            return dados_corrigidos
    except Exception as e:
        print(f"[ERRO PARSE GEMINI] {e} — resposta recebida:\n{resposta}")

    return dados_extraidos  # fallback: retorna os dados originais
