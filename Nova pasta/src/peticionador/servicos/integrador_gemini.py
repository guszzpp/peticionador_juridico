# src/peticionador/servicos/integrador_gemini.py
import logging
from typing import Optional, Literal
import google.generativeai as genai
from peticionador.utilitarios.configuracoes import GEMINI_API_KEY
from peticionador.modelos.interfaces.servico_resumidor import ServicoResumidor # Mantenha se usado em outros lugares

genai.configure(api_key=GEMINI_API_KEY)
log = logging.getLogger(__name__)

TipoModeloGemini = Literal[
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash",
]

class ClienteGemini(ServicoResumidor):
    """
    Cliente para interagir com a API do Gemini, permitindo especificar o modelo e configurações de geração.
    """
    DEFAULT_MODEL_FLASH: TipoModeloGemini = "models/gemini-2.0-flash"
    DEFAULT_MODEL_PRO: TipoModeloGemini = "models/gemini-1.5-flash"

    def __init__(self, model_name: Optional[TipoModeloGemini] = None):
        self.target_model_name = model_name if model_name else self.DEFAULT_MODEL_FLASH
        self.model_instance = None
        self._inicializar_modelo()

    def _inicializar_modelo(self):
        """Tenta inicializar o modelo GenerativeModel."""
        if GEMINI_API_KEY == "__MISSING__":
            log.error("[ERRO CRÍTICO] GEMINI_API_KEY não configurada. Verifique suas variáveis de ambiente.")
            self.model_instance = None
            return

        try:
            log.info(f"Tentando inicializar modelo Gemini: {self.target_model_name}")
            self.model_instance = genai.GenerativeModel(self.target_model_name)
            log.info(f"✅ Modelo Gemini instanciado: {self.target_model_name}")
        except Exception as erro_inicializacao:
            log.error(f"[ERRO CRÍTICO] Falha ao instanciar {self.target_model_name}: {erro_inicializacao}", exc_info=True)
            self.model_instance = None

    def gerar_conteudo(self, prompt_texto: str, temperatura: Optional[float] = None, max_tokens: Optional[int] = None) -> Optional[str]:
        """
        Gera conteúdo usando o modelo configurado, com controle opcional de temperatura e max_tokens.

        Parâmetros:
            prompt_texto (str): O prompt completo a ser enviado para a API.
            temperatura (Optional[float]): Controla a aleatoriedade. Menor é mais determinístico. Ex: 0.2
            max_tokens (Optional[int]): Número máximo de tokens a serem gerados.

        Retorna:
            str | None: Resposta do modelo, ou None em caso de falha.
        """
        if self.model_instance is None:
            log.error(f"[ERRO] Modelo {self.target_model_name} não instanciado. Impossível enviar prompt.")
            if not GEMINI_API_KEY or GEMINI_API_KEY == "__MISSING__":
                 log.error("Verifique se GEMINI_API_KEY está configurada corretamente.")
            return "[ERRO: Modelo Gemini não pôde ser inicializado. Verifique a API Key e logs do servidor.]"


        generation_config_params = {}
        if temperatura is not None:
            generation_config_params["temperature"] = temperatura
        if max_tokens is not None:
            generation_config_params["max_output_tokens"] = max_tokens
        
        current_gen_config = None
        if generation_config_params:
            current_gen_config = genai.types.GenerationConfig(**generation_config_params)
            log.info(f"Usando configuration de geração: {generation_config_params}")

        try:
            log.info(f"[API Call] Enviando prompt para {self.target_model_name}...")
            resposta = self.model_instance.generate_content(
                prompt_texto,
                generation_config=current_gen_config
            )
            log.info(f"[API Response] Resposta recebida de {self.target_model_name}.")
            
            if resposta.parts:
                # Se houver várias partes, concatena. Normalmente é uma.
                full_text_response = "".join(part.text for part in resposta.parts if hasattr(part, 'text'))
                return full_text_response.strip()
            elif hasattr(resposta, 'text') and resposta.text: # Para modelos mais antigos ou respostas simples
                return resposta.text.strip()
            elif resposta.prompt_feedback and resposta.prompt_feedback.block_reason:
                 block_reason_message = getattr(resposta.prompt_feedback, 'block_reason_message', str(resposta.prompt_feedback.block_reason))
                 log.error(f"Geração bloqueada: {block_reason_message}")
                 return f"[CONTEÚDO BLOQUEADO PELA API: {block_reason_message}]"
            else:
                log.warning(f"Resposta da API Gemini não continha partes de texto utilizáveis ou foi bloqueada. Resposta: {resposta}")
                return "[RESPOSTA INESPERADA OU VAZIA DA API GEMINI]"

        except Exception as erro_api:
            log.error(f"[ERRO GEMINI API] Modelo: {self.target_model_name} - Erro: {erro_api}", exc_info=True)
            return f"[ERRO AO COMUNICAR COM API GEMINI: {erro_api}]"
        
    # Para um resumo, geralmente não se especifica temperatura, deixa o padrão do modelo.
    def resumir(self, texto: str) -> Optional[str]:
        # Se você quiser uma temperatura específica para resumos, pode passar aqui
        return self.gerar_conteudo(texto)