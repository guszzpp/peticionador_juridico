from peticionador.servicos.seletor_modelo import selecionar_modelo


def test_seletor_modelo_funciona():
    modelos = {
        "RE": "modelos/contrarrazoes_re.txt",
        "REsp": "modelos/contrarrazoes_resp.txt",
    }
    padrao = "modelos/default.txt"


modelos = {
    "RE": "modelos/contrarrazoes_re.txt",
    "REsp": "modelos/contrarrazoes_resp.txt",
    "Agravo": "modelos/default.txt",
}
padrao = "modelos/default.txt"

assert (
    selecionar_modelo("RE", modelos, padrao) == "modelos/contrarrazoes_re.txt"
)  # nosec B101
assert (
    selecionar_modelo("REsp", modelos, padrao) == "modelos/contrarrazoes_resp.txt"
)  # nosec B101
assert (
    selecionar_modelo("Agravo", modelos, padrao) == "modelos/default.txt"
)  # nosec B101
