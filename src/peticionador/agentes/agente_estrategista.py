#  src/peticionador/agentes/agente_estrategista.py

from typing import Dict, List


def sugerir_teses(
    texto_peticao: str, modelos_existentes: List[str]
) -> Dict[str, List[str]]:
    """
    Sugere teses defensivas com base no conteúdo da petição.

    Parâmetros:
        texto_peticao (str): Texto integral da petição (exceto a 1ª página).
        modelos_existentes (list): Lista de nomes de modelos já carregados no sistema.

    Retorna:
        dict: {
            "sugeridas": [teses novas],
            "presentes": [teses já existentes]
        }
    """
    #  MOCK simples baseado em palavras-chave
    teses_identificadas = []

    if "nulidade" in texto_peticao.lower():
        teses_identificadas.append("nulidade processual")

    if "prescrição" in texto_peticao.lower():
        teses_identificadas.append("prescrição penal")

    if "ampla defesa" in texto_peticao.lower():
        teses_identificadas.append("violação à ampla defesa")

    presentes = [t for t in teses_identificadas if t in modelos_existentes]
    novas = [t for t in teses_identificadas if t not in presentes]

    return {"presentes": presentes, "sugeridas": novas}
