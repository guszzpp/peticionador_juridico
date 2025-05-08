from abc import ABC, abstractmethod

class ServicoResumidor(ABC):
    @abstractmethod
    def resumir(self, texto: str) -> str:
        ...
