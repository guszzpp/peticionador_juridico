# src/peticionador/controladores/interface_flask.py

import os
from datetime import datetime
from pathlib import Path
from flask import (
    Flask, render_template, request, jsonify, flash,
    send_from_directory
)
from werkzeug.utils import secure_filename

from peticionador.controladores.controlador_principal import processar_peticao

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
        title="Gerenciar Modelos e Teses"
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
