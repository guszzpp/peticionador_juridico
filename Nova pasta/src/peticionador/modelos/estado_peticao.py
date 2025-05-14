from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class EstadoPeticao:
    estrutura_base: Dict[str, Any] = field(default_factory=dict)
    resumo: str = ""
    argumentos_reutilizaveis: List[str] = field(default_factory=list)
    modelos_usados: List[str] = field(default_factory=list)
    nome_arquivo_pdf: str = ""
    tempo_processamento: float = 0.0
