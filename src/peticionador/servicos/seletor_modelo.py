#  src/peticionador/servicos/seletor_modelo.py


def selecionar_modelo(
    tipo_recurso: str, modelos_por_tipo: dict[str, str], modelo_padrao: str
) -> str:
    """
    Retorna o caminho do modelo apropriado conforme o tipo de recurso identificado.

    Parâmetros:
        tipo_recurso (str): Ex: "RE", "REsp", "Agravo"
        modelos_por_tipo (dict): Mapeamento tipo → caminho do modelo
        modelo_padrao (str): Caminho do modelo padrão

    Retorna:
        str: Caminho do modelo a ser utilizado
    """
    return modelos_por_tipo.get(tipo_recurso, modelo_padrao)
