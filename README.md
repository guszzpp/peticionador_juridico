Peticionador Jurídico

Este projeto implementa uma aplicação modular em Python para a geração automatizada de contrarrazões de Recurso Especial (REsp) e Recurso Extraordinário (RE), com interface gráfica baseada em Gradio, extração de informações com modelos de linguagem e estruturação conforme padrões institucionais.
Funcionalidades

    Upload de petições em PDF

    Extração automática de:

        Nome do recorrente

        Tipo de recurso (RE ou REsp)

    Geração de resumo técnico com modelo Gemini

    Sugestão de teses e argumentos reutilizáveis

    Geração automática de documentos .docx e .odt

    Interface gráfica com drag-and-drop e customização via CSS

Estrutura do Projeto

peticionador_juridico/
├── src/
│   └── peticionador/
│       ├── agentes/
│       ├── controladores/
│       ├── modelos/
│       ├── servicos/
│       ├── utilitarios/
│       └── assets/
├── testes/
├── scripts/
├── arquivos_gerados/
├── requirements.txt
├── pyproject.toml
└── README.md

Execução local

    Instale as dependências em um ambiente virtual:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

    Execute a interface:

PYTHONPATH=src python src/peticionador/controladores/interface_gradio.py

Testes

Execute os testes unitários com:

pytest

Observações

    O modelo RoBERTa pode ser substituído facilmente por outro compatível via Hugging Face.

    A API Gemini é modular e opcional, podendo ser substituída por outro LLM.

    Os modelos de contrarrazões estão na pasta src/peticionador/modelos.

    ## Considerações de Segurança

Durante o desenvolvimento, a aplicação Gradio é configurada para rodar com:

```python
demo.launch(server_name="0.0.0.0", server_port=7860)  # nosec

Esse bind permite acesso via rede local para fins de teste interno.

Atenção: essa configuração não deve ser utilizada em produção sem camada de autenticação, firewall, proxy reverso e HTTPS. Caso deseje restringir o acesso, modifique para:

demo.launch(server_name="127.0.0.1", server_port=7860)


---

### Motivos para essa prática:

- **Justifica o uso de `# nosec`** para o Bandit em auditorias externas.
- Informa outros desenvolvedores sobre o **risco implícito**.
- Mostra aderência à diretriz da **Política Unificada – item 6.2: “documentar decisões de segurança explícitas”**.
