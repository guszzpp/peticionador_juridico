from peticionador.agentes.agente_extrator import extrair_info_roberta


def main():
    exemplos = [
        {
            "descricao": "REsp com menção explícita",
            "texto": "EXCELENTÍSSIMO SENHOR DESEMBARGADOR\nRECORRENTE: Maria da Silva\nRecurso Especial interposto contra acórdão...",
        },
        {
            "descricao": "RE com menção genérica",
            "texto": "RECORRENTE: João Pedro\nO presente extraordinário busca reforma de decisão...",
        },
        {
            "descricao": "Agravo sem especificação",
            "texto": "RECORRENTE: Fulano de Tal\nTrata-se de agravo interno contra decisão monocrática...",
        },
        {
            "descricao": "Texto indefinido",
            "texto": "Petição inicial recebida por esta promotoria para ciência.",
        }
    ]

    for exemplo in exemplos:
        print(f"🧪 Testando: {exemplo['descricao']}")
        resultado = extrair_info_roberta(exemplo["texto"])
        print(f"➡️  Nome: {resultado['recorrente']}")
        print(f"➡️  Tipo de Recurso: {resultado['tipo_recurso']}\n")


if __name__ == "__main__":
    main()
