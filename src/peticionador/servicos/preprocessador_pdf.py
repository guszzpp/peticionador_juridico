#  src/peticionador/servicos/preprocessador_pdf.py

import re


def limpar_texto_pdf(texto: str) -> str:
    """
    Remove elementos visuais indesejados do texto extraído de um PDF.

    Essa função elimina numeração de página, cabeçalhos repetitivos,
    marcas d'água e normaliza quebras de linha e espaçamentos.

    Parâmetros:
        texto (str): Texto bruto extraído do PDF.

    Retorna:
        str: Texto limpo e normalizado.
    """
    #  Remove linhas que indicam paginação
    texto = re.sub(r"(?i)p[aá]gina[s]?[:\s]*\d+(\s+de\s+\d+)?", "", texto)

    #  Remove cabeçalhos/rodapés genéricos
    texto = re.sub(r"(?i)poder judici[aá]rio.*\n", "", texto)
    texto = re.sub(r"(?i)tribunal de justiça.*\n", "", texto)

    #  Remove marcas d'água conhecidas (ex: "Provisório", "Minuta")
    texto = re.sub(r"(?i)provis[oó]rio|minuta|c[oó]pia", "", texto)

    #  Normaliza múltiplas quebras de linha
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    #  Remove espaços duplicados
    texto = re.sub(r"[ \t]+", " ", texto)

    return texto.strip()
