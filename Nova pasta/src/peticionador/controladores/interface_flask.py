# src/peticionador/controladores/interface_flask.py

import os
import shutil
from datetime import datetime
from pathlib import Path
import uuid
import logging # Adicionado para logging
from flask import (
    Flask, render_template, request, jsonify, flash,
    send_from_directory, current_app
)
from odf.opendocument import OpenDocumentText
from odf.text import P
from werkzeug.utils import secure_filename
from typing import Set, Dict
from docx.shared import Pt
from odf import text as odf_text_module, teletype
from odf.opendocument import load as load_odt_file

# Importações dos seus módulos
from peticionador.controladores.controlador_principal import processar_peticao
from peticionador.agentes.agente_gerador_peca import construir_minuta_com_ia

# --- Constantes de Caminho e Configuração ---
RAIZ_FLASK_APP = Path(__file__).resolve().parents[3]
RAIZ_PROJETO = RAIZ_FLASK_APP # Assumindo que são o mesmo

PASTA_MODELOS_BASE = RAIZ_PROJETO / "src" / "peticionador" / "modelos"
PASTA_PECAS_USUARIO = PASTA_MODELOS_BASE / "pecas_completas"
PASTA_TESES_USUARIO = PASTA_MODELOS_BASE / "teses_avulsas"
PASTA_MINUTAS_FINAIS_IA = RAIZ_PROJETO/ "arquivos_gerados"
PASTA_MINUTAS_FINAIS_IA.mkdir(parents=True, exist_ok=True)

# Garante que as pastas de usuário existam
PASTA_PECAS_USUARIO.mkdir(parents=True, exist_ok=True)
PASTA_TESES_USUARIO.mkdir(parents=True, exist_ok=True)

# Modelo Unificado
NOME_ARQUIVO_MODELO_TXT_UNIFICADO = "modelo.txt"
CAMINHO_ARQUIVO_MODELO_TXT_UNIFICADO_COMPLETO = PASTA_MODELOS_BASE / NOME_ARQUIVO_MODELO_TXT_UNIFICADO

CAMINHO_MODELOS: Dict[str, Path] = {
    "RE": CAMINHO_ARQUIVO_MODELO_TXT_UNIFICADO_COMPLETO,
    "REsp": CAMINHO_ARQUIVO_MODELO_TXT_UNIFICADO_COMPLETO,
    "Agravo": CAMINHO_ARQUIVO_MODELO_TXT_UNIFICADO_COMPLETO,
}
MODELO_PADRAO = str(CAMINHO_ARQUIVO_MODELO_TXT_UNIFICADO_COMPLETO) # Convertido para string

MODELOS_SISTEMA_NOMES = [NOME_ARQUIVO_MODELO_TXT_UNIFICADO]

# Outras Constantes
UPLOAD_FOLDER = RAIZ_PROJETO / "arquivos_upload"
EXTENSOES_PERMITIDAS_PDF = {"pdf"}
EXTENSOES_PERMITIDAS_MODELO_UPLOAD = {".txt", ".odt"}
TESES_DISPONIVEIS = []

# --- Inicialização da Aplicação Flask ---
def configurar_app() -> Flask:
    pasta_atual = Path(__file__).parent
    app_instance = Flask(__name__,
                         template_folder=pasta_atual / "templates",
                         static_folder=pasta_atual / "static")
    app_instance.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "padrao_seguro_para_desenvolvimento_trocar")
    app_instance.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app_instance.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app_instance.config["JSON_AS_ASCII"] = False
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    if not app_instance.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if not app_instance.logger.handlers: # Evita adicionar handlers duplicados
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(module)s[%(lineno)d]: %(message)s'
            ))
            app_instance.logger.addHandler(stream_handler)
        app_instance.logger.setLevel(logging.INFO)
        app_instance.logger.info('Logging configurado para produção/standalone.')
    else:
        app_instance.logger.setLevel(logging.DEBUG) # Debug level para desenvolvimento Flask
        app_instance.logger.info('Logging configurado para desenvolvimento Flask (debug=True).')
    
    app_instance.logger.info("Aplicação Flask configurada.")
    return app_instance

app = configurar_app()
app.logger.info("Instância da aplicação Flask criada.")


# --- Funções Auxiliares ---
def extensao_permitida_geral(nome_arquivo: str, extensoes_validas: Set[str]) -> bool:
    return '.' in nome_arquivo and \
           nome_arquivo.rsplit('.', 1)[1].lower() in extensoes_validas

