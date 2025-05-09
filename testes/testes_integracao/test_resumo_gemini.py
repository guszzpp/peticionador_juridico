import sys
from pathlib import Path
import pytest
import google.generativeai as genai
from peticionador.utilitarios.configuracoes import GEMINI_API_KEY

# Configura a API key
genai.configure(api_key=GEMINI_API_KEY)

# Adiciona src ao PYTHONPATH
src_dir = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(src_dir))

from peticionador.modelos.interfaces.servico_resumidor import ServicoResumidor
from peticionador.servicos.integrador_gemini import ClienteGemini

def testar_resumo_com_gemini():
    """Testa se o cliente Gemini retorna um resumo válido da entrada."""
    resumidor: ServicoResumidor = ClienteGemini()
    entrada = (
        "O Ministério Público tem papel essencial na fiscalização das parcerias "
        "com organizações da sociedade civil, assegurando a integridade do gasto público. "
        "A atuação preventiva e corretiva é prevista na Constituição Federal, em seu artigo 129."
    )

    resultado = resumidor.resumir(entrada)

    if resultado is None:
        pytest.skip("Quota do Gemini excedida — teste pulado")

    assert isinstance(resultado, str), "Resumo não é uma string"
    assert len(resultado.strip()) > 20, "Resumo muito curto"
    print("\n📄 Resumo retornado:\n", resultado)
