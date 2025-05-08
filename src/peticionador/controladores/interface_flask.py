import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path

from peticionador.controladores.controlador_principal import processar_peticao
from peticionador.servicos.extrator_pdf import extrair_texto_pdf

# Configurações
CAMINHO_MODELOS = {
    "RE": "src/peticionador/modelos/contrarrazoes_re.txt",
    "REsp": "src/peticionador/modelos/contrarrazoes_resp.txt",
    "Agravo": "src/peticionador/modelos/contrarrazoes_resp.txt"  # Usando REsp como base para Agravo
}
MODELO_PADRAO = "src/peticionador/modelos/contrarrazoes_resp.txt"
UPLOAD_FOLDER = 'arquivos_upload'
ALLOWED_EXTENSIONS = {'pdf'}
ARQUIVOS_GERADOS = 'arquivos_gerados'

# Lista de teses pré-carregadas
TESES_DISPONIVEIS = [
    "Ausência de prequestionamento",
    "RE: Súmula 284 STF",
    "RE: Ofensa a dispositivos infraconstitucionais",
    "RE: Tema 339 do STF",
    "RE: Ausência de preliminar de RG"
]

def configurar_app():
    # Obtenha o caminho absoluto para o diretório do módulo atual
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Criar a aplicação Flask com diretórios explícitos
    app = Flask(__name__, 
                template_folder=os.path.join(diretorio_atual, 'templates'),
                static_folder=os.path.join(diretorio_atual, 'static'))
    
    # Configurar UTF-8
    app.config['JSON_AS_ASCII'] = False
    
    app.config['SECRET_KEY'] = 'chave-secreta-temporaria'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB
    
    # Criar diretórios se não existirem
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(ARQUIVOS_GERADOS, exist_ok=True)
    
    return app

app = configurar_app()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html', teses=TESES_DISPONIVEIS)

@app.route('/processar', methods=['POST'])
def processar():
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo enviado')
        return redirect(url_for('index'))
    
    arquivo = request.files['arquivo']
    
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('index'))
    
    if arquivo and allowed_file(arquivo.filename):
        filename = secure_filename(arquivo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        arquivo.save(filepath)
        
        # Extrair texto do PDF
        primeira_pagina, texto_completo = extrair_texto_pdf(filepath)
        
        if not primeira_pagina or not texto_completo:
            flash('Falha ao extrair texto do PDF')
            return redirect(url_for('index'))
        
        try:
            # Processar a petição
            resultado = processar_peticao(
                primeira_pagina,
                texto_completo,
                TESES_DISPONIVEIS,
                CAMINHO_MODELOS,
                MODELO_PADRAO
            )
            
            estado = resultado["estado"]
            arquivos = resultado["arquivos"]
            
            # Salvar caminhos dos arquivos gerados na sessão para download posterior
            app.config['ULTIMO_PROCESSAMENTO'] = {
                'estado': {
                    'resumo': estado.resumo,
                    'argumentos': estado.argumentos_reutilizaveis,
                    'recorrente': estado.estrutura_base.get('recorrente', 'Não identificado'),
                    'tipo_recurso': estado.estrutura_base.get('tipo_recurso', 'Indeterminado')
                },
                'arquivos': arquivos
            }
            
            # Para requisições Ajax (XHR)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'resumo': estado.resumo,
                    'argumentos': estado.argumentos_reutilizaveis,
                    'recorrente': estado.estrutura_base.get('recorrente', 'Não identificado'),
                    'tipo_recurso': estado.estrutura_base.get('tipo_recurso', 'Indeterminado'),
                    'arquivos': list(arquivos.keys())
                })
            
            # Para requisições normais de formulário
            flash('Petição processada com sucesso')
            return render_template('index.html', 
                               teses=TESES_DISPONIVEIS,
                               resumo=estado.resumo,
                               recorrente=estado.estrutura_base.get('recorrente', 'Não identificado'),
                               tipo_recurso=estado.estrutura_base.get('tipo_recurso', 'Indeterminado'))
            
        except Exception as e:
            app.logger.error(f"Erro no processamento: {str(e)}")
            flash(f"Erro ao processar petição: {str(e)}")
            return redirect(url_for('index'))
    
    flash('Tipo de arquivo não permitido')
    return redirect(url_for('index'))

@app.route('/aplicar_tese', methods=['POST'])
def aplicar_tese():
    data = request.json
    tese = data.get('tese')
    texto_atual = data.get('texto_atual', '')
    
    if not tese:
        return jsonify({'erro': 'Tese não especificada'}), 400
    
    texto_atualizado = f"{texto_atual}\n\n{tese}"
    return jsonify({'texto': texto_atualizado})

@app.route('/download/<tipo_arquivo>')
def download(tipo_arquivo):
    if 'ULTIMO_PROCESSAMENTO' not in app.config:
        flash('Nenhum arquivo processado recentemente')
        return redirect(url_for('index'))
    
    arquivos = app.config['ULTIMO_PROCESSAMENTO']['arquivos']
    if tipo_arquivo not in arquivos:
        flash(f'Tipo de arquivo {tipo_arquivo} não disponível')
        return redirect(url_for('index'))
    
    caminho_arquivo = arquivos[tipo_arquivo]
    diretorio = os.path.dirname(caminho_arquivo)
    nome_arquivo = os.path.basename(caminho_arquivo)
    
    # Montar um nome de arquivo personalizado baseado no recorrente
    recorrente = app.config['ULTIMO_PROCESSAMENTO']['estado'].get('recorrente', '')
    tipo_recurso = app.config['ULTIMO_PROCESSAMENTO']['estado'].get('tipo_recurso', '')
    
    if recorrente and tipo_recurso:
        nome_base = f"Contrarrazoes_{tipo_recurso}_{recorrente.replace(' ', '_')}"
        if tipo_arquivo == 'docx':
            nome_personalizado = f"{nome_base}.docx"
        elif tipo_arquivo == 'odt':
            nome_personalizado = f"{nome_base}.odt"
        else:
            nome_personalizado = nome_arquivo
    else:
        nome_personalizado = nome_arquivo
    
    return send_from_directory(diretorio, nome_arquivo, as_attachment=True, download_name=nome_personalizado)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
