from peticionador.modelos.estado_peticao import EstadoPeticao
from peticionador.agentes.agente_extrator import extrair_info_roberta
from peticionador.agentes.agente_gemini import verificar_extracao_gemini
from peticionador.agentes.agente_resumidor import gerar_resumo_tecnico
from peticionador.agentes.agente_estrategista import sugerir_teses
from peticionador.servicos.gerador_documento import gerar_peca_personalizada


def processar_peticao(
    texto_primeira_pagina: str,
    texto_completo: str,
    modelos_existentes: list[str],
    modelos_por_tipo: dict[str, str],
    modelo_padrao: str = ""
) -> dict:
    """
    Executa o pipeline completo com seleção automática do modelo conforme tipo de recurso.

    Parâmetros:
        texto_primeira_pagina (str): Primeira página da petição.
        texto_completo (str): Texto completo limpo.
        modelos_existentes (list): Lista de modelos reutilizáveis carregados.
        modelos_por_tipo (dict): Map. tipo_recurso → caminho do modelo textual.
        modelo_padrao (str): Caminho do modelo padrão, se tipo não for detectado.

    Retorna:
        dict: {
            "estado": EstadoPeticao,
            "arquivos": dict com caminhos .docx e .odt
        }
    """
    estado = EstadoPeticao()

    try:
        # 1. Extração inicial com RoBERTa
        dados_extraidos = extrair_info_roberta(texto_primeira_pagina)

        # 2. Validação com Gemini
        dados_validados = verificar_extracao_gemini(texto_primeira_pagina, dados_extraidos)
        estado.estrutura_base.update(dados_validados)

        # 3. Resumo técnico
        estado.resumo = gerar_resumo_tecnico(texto_completo)

        # 4. Teses jurídicas
        teses = sugerir_teses(texto_completo, modelos_existentes)
        estado.argumentos_reutilizaveis = teses["presentes"] + teses["sugeridas"]
        estado.modelos_usados = teses["presentes"]

        # 5. Escolha do modelo com base no tipo do recurso
        tipo_detectado = estado.estrutura_base.get("tipo_recurso", "Indeterminado")
        modelo_path = modelos_por_tipo.get(tipo_detectado, modelo_padrao)

        # 6. Geração da peça
        arquivos = gerar_peca_personalizada(estado, modelo_path)

    except Exception as e:
        print(f"[ERRO] Falha no processamento: {e}")
        raise

    return {
        "estado": estado,
        "arquivos": arquivos
    }