def extrair_texto_de_arquivo(caminho_arquivo_upload: Path) -> str:
    extensao = caminho_arquivo_upload.suffix.lower()
    texto_extraido = ""
    logger = app.logger # Usar o logger do app Flask
    logger.info(f"Tentando extrair texto de: {caminho_arquivo_upload} (extensão: {extensao})")

    if extensao == ".txt":
        try:
            with open(caminho_arquivo_upload, 'r', encoding='utf-8') as f:
                texto_extraido = f.read()
        except Exception as e:
            logger.error(f"Erro ao ler arquivo .txt '{caminho_arquivo_upload.name}': {e}", exc_info=True)
            raise ValueError(f"Erro ao ler o arquivo .txt: {e}")
    elif extensao == ".odt":
        try:                       
            doc = load_odt_file(str(caminho_arquivo_upload))
            all_paras = doc.getElementsByType(odf_text_module.P)
            paragrafos_texto = [teletype.extractText(para).strip() for para in all_paras]
            texto_extraido = "\n\n".join(filter(None, paragrafos_texto)) 
            logger.info(f"Texto extraído de .odt (tamanho: {len(texto_extraido)}).")
        except ImportError:
            logger.error("Biblioteca odfpy não instalada. Necessária para extrair de .odt")
            raise ValueError("Erro ao processar .odt: dependência odfpy ausente no servidor.")
        except Exception as e:
            logger.error(f"Erro ao extrair texto de .odt '{caminho_arquivo_upload.name}': {e}", exc_info=True)
            raise ValueError(f"Erro ao converter o arquivo .odt para texto: {e}")
    else:
        raise ValueError(f"Tipo de arquivo não suportado para extração de texto: {extensao}. Use .txt ou .odt.")
    
    return texto_extraido.strip()


# --- Rotas ---
@app.route('/')
def index():
    app.logger.info(f"Acessando rota / (index)")
    todas_as_teses_para_index = []
    # Teses Predefinidas (agora é [])
    for idx, texto_tese in enumerate(TESES_DISPONIVEIS):
        todas_as_teses_para_index.append({
            "id": f"tese_predefinida_sistema_{idx}", # ID mais específico
            "nome_exibicao": texto_tese,
            "conteudo_completo": texto_tese
        })
    # Teses Salvas pelo Usuário
    if PASTA_TESES_USUARIO.exists():
        for nome_arquivo_tese in os.listdir(PASTA_TESES_USUARIO):
            if nome_arquivo_tese.endswith(".txt"): # A IA usa os .txt
                caminho_tese_txt = PASTA_TESES_USUARIO / nome_arquivo_tese
                conteudo_tese_arquivo = ""
                try:
                    with open(caminho_tese_txt, "r", encoding="utf-8") as f_tese:
                        conteudo_tese_arquivo = f_tese.read().strip()
                except Exception as e:
                    app.logger.error(f"Erro ao ler tese para index '{nome_arquivo_tese}': {e}")
                    continue
                
                nome_exibicao = nome_arquivo_tese[:-4].replace('_', ' ').capitalize()
                if not conteudo_tese_arquivo: continue # Pula teses vazias

                todas_as_teses_para_index.append({
                    "id": nome_arquivo_tese, 
                    "nome_exibicao": nome_exibicao,
                    "conteudo_completo": conteudo_tese_arquivo
                })
    todas_as_teses_para_index.sort(key=lambda t: t['nome_exibicao'])
    app.logger.debug(f"Teses para botões na index: {len(todas_as_teses_para_index)}")
    return render_template("index.html", TESES_PARA_BOTOES=todas_as_teses_para_index, title="AutoLex")


@app.route('/processar', methods=["POST"])
def processar():
    logger = app.logger
    logger.info("Requisição recebida em /processar")
    if "arquivo" not in request.files:
        logger.warning("Nenhum arquivo enviado em /processar")
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    arquivo = request.files["arquivo"]
    if not arquivo or not arquivo.filename:
        logger.warning("Arquivo enviado sem nome em /processar")
        return jsonify({"erro": "Arquivo sem nome"}), 400

    if not extensao_permitida_geral(arquivo.filename, EXTENSOES_PERMITIDAS_PDF):
        logger.warning(f"Extensão não permitida para {arquivo.filename} em /processar")
        return jsonify({"erro": "Extensão de arquivo não permitida. Apenas PDF."}), 400

    nome_seguro = secure_filename(arquivo.filename)
    caminho_arquivo = app.config["UPLOAD_FOLDER"] / nome_seguro
    try:
        arquivo.save(caminho_arquivo)
        logger.info(f"Arquivo '{nome_seguro}' salvo em {caminho_arquivo}")
    except Exception as e_save:
        logger.error(f"Erro ao salvar arquivo de upload '{nome_seguro}': {e_save}", exc_info=True)
        return jsonify({"erro": "Erro interno ao salvar arquivo de upload."}), 500

    try:
        modelos_por_tipo_str = {k: str(v) for k, v in CAMINHO_MODELOS.items()}
        # MODELO_PADRAO já é string pela definição global
        
        resultado = processar_peticao(
            caminho_arquivo_pdf=str(caminho_arquivo),
            modelos_existentes=TESES_DISPONIVEIS,
            modelos_por_tipo=modelos_por_tipo_str,
            modelo_padrao=MODELO_PADRAO # Já é string
        )
        
        estado = resultado.get("estado")
        
        if not estado:
            logger.error("Controlador 'processar_peticao' não retornou estado.")
            raise ValueError("Controlador não retornou estado.")

        # Armazena os dados para uso posterior (download, gerar peça com IA)
        app.config["ULTIMO_PROCESSAMENTO"] = {
            "estado": {
                "resumo": estado.resumo,
                "argumentos": estado.argumentos_reutilizaveis,
                "recorrente": estado.estrutura_base.get("recorrente", "Não identificado"),
                "tipo_recurso": estado.estrutura_base.get("tipo_recurso", "Indeterminado"),
                "numero_processo": estado.estrutura_base.get("numero_processo"),
                "num_eventos": estado.estrutura_base.get("num_eventos"),
                "artigo_fundamento": estado.estrutura_base.get("artigo_fundamento")
            },
        }
        logger.info(f"Processamento do PDF '{nome_seguro}' concluído com sucesso.")
        
        return jsonify({
            "resumo": estado.resumo,
            "argumentos": estado.argumentos_reutilizaveis,
            "recorrente": estado.estrutura_base.get("recorrente", "Não identificado"),
            "tipo_recurso": estado.estrutura_base.get("tipo_recurso", "Indeterminado"),
            "numero_processo": estado.estrutura_base.get("numero_processo"),
        })
    except ValueError as ve:
        logger.error(f"Erro de valor durante o processamento da petição '{nome_seguro}': {ve}", exc_info=True)
        return jsonify({"erro": f"Erro de processamento de dados: {str(ve)}"}), 400
    except Exception as erro:
        logger.exception(f"Erro geral inesperado ao processar a petição '{nome_seguro}'.")
        return jsonify({"erro": f"Erro inesperado no servidor durante o processamento: {str(erro)}"}), 500

