# Peticionador Jurídico

## Descrição

O Peticionador Jurídico é uma aplicação desenvolvida em Python com o objetivo de auxiliar na elaboração de peças processuais, especificamente contrarrazões a Recursos Especiais (REsp) e Recursos Extraordinários (RE). A ferramenta utiliza modelos de linguagem avançados (Google Gemini) para extrair informações relevantes de petições em formato PDF, gerar resumos técnicos, sugerir teses jurídicas e, finalmente, construir uma minuta da peça de contrarrazões.

A interface do usuário é construída com Flask, permitindo o upload de documentos, a interação com as sugestões da IA e o download das peças geradas nos formatos .docx e .odt.

## Funcionalidades Principais

* Upload de petições de recurso em formato PDF.
* Extração automática de informações como nome do recorrente e tipo de recurso utilizando IA.
* Geração de resumo técnico da petição do recorrente através de IA.
* Sugestão de teses e argumentos aplicáveis pela IA.
* Construção de minuta de contrarrazões com base em modelo pré-definido, resumo técnico e teses selecionadas, utilizando IA.
* Gerenciamento de modelos de peças completas e teses avulsas (arquivos .txt ou .odt).
* Download das minutas geradas em formatos .docx e .odt.
* Interface web intuitiva desenvolvida com Flask.

## Estrutura do Projeto

O projeto segue uma arquitetura modular, com as seguintes pastas principais dentro de `src/peticionador/`:

* `agentes/`: Módulos responsáveis pela interação com os modelos de linguagem (IA).
* `controladores/`: Contém a lógica da interface Flask, incluindo rotas, templates HTML e arquivos estáticos (CSS, JavaScript).
* `modelos/`: Armazena modelos de peças, teses avulsas e a definição do estado da petição.
* `servicos/`: Módulos com lógica de negócio, como extração de PDF, pré-processamento de texto e geração de documentos.
* `utilitarios/`: Funções e configurações auxiliares, como o gerenciamento de chaves de API.

Outras pastas importantes na raiz do projeto incluem:

* `testes/`: Contém os testes unitários e de integração.
* `scripts/`: Scripts para iniciar a aplicação e para testes manuais de funcionalidades.
* `arquivos_upload/`: Pasta temporária para arquivos PDF enviados pelo usuário.
* `arquivos_gerados/` (ou a pasta configurada): Destino padrão para algumas saídas de arquivos (configurável).
* `src/peticionador/modelos/pecas_completas/`: Local onde as minutas geradas pela IA e modelos de peças completas gerenciados pelo usuário são armazenados.
* `src/peticionador/modelos/teses_avulsas/`: Local para teses avulsas gerenciadas pelo usuário.

## Configuração e Execução

### Pré-requisitos

* Python 3.9 ou superior.
* Chave de API para o Google Gemini, configurada como variável de ambiente `GEMINI_API_KEY`.

### Instalação

1.  Clone o repositório:
    ```bash
    git clone <url-do-repositorio>
    cd peticionador-juridico
    ```

2.  Crie e ative um ambiente virtual:
    ```bash
    python -m venv venv
    # No Windows
    # venv\Scripts\activate
    # No macOS/Linux
    # source venv/bin/activate
    ```

3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

4.  (Opcional, para desenvolvimento) Instale as dependências de desenvolvimento:
    ```bash
    pip install -r requirements-dev.txt
    ```

5.  Configure a variável de ambiente `GEMINI_API_KEY` com sua chave da API do Google Gemini. Você pode criar um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
    ```
    GEMINI_API_KEY="SUA_CHAVE_API_AQUI"
    ```

### Execução

Para iniciar a aplicação Flask:

```bash
python scripts/iniciar_flask.py