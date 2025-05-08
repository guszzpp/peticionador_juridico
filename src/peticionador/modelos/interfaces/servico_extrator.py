from abc import ABC, abstractmethod

class ServicoExtrator(ABC):
    @abstractmethod
    def extrair(self, contexto: str, pergunta: str) -> str:
        ...
