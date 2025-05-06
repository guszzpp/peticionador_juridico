from peticionador.agentes.agente_gemini import verificar_extracao_gemini

texto_pagina = """
RECORRENTE: Maria José
Trata-se de Mandado de Segurança impetrado contra ato de...
"""

dados = {
    "recorrente": "Não identificado",
    "tipo_recurso": "Indeterminado"
}

resultado = verificar_extracao_gemini(texto_pagina, dados)
print(resultado)
