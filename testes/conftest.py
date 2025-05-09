import sys
from pathlib import Path

# Adiciona 'src/' ao PYTHONPATH em todos os testes automaticamente
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
