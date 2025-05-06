import google.generativeai as genai

def gerar_resumo_gemini(texto: str) -> str:
    """
    Gera um resumo técnico com o modelo Gemini 2.5 Pro via Vertex AI.
    """
    genai.configure(
        api_key=None,
        transport="rest",
        client_options={"api_endpoint": "us-central1-aiplatform.googleapis.com"}
    )

    model = genai.GenerativeModel("gemini-2.5-pro-preview-05-06")

    response = model.generate_content(
        f"Resuma tecnicamente esta petição:\n{texto}",
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 1200
        }
    )

    return response.text.strip()
