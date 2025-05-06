import gradio as gr
from pathlib import Path
from peticionador.controladores.controlador_principal import processar_peticao

CAMINHO_MODELOS = {
    "RE": "src/peticionador/modelos/contrarrazoes_re.txt",
    "REsp": "src/peticionador/modelos/contrarrazoes_resp.txt"
}
MODELO_PADRAO = "src/peticionador/modelos/contrarrazoes_resp.txt"
CAMINHO_CSS = "src/peticionador/assets/style.css"

def processar_arquivo(pdf):
    if not pdf:
        return "Nenhum arquivo enviado.", "", [], {}
    try:
        with open(pdf.name, "rb") as f:
            texto = f.read().decode("utf-8", errors="ignore")
        primeira_pagina = texto[:1000]
        resultado = processar_peticao(primeira_pagina, texto, CAMINHO_MODELOS, MODELO_PADRAO)
        estado = resultado["estado"]
        arquivos = resultado["arquivos"]
        return estado.resumo, estado.argumentos_reutilizaveis, arquivos
    except Exception as e:
        return f"[ERRO] Falha no processamento: {str(e)}", "", {}

def usar_resumo(resumo):
    return resumo

def inserir_modelo(argumento_atual, novo_texto):
    return f"{argumento_atual.strip()}\n{novo_texto}".strip()

with gr.Blocks(css=Path(CAMINHO_CSS).read_text()) as demo:
    gr.Markdown("## Peticionador Jurídico")

    with gr.Row():
        arquivo_pdf = gr.File(label="Upload do Arquivo", type="filepath", file_types=[".pdf"])
        modelos_reutilizaveis = gr.Textbox(label="Modelos Reutilizáveis", interactive=False)

    with gr.Row():
        resumo = gr.Textbox(label="Resumo da Petição", lines=6)
        lista_argumentos = gr.Textbox(label="Seleção de Teses", lines=6)

    btn_gerar = gr.Button("Usar Resumo na Peça")
    pre_visualizacao = gr.Textbox(label="Pré-visualização da minuta", lines=10)
    btn_salvar = gr.Button("Salvar Rascunho")

    resultado_download = gr.Textbox(label="Arquivos Gerados")

    # Lógica
    arquivo_pdf.change(fn=processar_arquivo, inputs=arquivo_pdf,
                       outputs=[resumo, lista_argumentos, resultado_download])
    btn_gerar.click(fn=usar_resumo, inputs=resumo, outputs=pre_visualizacao)

    # Adicionar botões de argumentos simulados
    with gr.Row():
        for tese in [
            "Ausência de prequestionamento",
            "RE: Súmula 284 STF",
            "RE: Ofensa a dispositivos infraconstitucionais",
            "RE: Tema 339 do STF",
            "RE: Ausência de preliminar de RG"
        ]:
            gr.Button(tese, elem_classes="tese-button").click(
                fn=inserir_modelo,
                inputs=[pre_visualizacao, gr.Textbox(value=tese, visible=False)],
                outputs=pre_visualizacao
            )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
