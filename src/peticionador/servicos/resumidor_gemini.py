# src/peticionador/servicos/resumidor_gemini.py

from typing import Any
from google.generativeai import GenerativeModel, configure
import os

configure(api_key=os.getenv("GOOGLE_API_KEY"))

modelo = GenerativeModel("gemini-pro")

def gerar_resumo_gemini(texto: str) -> str:
    """
    Resume um texto jurídico com base no modelo Gemini da Google.

    Parâmetros:
        texto (str): Texto original da petição ou decisão.

    Retorna:
        str: Resumo técnico gerado pelo modelo.
    """
    prompt = (
        "Resuma tecnicamente o seguinte trecho de uma petição ou decisão judicial. "
        "Mantenha o foco nos pedidos, fundamentos e argumentos jurídicos, sem floreios.\n\n"
        f"{texto}"
    )
    resposta = modelo.generate_content(prompt)
    return resposta.text.strip()
