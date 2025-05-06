# src/peticionador/agentes/agente_extrator.py

from typing import Dict
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from functools import lru_cache


@lru_cache(maxsize=1)
def carregar_pipeline_ner():
    """
    Carrega e retorna o pipeline de NER com RoBERTa para textos jurídicos.
    Usa cache para evitar recarregamento.
    """
    modelo_nome = "pierreguillou/ner-bert-base-cased-pt-lener-br"  # substituível por outro RoBERTa
    tokenizer = AutoTokenizer.from_pretrained(modelo_nome)
    modelo = AutoModelForTokenClassification.from_pretrained(modelo_nome)
    return pipeline("ner", model=modelo, tokenizer=tokenizer, aggregation_strategy="simple")


def extrair_info_roberta(texto_pagina: str) -> Dict[str, str]:
    """
    Aplica o modelo RoBERTa de NER para extrair informações da primeira página.

    Parâmetros:
        texto_pagina (str): Texto da primeira página da petição.

    Retorna:
        dict: Dicionário com tipo de recurso e nome do(s) recorrente(s).
    """
    ner = carregar_pipeline_ner()
    entidades = ner(texto_pagina)

    nome = None
    tipo_recurso = None

    for entidade in entidades:
        label = entidade["entity_group"].upper()
        valor = entidade["word"]

        if not nome and "PESSOA" in label:
            nome = valor.strip()

        if not tipo_recurso and any(term in valor.lower() for term in ["agravo", "apelação", "mandado"]):
            tipo_recurso = valor.strip()

    return {
        "recorrente": nome or "Nome não localizado",
        "tipo_recurso": tipo_recurso or "Recurso Indeterminado"
    }
