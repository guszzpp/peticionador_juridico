import sys
import os
from pathlib import Path

# Adicionar o diretório 'src' ao sys.path
projeto_dir = Path(__file__).parent.parent
src_dir = os.path.join(projeto_dir, 'src')
sys.path.insert(0, src_dir)

# Agora importa a aplicação Flask
from peticionador.controladores.interface_flask import app

if __name__ == '__main__':
    # Iniciar o servidor Flask
    app.run(debug=True, host='0.0.0.0', port=5000)