@app.route("/download/<tipo_arquivo>")
def download(tipo_arquivo: str):
    logger = app.logger
    logger.info(f"Requisição de download para tipo: {tipo_arquivo}")
    ultima_execucao = app.config.get("ULTIMO_PROCESSAMENTO")

    if not ultima_execucao:
        logger.warning("Tentativa de download sem processamento recente.")
        flash("Nenhum processamento recente encontrado para download.", "warning")
        return "Erro: Nenhum processamento recente encontrado.", 404

    arquivos_gerados = ultima_execucao.get("arquivos", {})
    if tipo_arquivo not in arquivos_gerados:
        logger.warning(f"Tipo de arquivo '{tipo_arquivo}' não disponível para download.")
        flash(f"Tipo de arquivo '{tipo_arquivo}' não está disponível para download.", "warning")
        return f"Erro: Tipo {tipo_arquivo} não disponível.", 404

    caminho_relativo = arquivos_gerados[tipo_arquivo]
    caminho_absoluto = RAIZ_PROJETO / caminho_relativo

    # Tenta substituir por .txt se existir e for mais representativo
    caminho_txt = caminho_absoluto.with_suffix('.txt')
    if caminho_txt.exists() and tipo_arquivo == "minuta_gerada":
        logger.info(f"Preferindo arquivo .txt da IA para download: {caminho_txt.name}")
        caminho_absoluto = caminho_txt

    if not caminho_absoluto.exists():
        logger.error(f"Arquivo para download não encontrado: {caminho_absoluto}")
        flash(f"Erro: Arquivo '{caminho_absoluto.name}' não encontrado no servidor.", "danger")
        return f"Erro: Arquivo '{caminho_absoluto.name}' não encontrado.", 404

    logger.info(f"Enviando arquivo para download: {caminho_absoluto}")
    return send_from_directory(
        directory=caminho_absoluto.parent,
        path=caminho_absoluto.name,
        as_attachment=True
    )


@app.route("/obter_conteudo_modelo", methods=["GET"])
def obter_conteudo_modelo_endpoint():
    # ... (código da rota como na sua última versão, está bom) ...
    logger = app.logger
    nome_arquivo_req = request.args.get("nome_arquivo")
    tipo = request.args.get("tipo")

    if not nome_arquivo_req or not tipo:
        logger.warning("Requisição para /obter_conteudo_modelo sem nome_arquivo ou tipo.")
        return jsonify({"erro": "Nome do arquivo e tipo são obrigatórios."}), 400

    logger.info(f"Requisitado conteúdo para: {nome_arquivo_req}, tipo: {tipo}")
    caminho_arquivo_txt_para_ler = None

    if tipo == 'peca':
        if nome_arquivo_req in MODELOS_SISTEMA_NOMES: # É um .txt de sistema
            caminho_arquivo_txt_para_ler = PASTA_MODELOS_BASE / nome_arquivo_req
        else: # Peça de usuário, deve ser .txt
            caminho_arquivo_txt_para_ler = PASTA_PECAS_USUARIO / nome_arquivo_req
    elif tipo == 'tese':
        # Teses predefinidas não são buscadas aqui, frontend passa o conteúdo.
        # Esta rota é para teses salvas pelo usuário, que são .txt
        caminho_arquivo_txt_para_ler = PASTA_TESES_USUARIO / nome_arquivo_req
    else:
        logger.warning(f"Tipo de modelo inválido '{tipo}' em /obter_conteudo_modelo.")
        return jsonify({"erro": "Tipo de modelo inválido."}), 400

    if not caminho_arquivo_txt_para_ler or not caminho_arquivo_txt_para_ler.exists():
         # Tenta fallback para .odt -> extrair -> salvar .txt -> ler .txt (se o original era .odt)
        nome_base_original = Path(nome_arquivo_req).stem
        pasta_original = PASTA_PECAS_USUARIO if tipo == 'peca' else PASTA_TESES_USUARIO
        caminho_odt_original = pasta_original / f"{nome_base_original}.odt"

        if caminho_odt_original.exists():
            logger.warning(f"Arquivo .txt '{caminho_arquivo_txt_para_ler}' não encontrado, mas .odt '{caminho_odt_original}' existe. Tentando extrair.")
            try:
                conteudo_extraido = extrair_texto_de_arquivo(caminho_odt_original)
                # Salva o .txt extraído para futuras requisições
                with open(caminho_arquivo_txt_para_ler, "w", encoding="utf-8") as f_txt_novo:
                    f_txt_novo.write(conteudo_extraido)
                logger.info(f"Conteúdo extraído de '{caminho_odt_original.name}' e salvo em '{caminho_arquivo_txt_para_ler.name}'.")
                return jsonify({"conteudo": conteudo_extraido})
            except Exception as e_extract:
                logger.error(f"Falha ao extrair/salvar .txt de '{caminho_odt_original.name}' sob demanda: {e_extract}", exc_info=True)
                return jsonify({"erro": f"Falha ao processar o arquivo modelo original: {nome_arquivo_req}"}), 500
        else:
            logger.error(f"Arquivo .txt para '{nome_arquivo_req}' não encontrado (e nenhum .odt correspondente).")
            return jsonify({"erro": f"Conteúdo textual para '{nome_arquivo_req}' não encontrado."}), 404
            
    try:
        with open(caminho_arquivo_txt_para_ler, "r", encoding="utf-8") as f:
            conteudo = f.read()
        logger.info(f"Conteúdo de '{caminho_arquivo_txt_para_ler.name}' lido com sucesso.")
        return jsonify({"conteudo": conteudo})
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo de texto '{caminho_arquivo_txt_para_ler}': {e}", exc_info=True)
        return jsonify({"erro": f"Erro interno ao ler o conteúdo do modelo: {e}"}), 500


