from peticionador.modelos.estado_peticao import EstadoPeticao
from peticionador.servicos.gerador_documento import gerar_peca_personalizada


def main():
    estado = EstadoPeticao()
    estado.estrutura_base = {"recorrente": "João da Silva", "tipo_recurso": "Agravo"}
    estado.resumo = (
        "O recorrente busca reforma de decisão proferida pelo Tribunal de Justiça, "
        "alegando nulidades processuais e afronta à ampla defesa."
    )
    estado.argumentos_reutilizaveis = [
        "inexistência de repercussão geral",
        "prescrição penal",
        "nulidade processual",
    ]

    saida = gerar_peca_personalizada(
        estado, modelo_path="src/peticionador/modelos/contrarrazoes_resp.txt"
    )

    print("Arquivos gerados com sucesso:")
    for tipo, caminho in saida.items():
        print(f"{tipo.upper()}: {caminho}")


if __name__ == "__main__":
    main()
