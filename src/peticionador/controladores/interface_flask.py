# src/peticionador/controladores/interface_flask.py

import os
import shutil # Para renomear arquivos
from datetime import datetime
from pathlib import Path
import uuid # Já estava sendo usado
from flask import (
    Flask, render_template, request, jsonify, flash,
    send_from_directory, current_app # Adicionado current_app
)
from werkzeug.utils import secure_filename
from typing import Optional, Set # <--- ADICIONE ESTA LINHA (ou pelo menos Optional)

from peticionador.controladores.controlador_principal import processar_peticao
import uuid # Para gerar IDs únicos, se necessário, ou usar o nome como ID

# --- Constantes de Caminho e Configuração ---
RAIZ_FLASK_APP = Path(__file__).resolve().parents[3]

CAMINHO_MODELOS = {
    "RE": RAIZ_FLASK_APP / "src/peticionador/modelos/contrarrazoes_re.txt",
    "REsp": RAIZ_FLASK_APP / "src/peticionador/modelos/contrarrazoes_resp.txt",
    "Agravo": RAIZ_FLASK_APP / "src/peticionador/modelos/contrarrazoes_resp.txt"
}
MODELO_PADRAO = CAMINHO_MODELOS["REsp"]
UPLOAD_FOLDER = RAIZ_FLASK_APP / "arquivos_upload"
ARQUIVOS_GERADOS_NOME_PASTA = "arquivos_gerados"
EXTENSOES_PERMITIDAS = {"pdf"}
TESES_DISPONIVEIS = [
    "Ausência de prequestionamento",
    "RE: Súmula 284 STF",
    "RE: Ofensa a dispositivos infraconstitucionais",
    "RE: Tema 339 do STF",
    "RE: Ausência de preliminar de RG"
]

# DEFINIÇÃO DAS PASTAS DE MODELOS (ajuste conforme sua estrutura final)
RAIZ_PROJETO = Path(__file__).resolve().parents[3] # Ajuste se necessário
PASTA_MODELOS_BASE = RAIZ_PROJETO / "src" / "peticionador" / "modelos"
PASTA_PECAS_USUARIO = PASTA_MODELOS_BASE / "pecas_completas"
PASTA_TESES_USUARIO = PASTA_MODELOS_BASE / "teses_avulsas"

# Garante que as pastas de usuário existam
PASTA_PECAS_USUARIO.mkdir(parents=True, exist_ok=True)
PASTA_TESES_USUARIO.mkdir(parents=True, exist_ok=True)

MODELOS_SISTEMA_NOMES = ["contrarrazoes_re.txt", "contrarrazoes_resp.txt"]

# --- Inicialização da Aplicação Flask ---
def configurar_app() -> Flask:
    pasta_atual = Path(__file__).parent
    app = Flask(__name__,
                template_folder=pasta_atual / "templates",
                static_folder=pasta_atual / "static")

    app.config["SECRET_KEY"] = "sua-chave-secreta-super-segura"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
    app.config["JSON_AS_ASCII"] = False

    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    return app


app = configurar_app()


# --- Funções Auxiliares ---
def extensao_permitida(nome_arquivo: str) -> bool:
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in EXTENSOES_PERMITIDAS


# --- Rotas ---
@app.route('/')
def index():
    return render_template("index.html", teses=TESES_DISPONIVEIS, title="Peticionador Jurídico")


@app.route('/processar', methods=["POST"])
def processar():
    if "arquivo" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivo = request.files["arquivo"]
    if arquivo.filename == '':
        return jsonify({"erro": "Arquivo sem nome"}), 400

    if not extensao_permitida(arquivo.filename):
        return jsonify({"erro": "Extensão não permitida"}), 400

    nome_seguro = secure_filename(arquivo.filename)
    caminho_arquivo = app.config["UPLOAD_FOLDER"] / nome_seguro
    arquivo.save(caminho_arquivo)

    try:
        resultado = processar_peticao(
            caminho_arquivo_pdf=caminho_arquivo,
            modelos_existentes=TESES_DISPONIVEIS,
            modelos_por_tipo=CAMINHO_MODELOS,
            modelo_padrao=MODELO_PADRAO
        )

        estado = resultado.get("estado")
        arquivos = resultado.get("arquivos", {})

        if not estado:
            raise ValueError("Controlador não retornou estado.")

        app.config["ULTIMO_PROCESSAMENTO"] = {
            "estado": {
                "resumo": estado.resumo,
                "argumentos": estado.argumentos_reutilizaveis,
                "recorrente": estado.estrutura_base.get("recorrente", "Não identificado"),
                "tipo_recurso": estado.estrutura_base.get("tipo_recurso", "Indeterminado")
            },
            "arquivos": arquivos
        }

        return jsonify({
            "resumo": estado.resumo,
            "argumentos": estado.argumentos_reutilizaveis,
            "recorrente": estado.estrutura_base.get("recorrente", "Não identificado"),
            "tipo_recurso": estado.estrutura_base.get("tipo_recurso", "Indeterminado"),
            "arquivos": list(arquivos.keys())
        })

    except Exception as erro:
        app.logger.exception("Erro ao processar petição.")
        return jsonify({"erro": str(erro)}), 500


