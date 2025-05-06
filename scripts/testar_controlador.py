from peticionador.controladores.controlador_principal import processar_peticao

def main():
    primeira_pagina = """
    RECORRENTE: João da Silva
    Trata-se de Recurso Especial interposto contra decisão...
    """

    texto_completo = """
    O recorrente foi condenado em primeira instância. Alega-se nulidade absoluta do processo,
    afronta à ampla defesa e ocorrência de prescrição penal.
    Requer a reforma da decisão por violação aos princípios constitucionais.
    """

    modelos_por_tipo = {
        "RE": "src/peticionador/modelos/contrarrazoes_re.txt",
        "REsp": "src/peticionador/modelos/contrarrazoes_resp.txt"
    }

    modelo_padrao = "src/peticionador/modelos/contrarrazoes_resp.txt"

    modelos_reutilizaveis = [
        "prescrição penal",
        "nulidade processual"
    ]

    resultado = processar_peticao(
        primeira_pagina,
        texto_completo,
        modelos_reutilizaveis,
        modelos_por_tipo,
        modelo_padrao
    )

    estado = resultado["estado"]
    arquivos = resultado["arquivos"]

    print("====== Resultado Final ======")
    print(f"Recorrente: {estado.estrutura_base.get('recorrente')}")
    print(f"Tipo de Recurso: {estado.estrutura_base.get('tipo_recurso')}")
    print("\nResumo:")
    print(estado.resumo)
    print("\nModelos já usados:")
    print(estado.modelos_usados)
    print("\nArgumentos sugeridos:")
    print(estado.argumentos_reutilizaveis)
    print("\nArquivos gerados:")
    print(arquivos)


if __name__ == "__main__":
    main()
