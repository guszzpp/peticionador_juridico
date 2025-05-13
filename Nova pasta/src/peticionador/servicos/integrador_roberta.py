from transformers import pipeline
from typing import Optional

class ExtratorRoBERTa:
    def __init__(self, modelo: str = "pierreguillou/roberta-base-legal-squad-v1"):
        self.pipeline = pipeline("question-answering", model=modelo, tokenizer=modelo)

    def extrair(self, contexto: str, pergunta: str) -> Optional[str]:
        resposta = self.pipeline(question=pergunta, context=contexto)
        return resposta.get("answer", None)