@app.route("/aplicar_tese", methods=["POST"])
def aplicar_tese():
    dados = request.json
    tese = dados.get("tese")
    texto = dados.get("texto_atual", "")

    if not tese:
        return jsonify({"erro": "Tese não especificada"}), 400

    return jsonify({"texto": f"{texto}\n\n{tese}"})


@app.route("/download/<tipo_arquivo>")
def download(tipo_arquivo):
    ultima_execucao = app.config.get("ULTIMO_PROCESSAMENTO")
    if not ultima_execucao:
        return "Erro: Nenhum processamento recente encontrado.", 404

    arquivos = ultima_execucao.get("arquivos", {})
    if tipo_arquivo not in arquivos:
        return f"Erro: Tipo {tipo_arquivo} não disponível.", 404

    caminho_relativo = arquivos[tipo_arquivo]
    caminho_absoluto = RAIZ_FLASK_APP / caminho_relativo
    if not caminho_absoluto.exists():
        return f"Erro: Arquivo não encontrado em {caminho_absoluto}", 404

    return send_from_directory(
        directory=caminho_absoluto.parent,
        path=caminho_absoluto.name,
        as_attachment=True
    )

@app.route("/obter_conteudo_modelo", methods=["GET"])
def obter_conteudo_modelo_endpoint():
    nome_arquivo = request.args.get("nome_arquivo")
    tipo = request.args.get("tipo") # 'peca' ou 'tese'

    if not nome_arquivo or not tipo:
        return jsonify({"erro": "Nome do arquivo e tipo são obrigatórios."}), 400

    caminho_arquivo = None
    if tipo == 'peca':
        # Tenta primeiro na pasta de usuário, depois na base (para modelos de sistema)
        if (PASTA_PECAS_USUARIO / nome_arquivo).exists():
            caminho_arquivo = PASTA_PECAS_USUARIO / nome_arquivo
        elif (PASTA_MODELOS_BASE / nome_arquivo).exists():
             caminho_arquivo = PASTA_MODELOS_BASE / nome_arquivo
        else:
            return jsonify({"erro": f"Modelo de peça '{nome_arquivo}' não encontrado."}), 404
            
    elif tipo == 'tese':
        # Teses predefinidas são tratadas pelo data-attribute no HTML, esta rota é para teses salvas
        caminho_arquivo = PASTA_TESES_USUARIO / nome_arquivo
        if not caminho_arquivo.exists():
             return jsonify({"erro": f"Tese '{nome_arquivo}' não encontrada."}), 404
    else:
        return jsonify({"erro": "Tipo de modelo inválido."}), 400

    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
        return jsonify({"conteudo": conteudo})
    except Exception as e:
        current_app.logger.error(f"Erro ao ler o arquivo {caminho_arquivo}: {e}")
        return jsonify({"erro": f"Erro ao ler o conteúdo do modelo: {e}"}), 500
    
