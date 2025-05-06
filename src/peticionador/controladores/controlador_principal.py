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
    modelo_path: str
) -> dict:
    """
    Executa o pipeline completo: extrai, valida, resume, sugere teses e gera a peça.

    Parâmetros:
        texto_primeira_pagina (str): Primeira página extraída do PDF
        texto_completo (str): Texto integral (limpo) da petição
        modelos_existentes (list): Modelos reutilizáveis já conhecidos
        modelo_path (str): Caminho do modelo base de peça a ser preenchido

    Retorna:
        dict com:
            - estado: objeto EstadoPeticao atualizado
            - arquivos: dict com caminhos para .docx e .odt gerados
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

        # 4. Teses e argumentos
        teses = sugerir_teses(texto_completo, modelos_existentes)
        estado.argumentos_reutilizaveis = teses["presentes"] + teses["sugeridas"]
        estado.modelos_usados = teses["presentes"]

        # 5. Geração da peça com base no modelo selecionado
        arquivos = gerar_peca_personalizada(estado, modelo_path)

    except Exception as e:
        print(f"[ERRO] Falha no processamento: {e}")
        raise

    return {
        "estado": estado,
        "arquivos": arquivos
    }
