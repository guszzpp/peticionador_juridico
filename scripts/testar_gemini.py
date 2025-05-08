from src.peticionador.servicos.integrador_gemini import ClienteGemini

resposta = ClienteGemini().resumir("Resuma brevemente a importância do controle ministerial sobre parcerias com OSCs.")
print(resposta)