@app.route("/gerenciar_modelos")
def gerenciar_modelos_page():
    modelos_pecas = []
    
    # 1. Carregar Peças do Sistema
    for nome_arquivo_sistema in MODELOS_SISTEMA_NOMES:
        caminho_arquivo = PASTA_MODELOS_BASE / nome_arquivo_sistema
        if caminho_arquivo.exists() and caminho_arquivo.is_file():
            modelos_pecas.append({
                "id": nome_arquivo_sistema,
                "nome": nome_arquivo_sistema,
                "data_modificacao": datetime.fromtimestamp(caminho_arquivo.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
                "editavel": True, # Pode ser editado (será salvo em pecas_completas ou sobrescrito com cuidado)
                "deletavel": False, # Modelos do sistema não são deletáveis
                "eh_sistema": True
            })

    # 2. Carregar Peças do Usuário
    if PASTA_PECAS_USUARIO.exists():
        for nome_arquivo in os.listdir(PASTA_PECAS_USUARIO):
            caminho_arquivo = PASTA_PECAS_USUARIO / nome_arquivo
            if caminho_arquivo.is_file() and nome_arquivo.endswith(".txt"):
                if nome_arquivo not in MODELOS_SISTEMA_NOMES: # Evitar duplicidade se copiado
                    modelos_pecas.append({
                        "id": nome_arquivo,
                        "nome": nome_arquivo,
                        "data_modificacao": datetime.fromtimestamp(caminho_arquivo.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
                        "editavel": True,
                        "deletavel": True,
                        "eh_sistema": False
                    })

    modelos_teses_lista = []
    # 1. Teses Predefinidas (da lista estática)
    for idx, texto_tese in enumerate(TESES_DISPONIVEIS): # TESES_DISPONIVEIS deve estar definida globalmente
        id_tese_predefinida = f"tese_predefinida_{idx}"
        modelos_teses_lista.append({
            "id": id_tese_predefinida,
            "nome": texto_tese, # Conteúdo é o nome para exibição
            "nome_arquivo": id_tese_predefinida, # Usado como placeholder para data-nome no HTML
            "conteudo_completo": texto_tese, # Para preencher o modal
            "data_modificacao": "N/A",
            "editavel": True,
            "deletavel": False,
            "eh_predefinida": True
        })

    # 2. Teses Salvas pelo Usuário
    if PASTA_TESES_USUARIO.exists():
        for nome_arquivo_tese in os.listdir(PASTA_TESES_USUARIO):
            caminho_tese = PASTA_TESES_USUARIO / nome_arquivo_tese
            if caminho_tese.is_file() and nome_arquivo_tese.endswith(".txt"):
                conteudo_tese = ""
                try:
                    with open(caminho_tese, "r", encoding="utf-8") as f_tese:
                        conteudo_tese = f_tese.read().strip()
                except Exception as e:
                    current_app.logger.error(f"Erro ao ler tese {nome_arquivo_tese}: {e}")
                    conteudo_tese = "Erro ao carregar conteúdo."
                
                # Nome para exibição pode ser o início do conteúdo ou o nome do arquivo
                nome_exibicao = conteudo_tese[:70] + "..." if len(conteudo_tese) > 70 else conteudo_tese
                if not nome_exibicao.strip(): # Se o conteúdo for vazio, usar nome do arquivo
                    nome_exibicao = nome_arquivo_tese

                modelos_teses_lista.append({
                    "id": nome_arquivo_tese, 
                    "nome": nome_exibicao,
                    "nome_arquivo": nome_arquivo_tese, # Para edição/exclusão
                    "conteudo_completo": conteudo_tese, # Para preencher o modal
                    "data_modificacao": datetime.fromtimestamp(caminho_tese.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
                    "editavel": True,
                    "deletavel": True,
                    "eh_predefinida": False
                })

    return render_template(
        "gerenciar_modelos.html",
        modelos_pecas=modelos_pecas,
        modelos_teses=modelos_teses_lista,
        title="Gerenciar modelos e teses"
    )

# Sua função extrair_texto_de_arquivo (adaptada para só .txt ou para erros se outras extensões forem enviadas)
def extrair_texto_de_arquivo(caminho_arquivo_upload: Path) -> str:
    extensao = caminho_arquivo_upload.suffix.lower()
    if extensao == ".txt":
        with open(caminho_arquivo_upload, 'r', encoding='utf-8') as f:
            return f.read()
    # Se você reabilitar docx/odt, adicione a lógica aqui
    # elif extensao == ".docx": ...
    # elif extensao == ".odt": ...
    else:
        # O HTML só permite .txt, então isso não deve acontecer a menos que o accept seja modificado
        raise ValueError(f"Tipo de arquivo não suportado para extração direta de texto: {extensao}")


@app.route('/salvar_modelo', methods=['POST'])
def salvar_modelo_endpoint():
    try:
        nome_modelo_form = request.form.get('nome', '').strip()
        tipo_modelo = request.form.get('tipo') # 'peca' ou 'tese'
        conteudo_texto = request.form.get('conteudo', '')
        
        # ID do modelo (nome do arquivo original se estiver editando)
        modelo_id_original = request.form.get('modelo_id') # Pode ser o nome do arquivo original ou ID da tese predefinida
        modelo_nome_original_arquivo = request.form.get('modelo_nome_original') # Nome original do arquivo
        eh_predefinida_str = request.form.get('modelo_eh_predefinida', 'false')
        eh_predefinida = eh_predefinida_str.lower() == 'true'

        arquivo_upload = request.files.get('arquivo')

        if not nome_modelo_form or not tipo_modelo:
            return jsonify({"erro": "Nome e tipo do modelo são obrigatórios."}), 400

        if eh_predefinida and tipo_modelo == 'tese':
            return jsonify({"erro": "Teses predefinidas não podem ser alteradas."}), 400

        # Sanitizar nome para arquivo (removendo .txt se o usuário digitou)
        nome_arquivo_base = nome_modelo_form
        if nome_arquivo_base.lower().endswith(".txt"):
            nome_arquivo_base = nome_arquivo_base[:-4]
        
        nome_arquivo_seguro = secure_filename(nome_arquivo_base)
        if not nome_arquivo_seguro:
            nome_arquivo_seguro = f"modelo_anonimo_{uuid.uuid4().hex[:6]}"
        nome_arquivo_final_com_ext = f"{nome_arquivo_seguro}.txt"

        pasta_destino = None
        pasta_origem_edicao = None # Para caso de renomear modelo de sistema

        if tipo_modelo == 'peca':
            pasta_destino = PASTA_PECAS_USUARIO # Peças de usuário sempre vão para cá
            if modelo_nome_original_arquivo: # Se é edição
                if modelo_nome_original_arquivo in MODELOS_SISTEMA_NOMES:
                    # Editando um modelo do sistema, será salvo como uma cópia na pasta de usuário
                    pasta_origem_edicao = PASTA_MODELOS_BASE 
                else:
                    pasta_origem_edicao = PASTA_PECAS_USUARIO
        elif tipo_modelo == 'tese':
            pasta_destino = PASTA_TESES_USUARIO
            if modelo_nome_original_arquivo: # Se é edição
                 pasta_origem_edicao = PASTA_TESES_USUARIO # Teses só existem na pasta de usuário ou são predefinidas
        else:
            return jsonify({"erro": "Tipo de modelo inválido."}), 400

        pasta_destino.mkdir(parents=True, exist_ok=True)
        caminho_final_arquivo = pasta_destino / nome_arquivo_final_com_ext
        
        conteudo_para_salvar = conteudo_texto

        if arquivo_upload: # Se um arquivo foi explicitamente enviado
            if not arquivo_upload.filename.lower().endswith(".txt"):
                 return jsonify({"erro": "Apenas arquivos .txt são permitidos para upload direto no momento."}), 400
            
            # Salva temporariamente para ler
            nome_seguro_upload = secure_filename(f"temp_{arquivo_upload.filename}")
            caminho_temporario_upload = UPLOAD_FOLDER / nome_seguro_upload # UPLOAD_FOLDER deve estar definido
            UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
            arquivo_upload.save(caminho_temporario_upload)
            
            try:
                conteudo_para_salvar = extrair_texto_de_arquivo(caminho_temporario_upload)
            except ValueError as e:
                os.remove(caminho_temporario_upload)
                return jsonify({"erro": str(e)}), 400
            finally:
                if caminho_temporario_upload.exists():
                    os.remove(caminho_temporario_upload)
        
        if not conteudo_para_salvar.strip() and not modelo_id_original: # Novo modelo sem conteúdo
            return jsonify({"erro": "Conteúdo não pode ser vazio para um novo modelo."}), 400

        # Lógica de Edição (Renomear/Sobrescrever)
        if modelo_nome_original_arquivo and pasta_origem_edicao:
            caminho_antigo_arquivo = pasta_origem_edicao / modelo_nome_original_arquivo
            
            # Se o nome do arquivo mudou ou se moveu de pasta (sistema para usuário)
            if caminho_antigo_arquivo != caminho_final_arquivo and caminho_antigo_arquivo.exists():
                if tipo_modelo == 'peca' and modelo_nome_original_arquivo in MODELOS_SISTEMA_NOMES:
                    # Editando modelo de sistema: salva como cópia em pasta de usuário, não mexe no original.
                    # O caminho_final_arquivo já aponta para pasta_destino (PASTA_PECAS_USUARIO)
                    pass # Apenas cria o novo arquivo na pasta de usuário
                elif caminho_final_arquivo.exists(): # Novo nome já existe na pasta destino
                     return jsonify({"erro": f"Um modelo com o nome '{nome_arquivo_final_com_ext}' já existe na pasta de destino. Escolha outro nome."}), 400
                else: # Renomeia
                    try:
                        shutil.move(str(caminho_antigo_arquivo), str(caminho_final_arquivo))
                        current_app.logger.info(f"Modelo '{modelo_nome_original_arquivo}' renomeado para '{nome_arquivo_final_com_ext}'")
                    except Exception as e:
                        current_app.logger.error(f"Erro ao renomear '{modelo_nome_original_arquivo}' para '{nome_arquivo_final_com_ext}': {e}")
                        return jsonify({"erro": f"Erro ao tentar renomear o modelo: {e}"}), 500
            # Se o nome não mudou, apenas sobrescreve no caminho_final_arquivo (que será igual ao caminho_antigo_arquivo se não for modelo de sistema)
        elif caminho_final_arquivo.exists() and not modelo_nome_original_arquivo : # Criando novo mas nome já existe
            return jsonify({"erro": f"Um modelo com o nome '{nome_arquivo_final_com_ext}' já existe. Escolha outro nome."}), 400


        # Salvar o conteúdo final
        try:
            with open(caminho_final_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo_para_salvar)
            msg = f"Modelo '{nome_modelo_form}' salvo com sucesso como '{nome_arquivo_final_com_ext}'!"
            current_app.logger.info(msg)
            return jsonify({"mensagem": msg})
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar arquivo de modelo '{nome_modelo_form}': {e}")
            return jsonify({"erro": f"Erro interno ao salvar o modelo: {e}"}), 500

    except Exception as e:
        current_app.logger.exception("Erro geral ao salvar modelo.")
        return jsonify({"erro": f"Ocorreu um erro inesperado: {str(e)}"}), 500

@app.route('/excluir_modelo', methods=['POST'])
def excluir_modelo_endpoint():
    try:
        data = request.get_json()
        nome_arquivo = data.get('nome_arquivo')
        tipo = data.get('tipo')

        if not nome_arquivo or not tipo:
            return jsonify({"erro": "Nome do arquivo e tipo são obrigatórios para exclusão."}), 400

        if tipo == 'peca':
            if nome_arquivo in MODELOS_SISTEMA_NOMES:
                return jsonify({"erro": "Modelos de peça do sistema não podem ser excluídos."}), 403 # Forbidden
            # Exclui da pasta de usuário
            caminho_arquivo = PASTA_PECAS_USUARIO / nome_arquivo
            pasta_verificada = PASTA_PECAS_USUARIO
        elif tipo == 'tese':
            # Teses predefinidas não são arquivos, então não serão encontradas aqui e nem deveriam ser tentadas
            if nome_arquivo.startswith("tese_predefinida_"):
                 return jsonify({"erro": "Teses predefinidas não podem ser excluídas."}), 403 # Forbidden
            caminho_arquivo = PASTA_TESES_USUARIO / nome_arquivo
            pasta_verificada = PASTA_TESES_USUARIO
        else:
            return jsonify({"erro": "Tipo de modelo inválido para exclusão."}), 400

        if caminho_arquivo.exists() and caminho_arquivo.is_file() and caminho_arquivo.parent.resolve() == pasta_verificada.resolve():
            try:
                os.remove(caminho_arquivo)
                current_app.logger.info(f"Modelo '{nome_arquivo}' ({tipo}) excluído com sucesso.")
                return jsonify({"mensagem": f"Modelo '{nome_arquivo}' excluído com sucesso!"})
            except Exception as e:
                current_app.logger.error(f"Erro ao excluir o arquivo {caminho_arquivo}: {e}")
                return jsonify({"erro": f"Erro interno ao excluir o modelo: {e}"}), 500
        else:
            return jsonify({"erro": f"Modelo '{nome_arquivo}' não encontrado ou acesso negado."}), 404

    except Exception as e:
        current_app.logger.exception("Erro geral ao excluir modelo.")
        return jsonify({"erro": f"Ocorreu um erro inesperado ao excluir: {str(e)}"}), 500

# Adicione a nova função de verificação de extensão ou modifique a existente
def extensao_permitida(nome_arquivo: str, extensoes_upload_modelo: Optional[set] = None) -> bool:
    extensoes = extensoes_upload_modelo if extensoes_upload_modelo is not None else EXTENSOES_PERMITIDAS
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in extensoes


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
