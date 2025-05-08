import sys
from pathlib import Path
from google.generativeai import list_models
from pprint import pprint
import google.generativeai as genai
from peticionador.utilitarios.configuracoes import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

print("\n📦 Modelos disponíveis:")
for modelo in genai.list_models():
    print("🧠 Modelo:", modelo.name)

# Garante que a pasta 'src' seja reconhecida como raiz dos pacotes
src_dir = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(src_dir))

# Agora importamos a partir de 'peticionador', não mais de 'src.peticionador'
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

    assert resultado is not None, "Resumo retornado está vazio"
    assert isinstance(resultado, str), "Resumo não é uma string"
    assert len(resultado) > 20, "Resumo muito curto"
    print("\n📄 Resumo retornado:\n", resultado)
