# src/peticionador/controladores/interface_flask.py

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Set # <--- ADICIONE ESTA LINHA (ou pelo menos Optional)
from flask import (
    Flask, render_template, request, jsonify, flash,
    send_from_directory
)
from werkzeug.utils import secure_filename

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


@app.route("/gerenciar_modelos")
def gerenciar_modelos_page():
    modelos_pecas = []
    diretorio_modelos = RAIZ_FLASK_APP / "src/peticionador/modelos"

    if diretorio_modelos.exists():
        for nome in os.listdir(diretorio_modelos):
            if nome.endswith(".txt"):
                caminho = diretorio_modelos / nome
                try:
                    with open(caminho, "r", encoding="utf-8") as f:
                        preview = f.read(100) + "..."
                except Exception:
                    preview = "Erro ao ler conteúdo."

                modelos_pecas.append({
                    "nome": nome,
                    "tipo": "Peça de Sistema",
                    "criado_por": "Sistema",
                    "data_modificacao": datetime.fromtimestamp(caminho.stat().st_mtime).strftime("%d/%m/%Y"),
                    "conteudo_preview": preview,
                    "editavel": True,
                    "deletavel": False
                })

    modelos_teses = [
        {
            "id": f"tese_predefinida_{idx}",
            "nome": texto,
            "tipo": "Tese Predefinida",
            "criado_por": "Sistema",
            "data_modificacao": "N/A",
            "editavel": True,
            "deletavel": False
        }
        for idx, texto in enumerate(TESES_DISPONIVEIS)
    ]

    return render_template(
        "gerenciar_modelos.html",
        modelos_pecas=modelos_pecas,
        modelos_teses=modelos_teses,
        title="Gerenciar modelos e teses"
    )

def extrair_texto_de_arquivo(caminho_arquivo_upload: Path) -> str:
    """
    Extrai texto de arquivos .txt, .docx, .odt.
    Retorna o texto extraído ou lança uma exceção em caso de erro.
    """
    extensao = caminho_arquivo_upload.suffix.lower()
    texto_extraido = ""

    if extensao == ".txt":
        with open(caminho_arquivo_upload, 'r', encoding='utf-8') as f:
            texto_extraido = f.read()
    elif extensao == ".docx":
        try:
            import docx2txt # Requer: pip install docx2txt
            texto_extraido = docx2txt.process(str(caminho_arquivo_upload))
        except ImportError:
            app.logger.error("Biblioteca docx2txt não instalada. Necessária para extrair de .docx")
            raise ValueError("Erro ao processar .docx: dependência ausente no servidor.")
        except Exception as e:
            app.logger.error(f"Erro ao extrair texto de .docx: {e}")
            raise ValueError(f"Erro ao extrair texto de .docx: {e}")
    elif extensao == ".odt":
        try:
            from odf import text, teletype # Requer: pip install odfpy
            from odf.opendocument import load as load_odt
            doc = load_odt(str(caminho_arquivo_upload))
            all_paras = doc.getElementsByType(text.P)
            texto_extraido = "\n\n".join(teletype.extractText(para) for para in all_paras)
        except ImportError:
            app.logger.error("Biblioteca odfpy não instalada. Necessária para extrair de .odt")
            raise ValueError("Erro ao processar .odt: dependência ausente no servidor.")
        except Exception as e:
            app.logger.error(f"Erro ao extrair texto de .odt: {e}")
            raise ValueError(f"Erro ao extrair texto de .odt: {e}")
    else:
        raise ValueError(f"Tipo de arquivo não suportado para extração de texto: {extensao}")
    
    return texto_extraido.strip()