@app.route("/gerenciar_modelos")
def gerenciar_modelos_page():
    logger = app.logger
    logger.info("Acessando rota /gerenciar_modelos")

    modelos_pecas = []
    modelos_teses_lista = []

    # Modelos do sistema
    for nome_arq_sistema_txt in MODELOS_SISTEMA_NOMES:
        caminho_txt = PASTA_MODELOS_BASE / nome_arq_sistema_txt
        if caminho_txt.is_file():
            nome_base = nome_arq_sistema_txt[:-4]
            odt_correspondente = PASTA_MODELOS_BASE / f"{nome_base}.odt"
            formato_orig = "odt" if odt_correspondente.exists() else "txt"
            modelos_pecas.append({
                "id": nome_arq_sistema_txt,
                "nome": f"{nome_arq_sistema_txt} (Sistema, original: {formato_orig.upper()})",
                "data_modificacao": datetime.fromtimestamp(caminho_txt.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
                "editavel": True, "deletavel": False, "eh_sistema": True, "formato_original": formato_orig,
                "nome_arquivo_original_odt_ou_txt": odt_correspondente.name if formato_orig == 'odt' else nome_arq_sistema_txt
            })

    # Modelos de usuário (peças e teses)
    for pasta_usuario_tipo, tipo_item in [(PASTA_PECAS_USUARIO, "peça"), (PASTA_TESES_USUARIO, "tese")]:
        if pasta_usuario_tipo.exists():
            for nome_arquivo_item in os.listdir(pasta_usuario_tipo):
                caminho_item = pasta_usuario_tipo / nome_arquivo_item
                if caminho_item.is_file():
                    formato_original_item = caminho_item.suffix[1:].lower()
                    id_item = nome_arquivo_item
                    nome_exibicao_item = nome_arquivo_item

                    conteudo_completo_item = ""
                    arquivo_txt_associado = (
                        pasta_usuario_tipo / (nome_arquivo_item[:-4] + ".txt" if formato_original_item == "odt" else nome_arquivo_item)
                    )
                    if arquivo_txt_associado.exists():
                        try:
                            with open(arquivo_txt_associado, "r", encoding="utf-8") as f_txt:
                                conteudo_completo_item = f_txt.read().strip()
                        except Exception as e_read:
                            logger.error(f"Erro ao ler conteúdo de {arquivo_txt_associado} para {nome_arquivo_item}: {e_read}")

                    item_data = {
                        "id": id_item,
                        "nome": nome_exibicao_item,
                        "nome_arquivo": id_item,
                        "data_modificacao": datetime.fromtimestamp(caminho_item.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
                        "editavel": True,
                        "deletavel": True,
                        "eh_sistema": False,
                        "formato_original": formato_original_item,
                        "conteudo_completo": conteudo_completo_item
                    }

                    if tipo_item == "peça":
                        if id_item not in MODELOS_SISTEMA_NOMES:
                            modelos_pecas.append(item_data)
                    else:  # tese
                        item_data["eh_predefinida"] = False
                        modelos_teses_lista.append(item_data)

    # Teses predefinidas
    for idx, texto_tese_predef in enumerate(TESES_DISPONIVEIS):
        modelos_teses_lista.append({
            "id": f"tese_predefinida_sistema_{idx}",
            "nome": texto_tese_predef,
            "nome_arquivo": f"tese_predefinida_sistema_{idx}",
            "conteudo_completo": texto_tese_predef,
            "data_modificacao": "N/A",
            "editavel": True,
            "deletavel": False,
            "eh_predefinida": True,
            "formato_original": "interno"
        })

    logger.debug(f"Modelos de peças para gerenciar: {len(modelos_pecas)}")
    logger.debug(f"Modelos de teses para gerenciar: {len(modelos_teses_lista)}")
    return render_template("gerenciar_modelos.html", modelos_pecas=modelos_pecas, modelos_teses=modelos_teses_lista, title="Gerenciar modelos e teses")



@app.route('/salvar_modelo', methods=['POST'])
def salvar_modelo_endpoint():    
    logger = app.logger
    try:
        nome_modelo_form = request.form.get('nome', '').strip() # Nome base que o usuário quer
        tipo_modelo = request.form.get('tipo') 
        conteudo_texto_form = request.form.get('conteudo', '')
        modelo_nome_original_arquivo = request.form.get('modelo_nome_original') # Nome do .odt ou .txt original
        eh_predefinida = request.form.get('modelo_eh_predefinida', 'false').lower() == 'true'
        arquivo_upload = request.files.get('arquivo')

        logger.info(f"Tentativa de salvar modelo: Nome Form: {nome_modelo_form}, Tipo: {tipo_modelo}, Editando: {modelo_nome_original_arquivo or 'Não'}, Upload: {'Sim' if arquivo_upload else 'Não'}")

        if not nome_modelo_form or not tipo_modelo:
            return jsonify({"erro": "Nome e tipo do modelo são obrigatórios."}), 400
        if eh_predefinida: # Teses predefinidas não são salvas por aqui
            return jsonify({"erro": "Itens predefinidos do sistema não podem ser alterados."}), 403

        nome_arquivo_base_seguro = secure_filename(nome_modelo_form)
        if not nome_arquivo_base_seguro:
            nome_arquivo_base_seguro = f"{tipo_modelo}_anonimo_{uuid.uuid4().hex[:6]}"

        pasta_destino = PASTA_PECAS_USUARIO if tipo_modelo == 'peca' else PASTA_TESES_USUARIO
        
        caminho_odt_final = pasta_destino / f"{nome_arquivo_base_seguro}.odt"
        caminho_txt_final = pasta_destino / f"{nome_arquivo_base_seguro}.txt"
        conteudo_final_para_txt = conteudo_texto_form.strip()

        # Lidar com upload de arquivo
        if arquivo_upload and arquivo_upload.filename:
            if not extensao_permitida_geral(arquivo_upload.filename, EXTENSOES_PERMITIDAS_MODELO_UPLOAD):
                return jsonify({"erro": f"Formato de arquivo inválido. Use {', '.join(EXTENSOES_PERMITIDAS_MODELO_UPLOAD)}."}), 400
            
            extensao_upload = Path(arquivo_upload.filename).suffix.lower()
            caminho_temporario_upload = UPLOAD_FOLDER / secure_filename(f"temp_upload_{uuid.uuid4().hex[:8]}{extensao_upload}")
            UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
            arquivo_upload.save(caminho_temporario_upload)

            try:
                conteudo_extraido_do_upload = extrair_texto_de_arquivo(caminho_temporario_upload)
                conteudo_final_para_txt = conteudo_extraido_do_upload # Prioriza conteúdo do arquivo
                
                if extensao_upload == ".odt":
                    # Se fez upload de ODT, ele será o novo ODT mestre.
                    # Remove ODT antigo com nome novo se existir para evitar conflito com move
                    if caminho_odt_final.exists() and (not modelo_nome_original_arquivo or Path(modelo_nome_original_arquivo).stem != nome_arquivo_base_seguro):
                        os.remove(caminho_odt_final)
                    shutil.move(str(caminho_temporario_upload), str(caminho_odt_final))
                    logger.info(f"Novo arquivo .odt '{caminho_odt_final.name}' salvo/movido.")
                else: # .txt foi upado
                    # Se um .txt foi upado, ele é o "mestre" textual. Remove qualquer .odt com o mesmo nome base.
                    if caminho_odt_final.exists():
                        logger.info(f"Removendo .odt '{caminho_odt_final.name}' pois um .txt foi carregado com o mesmo nome base.")
                        os.remove(caminho_odt_final)
                    # O conteúdo já foi extraído para conteudo_final_para_txt
                    os.remove(caminho_temporario_upload) # Remove temp .txt
            except ValueError as e_extract:
                if caminho_temporario_upload.exists(): os.remove(caminho_temporario_upload)
                return jsonify({"erro": str(e_extract)}), 400
            except Exception as e_file_proc:
                if caminho_temporario_upload.exists(): os.remove(caminho_temporario_upload)
                logger.error(f"Erro ao processar arquivo de upload: {e_file_proc}", exc_info=True)
                return jsonify({"erro": "Erro ao processar arquivo de upload."}), 500
        
        elif not conteudo_final_para_txt and not modelo_nome_original_arquivo : # Criando novo, sem upload e sem texto
             return jsonify({"erro": "Conteúdo ou arquivo são necessários para um novo item."}), 400


        # Lógica de Renomear/Excluir arquivos antigos se estiver editando e o nome base mudou
        if modelo_nome_original_arquivo and Path(modelo_nome_original_arquivo).stem != nome_arquivo_base_seguro:
            pasta_origem = PASTA_PECAS_USUARIO if tipo_modelo == 'peca' and modelo_nome_original_arquivo not in MODELOS_SISTEMA_NOMES else \
                           PASTA_TESES_USUARIO if tipo_modelo == 'tese' and not modelo_nome_original_arquivo.startswith("tese_predefinida_sistema_") else \
                           PASTA_MODELOS_BASE if tipo_modelo == 'peca' and modelo_nome_original_arquivo in MODELOS_SISTEMA_NOMES else \
                           None # Não deve acontecer para predefinidas, já tratado

            if pasta_origem: # Só renomeia/exclui se não for modelo de sistema que está sendo "copiado"
                nome_base_antigo = Path(modelo_nome_original_arquivo).stem
                odt_antigo = pasta_origem / f"{nome_base_antigo}.odt"
                txt_antigo = pasta_origem / f"{nome_base_antigo}.txt"
                
                if odt_antigo.exists(): 
                    if not (arquivo_upload and Path(arquivo_upload.filename).suffix.lower() == ".odt"): # Se não foi substituído por um novo ODT
                        if caminho_odt_final.exists(): os.remove(caminho_odt_final) # Remove o .odt do novo nome se já existia (raro)
                        shutil.move(str(odt_antigo), str(caminho_odt_final))
                    elif odt_antigo != caminho_odt_final : # Se o upload de ODT não foi para o mesmo path do antigo
                        os.remove(odt_antigo) # Remove ODT antigo pois foi substituído por upload
                
                if txt_antigo.exists() and txt_antigo != caminho_txt_final: # Se não está sobrescrevendo o mesmo arquivo
                    if caminho_txt_final.exists() and not (arquivo_upload and Path(arquivo_upload.filename).suffix.lower() == ".txt"):
                         pass # Deixa o .txt existente do novo nome, pois será sobrescrito abaixo
                    else:
                        shutil.move(str(txt_antigo), str(caminho_txt_final))
        
        # Verifica se o caminho final já existe (para criação)
        if not modelo_nome_original_arquivo and (caminho_txt_final.exists() or (arquivo_upload and Path(arquivo_upload.filename).suffix.lower() == ".odt" and caminho_odt_final.exists())):
            return jsonify({"erro": f"Um item com o nome '{nome_arquivo_base_seguro}' já existe. Escolha outro nome."}), 400


        # Salva o arquivo .txt com o conteúdo final (do upload ou do textarea)
        with open(caminho_txt_final, 'w', encoding='utf-8') as f:
            f.write(conteudo_final_para_txt)
        logger.info(f"Conteúdo de texto salvo em '{caminho_txt_final.name}'")

        return jsonify({"mensagem": f"'{nome_modelo_form}' salvo com sucesso!"})

    except Exception as e:
        app.logger.exception("Erro geral ao salvar modelo/tese.")
        return jsonify({"erro": f"Ocorreu um erro inesperado ao salvar: {str(e)}"}), 500


@app.route('/excluir_modelo', methods=['POST'])
def excluir_modelo_endpoint():
    logger = app.logger
    data = request.get_json()
    nome_arquivo_ref = data.get('nome_arquivo') # Pode ser nome.odt ou nome.txt
    tipo = data.get('tipo')
    logger.info(f"Requisição para excluir: {nome_arquivo_ref}, tipo: {tipo}")

    if not nome_arquivo_ref or not tipo:
        return jsonify({"erro": "Nome do arquivo e tipo são obrigatórios."}), 400

    if (tipo == 'peca' and nome_arquivo_ref in MODELOS_SISTEMA_NOMES) or \
       (tipo == 'tese' and nome_arquivo_ref.startswith("tese_predefinida_sistema_")):
        return jsonify({"erro": "Itens do sistema não podem ser excluídos."}), 403

    pasta_base_item = PASTA_PECAS_USUARIO if tipo == 'peca' else PASTA_TESES_USUARIO
    nome_base = Path(nome_arquivo_ref).stem

    arquivo_odt_para_excluir = pasta_base_item / f"{nome_base}.odt"
    arquivo_txt_para_excluir = pasta_base_item / f"{nome_base}.txt"
    
    excluido_algum = False
    try:
        if arquivo_odt_para_excluir.exists() and arquivo_odt_para_excluir.is_file():
            os.remove(arquivo_odt_para_excluir)
            logger.info(f"Arquivo '{arquivo_odt_para_excluir.name}' excluído.")
            excluido_algum = True
        if arquivo_txt_para_excluir.exists() and arquivo_txt_para_excluir.is_file():
            os.remove(arquivo_txt_para_excluir)
            logger.info(f"Arquivo '{arquivo_txt_para_excluir.name}' excluído.")
            excluido_algum = True
        
        if not excluido_algum:
            logger.warning(f"Nenhum arquivo encontrado para exclusão com base em '{nome_base}' na pasta {pasta_base_item}")
            return jsonify({"erro": f"Modelo/Tese '{nome_base}' não encontrado para exclusão."}), 404
            
        return jsonify({"mensagem": f"'{nome_base}' e arquivos associados excluídos com sucesso!"})
    except Exception as e:
        logger.exception(f"Erro ao excluir arquivos para '{nome_base}'.")
        return jsonify({"erro": f"Erro interno ao excluir: {str(e)}"}), 500


@app.route('/gerar_peca_com_ia', methods=['POST'])
def gerar_peca_com_ia_endpoint():
    logger = app.logger
    data = request.json
    resumo_tecnico_frontend = data.get('resumo_tecnico')
    teses_selecionadas = data.get('teses_selecionadas', [])
    tipo_recurso_frontend = data.get('tipo_recurso')
    dados_processo_frontend = data.get('dados_processo', {})

    logger.info(f"Requisição para /gerar_peca_com_ia recebida.")

    if not resumo_tecnico_frontend or not teses_selecionadas:
        return jsonify({"erro": "Resumo técnico e ao menos uma tese selecionada são necessários."}), 400

    ultimo_processamento_servidor = app.config.get("ULTIMO_PROCESSAMENTO")
    dados_estado_servidor = {}
    estrutura_base_servidor = {}

    if ultimo_processamento_servidor and isinstance(ultimo_processamento_servidor.get("estado"), dict):
        dados_estado_servidor = ultimo_processamento_servidor["estado"]
        if isinstance(dados_estado_servidor.get("estrutura_base"), dict):
            estrutura_base_servidor = dados_estado_servidor["estrutura_base"]
    else:
        logger.warning("Nenhum 'ULTIMO_PROCESSAMENTO' válido encontrado no app.config. Usando dados do frontend ou defaults.")

    resumo_tecnico_para_agente = dados_estado_servidor.get('resumo', resumo_tecnico_frontend)
    tipo_recurso_para_agente = dados_estado_servidor.get('tipo_recurso', tipo_recurso_frontend)

    tipo_recurso_usado_para_modelo = "REsp"
    if tipo_recurso_para_agente and tipo_recurso_para_agente != "Indeterminado" and tipo_recurso_para_agente in CAMINHO_MODELOS:
        tipo_recurso_usado_para_modelo = tipo_recurso_para_agente
    else:
        logger.warning(f"Tipo de recurso para modelo não claramente definido ('{tipo_recurso_para_agente}'), usando default '{tipo_recurso_usado_para_modelo}'.")

    modelo_path_obj = CAMINHO_MODELOS.get(tipo_recurso_usado_para_modelo, Path(MODELO_PADRAO))

    if not modelo_path_obj.exists():
        logger.error(f"Modelo base TXT não encontrado: {modelo_path_obj} para tipo {tipo_recurso_usado_para_modelo}")
        return jsonify({"erro": f"Arquivo de modelo base (.txt) para '{tipo_recurso_usado_para_modelo}' não encontrado no servidor."}), 500

    dados_para_agente = {
        'numero_processo': estrutura_base_servidor.get('numero_processo') or dados_processo_frontend.get('numero_processo', "{{NUM_PROCESSO}}"),
        'recorrente': estrutura_base_servidor.get('recorrente') or dados_processo_frontend.get('recorrente', "{{NOME_RECORRENTE}}"),
        'CIDADE': "Goiânia",
        'DATA_ATUAL': datetime.now().strftime("%d de %B de %Y"),
        'NOME_PROMOTOR': "Promotor(a) de Justiça",
        'TIPO_RECURSO_MAIUSCULO': tipo_recurso_usado_para_modelo.upper(),
        'SAUDACAO_TRIBUNAL_SUPERIOR': "COLENDO SUPERIOR TRIBUNAL DE JUSTIÇA" if tipo_recurso_usado_para_modelo == "REsp"
                                     else "EXCELSO SUPREMO TRIBUNAL FEDERAL" if tipo_recurso_usado_para_modelo == "RE"
                                     else "{{SAUDACAO_TRIBUNAL_SUPERIOR}}",
        'NUM_EVENTOS_ACORDAOS': estrutura_base_servidor.get('num_eventos', "{{NUM_EVENTOS_ACORDAOS}}"),
        'ARTIGO_FUNDAMENTO_RECURSO': estrutura_base_servidor.get('artigo_fundamento', "{{ARTIGO_FUNDAMENTO_RECURSO}}"),
        'NUMERO_CONTRARRAZOES': "{{NUMERO_CONTRARRAZOES}}",
        'ANO_ATUAL': str(datetime.now().year),
        'NOME_NUCLEO_OU_PROMOTORIA': "{{NOME_NUCLEO_OU_PROMOTORIA}}",
        'NUM_PORTARIA': "{{NUM_PORTARIA}}",
        'COMPLEMENTO_CARGO_PROMOTOR': "",
        'INFO_DELEGACAO_PROMOTOR': ""
    }

    logger.debug(f"Dados para agente: {dados_para_agente}")
    logger.debug(f"Resumo para agente (início): {resumo_tecnico_para_agente[:200] if resumo_tecnico_para_agente else 'Nenhum'}...")

    arquivos_gerados_nesta_etapa: Dict[str, str] = {}

    try:
        minuta_gerada = construir_minuta_com_ia(
            resumo_tecnico=resumo_tecnico_para_agente,
            teses_selecionadas=teses_selecionadas,
            modelo_base_path=modelo_path_obj,
            dados_processo=dados_para_agente,
            temperatura_ia=0.2
        )

        if isinstance(minuta_gerada, str) and any(
            erro in minuta_gerada for erro in [
                "[ERRO:", "[FALHA NA GERAÇÃO PELA IA", "[CONTEÚDO BLOQUEADO PELA API:", "[RESPOSTA INESPERADA OU VAZIA DA API GEMINI]"
            ]
        ):
            logger.error(f"Agente de IA retornou erro/bloqueio: {minuta_gerada}")
            return jsonify({"erro": f"A IA encontrou um problema ao gerar a peça. Detalhe técnico: {minuta_gerada}"}), 500
        elif minuta_gerada is None:
            logger.error("Agente de IA retornou None.")
            return jsonify({"erro": "A IA não retornou uma minuta válida."}), 500

        # Salvar a minuta gerada como .txt
        nome_arquivo_minuta_txt = f"minuta_gerada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        caminho_completo_minuta = PASTA_PECAS_USUARIO / nome_arquivo_minuta_txt

        with open(caminho_completo_minuta, "w", encoding="utf-8") as f_minuta:
            f_minuta.write(minuta_gerada)
        logger.info(f"Minuta gerada pela IA salva em '{caminho_completo_minuta}'")

        # Gerar .docx com python-docx
        try:
            caminho_docx = caminho_completo_minuta.with_suffix(".docx")
            doc = Document()
            for paragrafo in minuta_gerada.strip().split("\n\n"):
                doc.add_paragraph(paragrafo.strip())
            doc.save(caminho_docx)
            logger.info(f"Minuta .docx salva em '{caminho_docx.name}'")
            arquivos_gerados_nesta_etapa["minuta_gerada_docx"] = str(caminho_docx.relative_to(RAIZ_PROJETO))
        except Exception as e_docx:
            logger.error(f"Erro ao gerar .docx: {e_docx}", exc_info=True)


        # Gerar .odt com odfpy
        try:
            caminho_odt = caminho_completo_minuta.with_suffix(".odt")
            odt = OpenDocumentText()
            for paragrafo in minuta_gerada.strip().split("\n\n"):
                p = P(text=paragrafo.strip())
                odt.text.addElement(p)
            odt.save(str(caminho_odt))
            logger.info(f"Minuta .odt salva em '{caminho_odt.name}'")
            arquivos_gerados_nesta_etapa["minuta_gerada_docx"] = str(caminho_docx.relative_to(RAIZ_PROJETO))
        except Exception as e_odt:
            logger.error(f"Erro ao gerar .odt: {e_odt}", exc_info=True)


        # Registrar caminho para download
        if "ULTIMO_PROCESSAMENTO" not in app.config:
            app.config["ULTIMO_PROCESSAMENTO"]["arquivos"] = arquivos_gerados_nesta_etapa
        else:            
            if "ULTIMO_PROCESSAMENTO" not in app.config:
                app.config["ULTIMO_PROCESSAMENTO"] = {"estado": {}, "arquivos": arquivos_gerados_nesta_etapa}
            else:
                app.config["ULTIMO_PROCESSAMENTO"]["arquivos"] = arquivos_gerados_nesta_etapa
            logger.warning("Chave 'ULTIMO_PROCESSAMENTO' não existia em app.config. Criada agora ao salvar arquivos da IA.")
        
        if "arquivos" not in app.config["ULTIMO_PROCESSAMENTO"]:
            app.config["ULTIMO_PROCESSAMENTO"]["arquivos"] = {}

        caminho_relativo_minuta = caminho_completo_minuta.relative_to(RAIZ_PROJETO)
        app.config["ULTIMO_PROCESSAMENTO"]["arquivos"]["minuta_gerada"] = caminho_relativo_minuta
        logger.info(f"Caminho da minuta registrado para download: {caminho_relativo_minuta}")

        return jsonify({"minuta_gerada": minuta_gerada})

    except Exception as e:
        logger.exception("Erro crítico ao gerar ou salvar a minuta com IA.")

    if "ULTIMO_PROCESSAMENTO" in app.config:
        if "arquivos" in app.config["ULTIMO_PROCESSAMENTO"]:
            del app.config["ULTIMO_PROCESSAMENTO"]["arquivos"]
        logger.info("Chave 'arquivos' removida de ULTIMO_PROCESSAMENTO devido a erro.")
    
    return jsonify({"erro": f"Erro interno no servidor ao gerar ou salvar a peça: {str(e)}"}), 500

if __name__ == "__main__":
    # Configuração de logging para execução direta (python interface_flask.py)
    # Se rodando com 'flask run', o logger do app já é configurado em configurar_app()
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if not app.logger.handlers: # Evitar duplicidade se já configurado
            logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(module)s[%(lineno)d]: %(message)s')
            app.logger.info("Logging básico configurado para execução standalone.")
        else:
            app.logger.info("Handlers de logging do app já existem.")
    else: # Modo debug do Flask
        app.logger.info("Rodando em modo debug do Flask, logger já configurado pelo Flask.")
    
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))