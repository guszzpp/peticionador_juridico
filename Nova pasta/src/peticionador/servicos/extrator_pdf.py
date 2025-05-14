# src/peticionador/servicos/extrator_pdf.py
import fitz  # PyMuPDF
import os
import re
from typing import Tuple, Dict, List, Optional
from pathlib import Path
from peticionador.servicos.preprocessador_pdf import limpar_texto_pdf
import logging

log = logging.getLogger(__name__)

def extrair_texto_pdf_separado(caminho_arquivo: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extrai texto de um arquivo PDF, separando a primeira página do restante.

    Parâmetros:
        caminho_arquivo (str): Caminho para o arquivo PDF

    Retorna:
        Tuple[Optional[str], Optional[str], Optional[str]]:
            (texto_primeira_pagina, texto_demais_paginas, texto_completo)
            Retorna None para uma parte se ela não existir ou ocorrer erro.
    """
    if not os.path.exists(caminho_arquivo):
        log.error(f"Arquivo PDF não encontrado: {caminho_arquivo}")
        return None, None, None

    texto_primeira_pagina: Optional[str] = None
    texto_demais_paginas: str = ""
    texto_completo: str = ""

    try:
        documento = fitz.open(caminho_arquivo)
        num_paginas = len(documento)
        log.info(f"Abrindo PDF: {caminho_arquivo} ({num_paginas} páginas)")

        if num_paginas == 0:
            log.warning("PDF não contém páginas.")
            documento.close()
            return None, None, None

        # Extrair e limpar primeira página
        try:
            primeira_pagina_raw = documento[0].get_text()
            texto_primeira_pagina = limpar_texto_pdf(primeira_pagina_raw)
            texto_completo += texto_primeira_pagina + "\n\n" # Adiciona ao completo
            log.info("Texto da primeira página extraído e limpo.")
        except Exception as e_pg1:
            log.error(f"Erro ao processar primeira página: {e_pg1}", exc_info=True)
            # Continua para tentar extrair o resto

        # Extrair e limpar demais páginas (se existirem)
        if num_paginas > 1:
            log.info("Extraindo texto das demais páginas...")
            for i in range(1, num_paginas):
                try:
                    pagina_raw = documento[i].get_text()
                    texto_limpo = limpar_texto_pdf(pagina_raw)
                    texto_demais_paginas += texto_limpo + "\n\n"
                    texto_completo += texto_limpo + "\n\n" # Adiciona ao completo
                except Exception as e_pg_demais:
                     log.error(f"Erro ao processar página {i+1}: {e_pg_demais}", exc_info=True)
            log.info("Texto das demais páginas extraído e limpo.")
        else:
            log.info("PDF possui apenas uma página.")
            texto_demais_paginas = None # Explicitamente None se não há outras páginas


        documento.close()

        # Limpeza final do texto completo
        texto_completo = texto_completo.strip()
        if texto_demais_paginas is not None:
             texto_demais_paginas = texto_demais_paginas.strip()


        return texto_primeira_pagina, texto_demais_paginas, texto_completo

    except Exception as e:
        log.error(f"Erro CRÍTICO ao extrair texto do PDF: {e}", exc_info=True)
        if 'documento' in locals() and documento:
            documento.close() # Garante fechar o documento
        return None, None, None

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