@app.route('/salvar_modelo', methods=['POST'])
def salvar_modelo_endpoint():
    try:
        nome_modelo = request.form.get('nome')
        tipo_modelo = request.form.get('tipo') # 'peca' ou 'tese'
        conteudo_texto = request.form.get('conteudo', '') # Conteúdo do textarea

        if not nome_modelo or not tipo_modelo:
            return jsonify({"erro": "Nome e tipo do modelo são obrigatórios."}), 400

        arquivo_upload = request.files.get('arquivo')
        conteudo_final_modelo = conteudo_texto

        diretorio_base_modelos = RAIZ_FLASK_APP / "src/peticionador/modelos" # Ou um subdiretório
        
        # Define o diretório específico com base no tipo
        if tipo_modelo == 'peca':
            diretorio_destino = diretorio_base_modelos / "pecas_completas"
        elif tipo_modelo == 'tese':
            diretorio_destino = diretorio_base_modelos / "teses_avulsas"
        else:
            return jsonify({"erro": "Tipo de modelo inválido."}), 400
            
        diretorio_destino.mkdir(parents=True, exist_ok=True)
        
        # Sanitizar o nome do modelo para usar como nome de arquivo
        # Evitar caracteres problemáticos e garantir extensão .txt para o conteúdo textual
        nome_arquivo_seguro = secure_filename(nome_modelo).replace('-', '_')
        if not nome_arquivo_seguro: # se o nome for algo como "---"
            nome_arquivo_seguro = f"modelo_{uuid.uuid4().hex[:8]}"
        
        caminho_final_arquivo_txt = diretorio_destino / f"{nome_arquivo_seguro}.txt"


        if arquivo_upload:
            if not extensao_permitida(arquivo_upload.filename, extensoes_upload_modelo={".docx", ".odt", ".txt"}):
                return jsonify({"erro": "Extensão de arquivo não permitida para upload."}), 400
            
            nome_seguro_upload = secure_filename(arquivo_upload.filename)
            caminho_temporario_upload = app.config["UPLOAD_FOLDER"] / f"temp_{nome_seguro_upload}"
            arquivo_upload.save(caminho_temporario_upload)
            
            try:
                app.logger.info(f"Tentando extrair texto de: {caminho_temporario_upload}")
                texto_extraido_do_arquivo = extrair_texto_de_arquivo(caminho_temporario_upload)
                # Se o textarea já tinha algo e um arquivo foi enviado, decidir qual usar ou como mesclar.
                # Aqui, o arquivo tem precedência se fornecer texto.
                if texto_extraido_do_arquivo:
                    conteudo_final_modelo = texto_extraido_do_arquivo
                app.logger.info(f"Texto extraído com sucesso (tamanho: {len(conteudo_final_modelo)}).")
            except ValueError as e: # Erro na extração
                app.logger.error(f"Falha ao extrair texto do arquivo: {e}")
                os.remove(caminho_temporario_upload) # Limpa o arquivo temporário
                return jsonify({"erro": str(e)}), 400
            finally:
                if caminho_temporario_upload.exists():
                    os.remove(caminho_temporario_upload) # Limpa o arquivo temporário

        if not conteudo_final_modelo and not arquivo_upload : # Se nem texto no textarea nem arquivo
             return jsonify({"erro": "Nenhum conteúdo fornecido para o modelo (nem texto, nem arquivo)."}), 400


        # Salvar o conteúdo final (do textarea ou extraído do arquivo) em um arquivo .txt
        try:
            with open(caminho_final_arquivo_txt, 'w', encoding='utf-8') as f:
                f.write(conteudo_final_modelo)
            app.logger.info(f"Modelo '{nome_modelo}' ({tipo_modelo}) salvo em: {caminho_final_arquivo_txt}")
            return jsonify({"mensagem": f"Modelo '{nome_modelo}' salvo com sucesso!"})
        except Exception as e:
            app.logger.error(f"Erro ao salvar arquivo de modelo '{nome_modelo}': {e}")
            return jsonify({"erro": f"Erro interno ao salvar o modelo: {e}"}), 500

    except Exception as e:
        app.logger.exception("Erro geral ao salvar modelo.")
        return jsonify({"erro": f"Ocorreu um erro inesperado: {str(e)}"}), 500

# Adicione a nova função de verificação de extensão ou modifique a existente
def extensao_permitida(nome_arquivo: str, extensoes_upload_modelo: Optional[set] = None) -> bool:
    extensoes = extensoes_upload_modelo if extensoes_upload_modelo is not None else EXTENSOES_PERMITIDAS
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in extensoes


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
