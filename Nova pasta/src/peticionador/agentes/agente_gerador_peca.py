# src/peticionador/agentes/agente_gerador_peca.py
import logging
from pathlib import Path
from typing import List, Dict, Optional
from peticionador.servicos.integrador_gemini import ClienteGemini

log = logging.getLogger(__name__)

def construir_minuta_com_ia(
    resumo_tecnico: str, # Este é o "ANÁLISE COMPLETA DO RECURSO ADVERSÁRIO"
    teses_selecionadas: List[str],
    modelo_base_path: Path,
    dados_processo: Dict[str, str],
    temperatura_ia: float = 0.2,
    max_tokens_ia: Optional[int] = 8000 # Aumentado um pouco para peças completas
) -> str:
    log.info(f"Iniciando construção da minuta com IA. Modelo base: {modelo_base_path.name}")
    log.info(f"Teses selecionadas pelo usuário para IA: {teses_selecionadas}")
    log.debug(f"Resumo técnico (análise do recurso) para IA: {resumo_tecnico[:300]}...") # Log truncado

    try:
        with open(modelo_base_path, "r", encoding="utf-8") as f:
            conteudo_modelo_base = f.read()
    except FileNotFoundError:
        log.error(f"Arquivo de modelo base não encontrado em: {modelo_base_path}")
        return "[ERRO INTERNO: Arquivo de modelo base não encontrado.]"
    except Exception as e:
        log.error(f"Erro ao ler arquivo de modelo base {modelo_base_path}: {e}")
        return f"[ERRO INTERNO: Falha ao ler modelo base - {e}]"

    teses_formatadas_prompt = ""
    if teses_selecionadas:
        teses_formatadas_prompt = "\n".join([f"- {tese.strip()}" for tese in teses_selecionadas])
    else:
        # Se não houver teses, o prompt precisa instruir a IA sobre o que fazer com a seção de argumentos.
        teses_formatadas_prompt = "Nenhuma tese específica foi selecionada pelo usuário para esta seção."

    # ----- ESTE É O PROMPT CORRIGIDO E MAIS DETALHADO -----
    prompt = f"""
Você é um Procurador de Justiça do Ministério Público do Estado de Goiás, um especialista experiente e altamente eficiente na elaboração de contrarrazões a Recursos Extraordinários e Especiais (RE/REsp), aderindo a um estilo formal, técnico, objetivo e conciso.

Sua tarefa é gerar o texto COMPLETO de uma peça de contrarrazões, utilizando um MODELO BASE e integrando informações específicas.

**1. MODELO BASE DA PEÇA (Use esta estrutura):**
--- INÍCIO MODELO BASE ---
{conteudo_modelo_base}
--- FIM MODELO BASE ---
(Observação: O `conteudo_modelo_base` é o texto extraído do arquivo .odt modelo, já em formato de texto puro com placeholders como {{{{NOME_DO_PLACEHOLDER}}}}.)

**2. INFORMAÇÕES DISPONÍVEIS PARA INTEGRAR NA PEÇA:**

    **A. ANÁLISE DO RECURSO ADVERSÁRIO (Use como CONTEXTO para criar o "Relatório da Peça"):**
        {resumo_tecnico}

    **B. TESES DE DEFESA (Selecionadas pelo usuário. Estas DEVEM ser desenvolvidas na peça. Se estiver indicado "Nenhuma tese específica foi selecionada...", então a seção de argumentação deve refletir isso de forma apropriada, como indicando que os fundamentos do acórdão recorrido são suficientes):**
        {teses_formatadas_prompt}

    **C. DADOS DO PROCESSO (Para preencher placeholders):**
        Número do Processo: {dados_processo.get('numero_processo', '{{NUM_PROCESSO}}')}
        Nome do Recorrente: {dados_processo.get('recorrente', '{{NOME_RECORRENTE}}')}
        Cidade: {dados_processo.get('CIDADE', 'Goiânia')}
        Data da Peça: {dados_processo.get('DATA_ATUAL', '{{DATA_ATUAL}}')}
        Promotor(a): {dados_processo.get('NOME_PROMOTOR', 'Promotor(a) de Justiça')}
        (Outros placeholders como {{{{NUMERO_CONTRARRAZOES}}}}, {{{{ANO_ATUAL}}}}, {{{{NOME_NUCLEO_OU_PROMOTORIA}}}}, {{{{NUM_PORTARIA}}}}, {{{{NUM_EVENTOS_ACORDAOS}}}}, {{{{TIPO_RECURSO_MAIUSCULO}}}}, {{{{SAUDACAO_TRIBUNAL_SUPERIOR}}}}, {{{{ARTIGO_FUNDAMENTO_RECURSO}}}} devem ser preenchidos com os dados correspondentes, se disponíveis nos DADOS DO PROCESSO, ou com valores genéricos apropriados, ou mantidos como placeholders se a informação não for fornecida.)

**3. INSTRUÇÕES DETALHADAS PARA GERAÇÃO DA PEÇA:**

    **Passo 1: Gerar o "Relatório da Peça" (para o placeholder `{{{{RESUMO_PARA_A_PECA}}}}` no MODELO BASE):**
        - Com base na "ANÁLISE DO RECURSO ADVERSÁRIO" (item 2.A), identifique: o nome do recorrente, os acórdãos/eventos recorridos e o fundamento legal principal do recurso interposto pelo recorrente (ex: art. 105, III, 'a', CF).
        - Redija UM ÚNICO PARÁGRAFO conciso e direto para o relatório da peça, com no máximo 2-3 frases, no seguinte estilo: "[Nome do Recorrente], nos autos em referência, irresignado(a) com os v. Acórdãos dos eventos n.º [Número dos Eventos], interpôs o presente Recurso [Extraordinário/Especial], com fundamento no [Artigo da CF/Lei invocado]."
        - ESTE PARÁGRAFO CONCISO SUBSTITUIRÁ EXATAMENTE O PLACEHOLDER `{{{{RESUMO_PARA_A_PECA}}}}` no MODELO BASE. 
        - IMPORTANTE: NÃO adicione a frase "É o sucinto relatório." ao final deste parágrafo que você está gerando, pois essa frase JÁ EXISTE no MODELO BASE, logo após o placeholder `{{{{RESUMO_PARA_A_PECA}}}}`.

    **Passo 2: Desenvolver as "Teses de Defesa Selecionadas" (para o placeholder `{{{{TESES_E_ARGUMENTOS}}}}` no MODELO BASE):**
        - Para CADA tese listada em "TESES DE DEFESA" (item 2.B), você DEVE redigir um ou mais parágrafos desenvolvendo o argumento jurídico completo e fundamentado.
        - Inicie a argumentação de cada tese de forma clara e distinta (ex: "No que tange à tese de [Nome da Tese]...", "Quanto à alegada [Nome da Tese]...").
        - Elabore o texto de forma dissertativa e argumentativa, conectando as ideias com fluidez. NÃO APRESENTE AS TESES COMO UMA LISTA DE TÓPICOS OU COM MARCADORES (COMO '*' OU '-').
        - Se em "TESES DE DEFESA" (item 2.B) constar "Nenhuma tese específica foi selecionada pelo usuário para esta seção.", então a seção `{{{{TESES_E_ARGUMENTOS}}}}` no MODELO BASE deve ser preenchida com um texto apropriado, como por exemplo: "O acórdão recorrido deve ser mantido por seus próprios e jurídicos fundamentos, os quais se mostram irrefutáveis e em consonância com a pacífica jurisprudência pátria." ou algo similar que indique a ausência de teses específicas a serem rebatidas.

    **Passo 3: Preencher Demais Placeholders e Finalizar:**
        - Substitua TODOS os demais placeholders no MODELO BASE (ex: `{{{{NUM_PROCESSO}}}}`, `{{{{NOME_RECORRENTE}}}}`, `{{{{NOME_PROMOTOR}}}}`, `{{{{TIPO_RECURSO_MAIUSCULO}}}}`, `{{{{SAUDACAO_TRIBUNAL_SUPERIOR}}}}`, etc.) usando os "DADOS DO PROCESSO" (item 2.C) ou inferindo do contexto (ex: se o recurso é REsp, a saudação é ao STJ). Se um dado não for fornecido, mantenha o placeholder ou use um valor genérico como "XXXX" ou "a ser preenchido".
        - Mantenha a estrutura geral, saudações, fechos e texto fixo do MODELO BASE.
        - A linguagem deve ser estritamente formal, técnica, objetiva e impessoal, no padrão do Ministério Público.
        - NÃO adicione informações ou argumentos que não derivem das teses selecionadas, da análise do recurso ou dos dados do processo.

**4. SAÍDA FINAL:**
Retorne APENAS o texto completo da peça processual finalizada, após todas as substituições e desenvolvimentos. Não inclua esta introdução, os delimitadores de seção (como --- INÍCIO MODELO BASE ---), comentários, explicações ou qualquer texto que não faça parte da peça em si.

PEÇA PROCESSUAL FINALIZADA:
"""
    # ----- FIM DO PROMPT CORRIGIDO -----

    cliente_ia = ClienteGemini(model_name=ClienteGemini.DEFAULT_MODEL_PRO) 
    log.info(f"Enviando prompt para IA com temperatura {temperatura_ia} e max_tokens {max_tokens_ia}")
    
    minuta_final = cliente_ia.gerar_conteudo(prompt, temperatura=temperatura_ia, max_tokens=max_tokens_ia)

    if minuta_final is None:
        log.error("Falha ao gerar minuta com IA. A resposta foi None.")
        return "[ERRO: A IA não conseguiu gerar a minuta. Tente novamente ou verifique os logs do servidor.]"
    if "[ERRO:" in minuta_final or "[CONTEÚDO BLOQUEADO PELA API:" in minuta_final or "[RESPOSTA INESPERADA OU VAZIA DA API GEMINI]" in minuta_final:
        log.error(f"IA retornou um erro ou conteúdo bloqueado: {minuta_final}")
        return f"[FALHA NA GERAÇÃO PELA IA. Detalhe: {minuta_final}]"

    log.info("Minuta gerada com IA com sucesso.")
    return minuta_final.strip()