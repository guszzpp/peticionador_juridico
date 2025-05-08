from typing import Optional
import google.generativeai as genai
from peticionador.utilitarios.configuracoes import GEMINI_API_KEY
from peticionador.modelos.interfaces.servico_resumidor import ServicoResumidor

genai.configure(api_key=GEMINI_API_KEY)


class ClienteGemini(ServicoResumidor):
    """
    Cliente para resumo de textos jurídicos utilizando a API do Gemini,
    com fallback automático entre modelos compatíveis.
    """

    def __init__(self):
        self.modelo_primario = "models/gemini-1.5-pro"
        self.modelo_secundario = "models/gemini-1.5-flash"

        try:
            self.chat = genai.GenerativeModel(self.modelo_primario).start_chat()
            print(f"✅ Usando modelo Gemini: {self.modelo_primario}")
        except Exception as erro_primario:
            print(f"[AVISO] Falha ao inicializar {self.modelo_primario}: {erro_primario}")
            print(f"🔁 Tentando modelo alternativo: {self.modelo_secundario}")
            try:
                self.chat = genai.GenerativeModel(self.modelo_secundario).start_chat()
                print(f"✅ Usando modelo Gemini: {self.modelo_secundario}")
            except Exception as erro_secundario:
                print(f"[ERRO CRÍTICO] Nenhum modelo Gemini disponível: {erro_secundario}")
                self.chat = None

    def resumir(self, texto: str) -> Optional[str]:
        """
        Gera um resumo técnico para um texto jurídico usando Gemini.

        Parâmetros:
            texto (str): Texto original a ser resumido.

        Retorna:
            str | None: Resumo gerado, ou None em caso de falha.
        """
        if self.chat is None:
            print("[ERRO] Nenhum modelo carregado para gerar o resumo.")
            return None

        try:
            resposta = self.chat.send_message(
                f"Resuma tecnicamente e em português o seguinte conteúdo jurídico:\n\n{texto}"
            )
            return resposta.text.strip()
        except Exception as erro:
            print(f"[ERRO GEMINI] {erro}")
            return None
