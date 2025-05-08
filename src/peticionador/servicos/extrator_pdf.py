import fitz  # PyMuPDF
import os
import re
from typing import Tuple, Dict, List, Optional
from pathlib import Path
from peticionador.servicos.preprocessador_pdf import limpar_texto_pdf


def extrair_texto_pdf(caminho_arquivo: str) -> Tuple[str, str]:
    """
    Extrai texto de um arquivo PDF usando PyMuPDF (fitz).
    
    Parâmetros:
        caminho_arquivo (str): Caminho para o arquivo PDF
        
    Retorna:
        Tuple[str, str]: (primeira_pagina, texto_completo)
    """
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
    
    try:
        # Abrir o documento
        documento = fitz.open(caminho_arquivo)
        
        if len(documento) == 0:
            raise ValueError("O PDF não contém páginas")
        
        # Extrair a primeira página
        primeira_pagina = documento[0].get_text()
        
        # Extrair o texto completo
        texto_completo = ""
        for pagina in documento:
            texto_completo += pagina.get_text() + "\n\n"
        
        # Fechar o documento
        documento.close()
        
        # Pré-processar para remover elementos indesejados
        primeira_pagina = limpar_texto_pdf(primeira_pagina)
        texto_completo = limpar_texto_pdf(texto_completo)
        
        return primeira_pagina, texto_completo
    
    except Exception as e:
        raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")


def extrair_metadados_pdf(caminho_arquivo: str) -> Dict:
    """
    Extrai metadados de um arquivo PDF.
    
    Parâmetros:
        caminho_arquivo (str): Caminho para o arquivo PDF
        
    Retorna:
        Dict: Dicionário com metadados do documento
    """
    try:
        documento = fitz.open(caminho_arquivo)
        metadados = documento.metadata
        documento.close()
        return metadados
    except Exception as e:
        return {"erro": str(e)}


def extrair_blocos_texto(caminho_arquivo: str, pagina_inicio: int = 0, pagina_fim: Optional[int] = None) -> List[Dict]:
    """
    Extrai blocos de texto estruturado, mantendo informações de posicionamento.
    Útil para análise de layouts específicos de documentos jurídicos.
    
    Parâmetros:
        caminho_arquivo (str): Caminho para o arquivo PDF
        pagina_inicio (int): Página inicial (0-indexed)
        pagina_fim (Optional[int]): Página final (inclusive), ou None para todas
        
    Retorna:
        List[Dict]: Lista de blocos de texto com posição e conteúdo
    """
    try:
        documento = fitz.open(caminho_arquivo)
        
        if pagina_fim is None:
            pagina_fim = len(documento) - 1
        
        blocos = []
        
        for num_pagina in range(pagina_inicio, min(pagina_fim + 1, len(documento))):
            pagina = documento[num_pagina]
            # dict_keys(['type', 'bbox', 'lines', 'spans'])
            blocks = pagina.get_text("dict")["blocks"]
            
            for bloco in blocks:
                if "lines" in bloco:
                    texto_bloco = ""
                    for linha in bloco["lines"]:
                        if "spans" in linha:
                            for span in linha["spans"]:
                                texto_bloco += span["text"] + " "
                            texto_bloco += "\n"
                    
                    if texto_bloco.strip():
                        blocos.append({
                            "pagina": num_pagina + 1,  # 1-indexed para humanos
                            "posicao": bloco["bbox"],  # [x0, y0, x1, y1]
                            "texto": texto_bloco.strip()
                        })
        
        documento.close()
        return blocos
    
    except Exception as e:
        raise Exception(f"Erro ao extrair blocos de texto: {str(e)}")


def detectar_cabecalho_rodape(blocos: List[Dict], tolerancia: float = 20.0) -> Dict[str, str]:
    """
    Detecta automaticamente cabeçalhos e rodapés recorrentes em um documento.
    
    Parâmetros:
        blocos (List[Dict]): Lista de blocos de texto obtida via extrair_blocos_texto
        tolerancia (float): Margem de tolerância em pontos para considerar como mesma posição
        
    Retorna:
        Dict[str, str]: Cabeçalho e rodapé detectados
    """
    # Agrupar blocos por posição Y similar
    grupos_superior = {}
    grupos_inferior = {}
    
    # Obter altura máxima das páginas (aproximada)
    max_y = max([bloco["posicao"][3] for bloco in blocos]) if blocos else 0
    
    for bloco in blocos:
        y_top = bloco["posicao"][1]  # y0 (topo)
        y_bottom = bloco["posicao"][3]  # y1 (base)
        
        # Candidato a cabeçalho (no topo da página)
        if y_top < 100:  # Primeiros 100 pontos da página
            key = round(y_top / tolerancia) * tolerancia
            if key not in grupos_superior:
                grupos_superior[key] = []
            grupos_superior[key].append(bloco["texto"])
        
        # Candidato a rodapé (na base da página)
        if max_y - y_bottom < 100:  # Últimos 100 pontos da página
            key = round(y_bottom / tolerancia) * tolerancia
            if key not in grupos_inferior:
                grupos_inferior[key] = []
            grupos_inferior[key].append(bloco["texto"])
    
    # Identificar o grupo mais frequente como cabeçalho/rodapé
    cabecalho = _texto_mais_frequente(grupos_superior)
    rodape = _texto_mais_frequente(grupos_inferior)
    
    return {
        "cabecalho": cabecalho,
        "rodape": rodape
    }


def _texto_mais_frequente(grupos: Dict[float, List[str]]) -> str:
    """Função auxiliar para encontrar o texto mais frequente em grupos posicionais."""
    # Contar ocorrências de cada texto
    contagem = {}
    for textos in grupos.values():
        for texto in textos:
            texto_norm = re.sub(r'\s+', ' ', texto).strip()
            if texto_norm:
                if texto_norm not in contagem:
                    contagem[texto_norm] = 0
                contagem[texto_norm] += 1
    
    # Encontrar o mais frequente
    texto_freq = max(contagem.items(), key=lambda x: x[1], default=(None, 0))
    return texto_freq[0] if texto_freq[0] else ""