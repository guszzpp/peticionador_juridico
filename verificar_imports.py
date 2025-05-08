import os
import re


def corrigir_asserts_em_multiplas_pastas(pastas: list):
    arquivos_modificados = []

    for pasta in pastas:
        for root, _, files in os.walk(pasta):
            for file in files:
                if file.endswith(".py"):
                    caminho_arquivo = os.path.join(root, file)
                    with open(caminho_arquivo, encoding="utf-8") as f:
                        linhas = f.readlines()

                    novas_linhas = []
                    skip_next = False
                    alterado = False

                    for i in range(len(linhas)):
                        linha = linhas[i]

                        # Detectar assert multi-linha com # nosec B101 na linha errada
                        if (
                            "assert" in linha
                            and "# nosec B101" in linha
                            and i + 1 < len(linhas)
                            and linhas[i + 1].strip().startswith("(")
                        ):
                            linha_assert = linhas[i].split("#")[0].strip()
                            linha_seg = linhas[i + 1].strip().lstrip("() ")
                            linha_final = f"{linha_assert} {linha_seg}  # nosec B101\n"
                            novas_linhas.append(linha_final)
                            skip_next = True
                            alterado = True
                            continue

                        elif skip_next:
                            skip_next = False
                            continue

                        novas_linhas.append(linha)

                    # Corrigir variáveis ambíguas 'l'
                    novas_linhas_corrigidas = []
                    for linha in novas_linhas:
                        nova = re.sub(r"\bl\b", "linha", linha)
                        if nova != linha:
                            alterado = True
                        novas_linhas_corrigidas.append(nova)

                    novas_linhas = novas_linhas_corrigidas

                    # Remover imports de typing desnecessários
                    linhas_finais = []
                    for linha in novas_linhas:
                        if re.match(
                            r"^from typing import (Any|Optional)", linha.strip()
                        ):
                            alterado = True
                            continue
                        linhas_finais.append(linha)

                    if alterado:
                        with open(caminho_arquivo, "w", encoding="utf-8") as f:
                            f.writelines(linhas_finais)
                        arquivos_modificados.append(caminho_arquivo)

    return arquivos_modificados


if __name__ == "__main__":
    pastas = ["testes", "scripts", "src"]
    modificados = corrigir_asserts_em_multiplas_pastas(pastas)
    print("\n✅ Arquivos modificados:")
    for path in modificados:
        print(f" - {path}")
    if not modificados:
        print("Nenhuma modificação foi necessária.")
