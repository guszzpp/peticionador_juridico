import logging
import os
from typing import Dict, List, Optional # Garanta que todos os tipos usados estão aqui

# Imports dos módulos do projeto
from peticionador.modelos.estado_peticao import EstadoPeticao
from peticionador.servicos.extrator_pdf import extrair_texto_pdf_separado
from peticionador.agentes.agente_resumidor import gerar_resumo_tecnico
from peticionador.agentes.agente_extrator import extrair_dados_iniciais_gemini #, extrair_numero_processo_cnj # Mantenha cnj se usar
from peticionador.agentes.agente_estrategista import sugerir_teses
from peticionador.servicos.seletor_modelo import selecionar_modelo
from peticionador.servicos.gerador_documento import gerar_peca_personalizada

log = logging.getLogger(__name__)

# --- Definição CORRETA da Raiz do Projeto e Caminho de Saída ---
# __file__ aqui se refere a controlador_principal.py, que está em D:\...\src\peticionador\controladores\
# 1º dirname: D:\...\src\peticionador\controladores
# 2º dirname: D:\...\src\peticionador
# 3º dirname: D:\...\src
# 4º dirname: D:\Projetos\peticionador_juridico (RAIZ_PROJETO)
RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CAMINHO_SAIDA_ARQUIVOS = os.path.join(RAIZ_PROJETO, "arquivos_gerados")
# --- FIM DA DEFINIÇÃO CORRETA ---

def processar_peticao(
    caminho_arquivo_pdf: str,
    modelos_existentes: list[str],
    modelos_por_tipo: dict[str, str],
    modelo_padrao: str = "",
) -> dict:
    """
    Executa o pipeline completo de processamento da petição.
    """
    estado = EstadoPeticao()
    estado.nome_arquivo_pdf = os.path.basename(caminho_arquivo_pdf)
    arquivos_gerados = {} # Inicia vazio

    try:
        log.info(f"Iniciando processamento do PDF: {estado.nome_arquivo_pdf}")

        # 0. Extrair texto separado
        texto_pg1, texto_outras_pgs, texto_completo = extrair_texto_pdf_separado(caminho_arquivo_pdf)

        if texto_pg1 is None and texto_completo is None:
             raise ValueError("Falha crítica ao extrair qualquer texto do PDF.")
        texto_pg1_valido = texto_pg1 if texto_pg1 is not None else ""
        texto_completo_valido = texto_completo if texto_completo is not None else texto_pg1_valido

        # 1. Extração Inicial com Gemini
        log.info("Iniciando Etapa 1: Extração de dados iniciais com Gemini (Flash)...")
        dados_iniciais = extrair_dados_iniciais_gemini(texto_pg1_valido)
        estado.estrutura_base.update(dados_iniciais)
        log.info(f"Extração Gemini (Flash) concluída: {estado.estrutura_base}")

        # (Opcional: Se você for usar extrair_numero_processo_cnj, chame aqui)
        # if hasattr(estado, 'numero_processo'): # Verifica se o campo existe
        #     from peticionador.agentes.agente_extrator import extrair_numero_processo_cnj # Importa aqui para evitar dependencia se não usar
        #     estado.numero_processo = extrair_numero_processo_cnj(texto_pg1_valido)


        # 3. Resumo técnico com Gemini Flash
        log.info("Iniciando Etapa 3: Geração de resumo com Gemini (Flash)...")
        texto_para_resumo = texto_outras_pgs if texto_outras_pgs else texto_completo_valido
        if texto_para_resumo:
             estado.resumo = gerar_resumo_tecnico(texto_para_resumo)
             log.info(f"Resumo Gemini (Flash) gerado (tamanho: {len(estado.resumo)}).")
        else:
             log.warning("Nenhum texto disponível para resumo (páginas 2+).")
             estado.resumo = "[Resumo não gerado - Sem texto das páginas subsequentes]"

        # 4. Teses jurídicas com Gemini Flash
        log.info("Iniciando Etapa 4: Sugestão de teses com Gemini (Flash)...")
        if texto_completo_valido:
             teses = sugerir_teses(texto_completo_valido, modelos_existentes)
             estado.argumentos_reutilizaveis = teses.get("sugeridas", [])
             estado.modelos_usados = teses.get("presentes", [])
             log.info(f"Sugestão de teses (Gemini Flash): {len(estado.argumentos_reutilizaveis)} teses sugeridas.")
        else:
            log.warning("Nenhum texto completo disponível para sugestão de teses.")

        # 5. Escolha do modelo de documento
        tipo_detectado = estado.estrutura_base.get("tipo_recurso", "Indeterminado")
        modelo_path = selecionar_modelo(tipo_detectado, modelos_por_tipo, modelo_padrao)
        log.info(f"Modelo de documento selecionado ({tipo_detectado}): {modelo_path}")

        # 6. Geração da peça
        # Garante que o diretório de saída exista na raiz correta
        os.makedirs(CAMINHO_SAIDA_ARQUIVOS, exist_ok=True) # <-- MOVIDO PARA ANTES DA CHAMADA
        log.info(f"Usando diretório de saída para peças: {CAMINHO_SAIDA_ARQUIVOS}")
        # Passa o caminho absoluto para o diretório de saída
        arquivos_gerados_com_path_abs = gerar_peca_personalizada(estado, modelo_path, saida_dir=CAMINHO_SAIDA_ARQUIVOS)

        # Converter caminhos absolutos para relativos à RAIZ_PROJETO para armazenar em app.config
        arquivos_gerados_relativos = {}
        for tipo, caminho_abs in arquivos_gerados_com_path_abs.items():
            if caminho_abs: # Se o arquivo foi gerado com sucesso
                # Garante que o caminho_abs é realmente uma string antes de usar relpath
                if isinstance(caminho_abs, str):
                    arquivos_gerados_relativos[tipo] = os.path.relpath(caminho_abs, RAIZ_PROJETO)
                else:
                    log.error(f"Caminho absoluto para tipo '{tipo}' não é uma string: {caminho_abs}")
        arquivos_gerados = arquivos_gerados_relativos
        log.info(f"Arquivos gerados (caminhos relativos à raiz do projeto): {arquivos_gerados}")

    except Exception as e:
        log.error(f"Erro GERAL no processamento da petição: {e}", exc_info=True)
        estado.resumo = f"[ERRO NO PROCESSAMENTO: {str(e)}]" # Exibe a mensagem do erro
        # Retorna estado parcial e arquivos vazios em caso de erro grave
        # É importante que 'arquivos_gerados' seja um dict para a interface Flask
        return {"estado": estado, "arquivos": {}}

    log.info(f"Processamento do PDF {estado.nome_arquivo_pdf} concluído.")
    return {"estado": estado, "arquivos": arquivos_gerados}