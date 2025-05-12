# src/peticionador/servicos/integrador_gemini.py
import logging
from typing import Optional, Literal
import google.generativeai as genai
from peticionador.utilitarios.configuracoes import GEMINI_API_KEY
from peticionador.modelos.interfaces.servico_resumidor import ServicoResumidor

genai.configure(api_key=GEMINI_API_KEY)
log = logging.getLogger(__name__)

# Definindo tipos para os nomes dos modelos
TipoModeloGemini = Literal[
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash"
    # Adicione outros modelos válidos se necessário
]

class ClienteGemini(ServicoResumidor):
    """
    Cliente para interagir com a API do Gemini, permitindo especificar o modelo.
    """
    DEFAULT_MODEL_FLASH: TipoModeloGemini = "models/gemini-1.5-flash"
    DEFAULT_MODEL_PRO: TipoModeloGemini = "models/gemini-1.5-pro"

    def __init__(self, model_name: Optional[TipoModeloGemini] = None):
        # Define o modelo a ser usado: o especificado, ou o flash como padrão
        self.target_model_name = model_name if model_name else self.DEFAULT_MODEL_FLASH
        self.chat = None # Inicializa como None

        try:
            # Tenta inicializar o modelo alvo diretamente
            log.info(f"Tentando inicializar modelo Gemini: {self.target_model_name}")
            self.chat = genai.GenerativeModel(self.target_model_name).start_chat()
            log.info(f"✅ Usando modelo Gemini: {self.target_model_name}")

        except Exception as erro_inicializacao:
            log.error(f"[ERRO CRÍTICO] Falha ao inicializar {self.target_model_name}: {erro_inicializacao}", exc_info=True)
            # Poderia tentar um fallback aqui se desejado, mas por enquanto falha
            self.chat = None # Garante que chat é None se falhar

    def resumir(self, texto: str) -> Optional[str]: # Mantendo o nome por compatibilidade
        """
        Envia um prompt para o modelo Gemini configurado.
        Embora chamado 'resumir', envia qualquer prompt fornecido no 'texto'.

        Parâmetros:
            texto (str): O prompt completo a ser enviado para a API.

        Retorna:
            str | None: Resposta do modelo, ou None em caso de falha.
        """
        if self.chat is None:
            log.error(f"[ERRO] Modelo {self.target_model_name} não carregado. Impossível enviar prompt.")
            return None

        try:
            log.info(f"[API Call] Enviando prompt para {self.target_model_name}...")
            # O 'texto' aqui é na verdade o PROMPT completo
            resposta = self.chat.send_message(texto)
            log.info(f"[API Response] Resposta recebida de {self.target_model_name}.")
            return resposta.text.strip()
        except Exception as erro_api:
            log.error(f"[ERRO GEMINI API] Modelo: {self.target_model_name} - Erro: {erro_api}", exc_info=True)
            # Retorna None para indicar falha na chamada
            return None