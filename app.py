import json
import os
import shutil
import atexit
from flask import Flask, render_template, request, redirect, url_for, abort
from dotenv import load_dotenv
import dropbox
import logging
from datetime import datetime

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter o token de acesso do Dropbox a partir das variáveis de ambiente
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
if not DROPBOX_ACCESS_TOKEN:
    raise ValueError("O token de acesso do Dropbox não está definido. Verifique a configuração.")

# Inicializar o cliente do Dropbox
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Arquivo JSON onde as anotações serão armazenadas
ANOTACOES_FILE = "anotacoes_culto.json"
DROPBOX_FILE_PATH = '/anotacoes_culto.json'

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Funções de sincronização com Dropbox
def upload_to_dropbox(local_file_path, dropbox_path):
    try:
        with open(local_file_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        logging.info("Arquivo enviado com sucesso para o Dropbox.")
    except Exception as e:
        logging.error(f"Erro ao enviar o arquivo para o Dropbox: {e}")

def download_from_dropbox(dropbox_path, local_file_path):
    try:
        dbx.files_download_to_file(local_file_path, dropbox_path)
        logging.info("Arquivo baixado com sucesso do Dropbox.")
    except Exception as e:
        logging.error(f"Erro ao baixar o arquivo do Dropbox: {e}")

# Carregar anotações de um arquivo JSON
def carregar_anotacoes():
    if not os.path.exists(ANOTACOES_FILE):
        download_from_dropbox(DROPBOX_FILE_PATH, ANOTACOES_FILE)
    try:
        with open(ANOTACOES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error("Erro ao decodificar o arquivo JSON.")
        return []

# Salvar anotações em um arquivo JSON
def salvar_anotacoes(anotacoes):
    try:
        with open(ANOTACOES_FILE, "w", encoding="utf-8") as f:
            json.dump(anotacoes, f, ensure_ascii=False, indent=4)
        upload_to_dropbox(ANOTACOES_FILE, DROPBOX_FILE_PATH)
    except IOError:
        logging.error("Erro ao salvar o arquivo JSON.")

# Criar um backup do arquivo JSON
def criar_backup():
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"anotacoes_culto_backup_{data_hora}.json"
    try:
        shutil.copy(ANOTACOES_FILE, backup_file)
        logging.info(f"Backup criado com sucesso: {backup_file}")
    except IOError as e:
        logging.error(f"Erro ao criar backup: {e}")

# Registrar função de finalização para criar backup
atexit.register(criar_backup)

app = Flask(__name__)

@app.route('/')
def index():
    anotacoes = carregar_anotacoes()
    return render_template('index.html', anotacoes=anotacoes, enumerate=enumerate)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        data = request.form.get('data', '').strip()
        tema = request.form.get('tema', '').strip()
        passagem_biblica = request.form.get('passagem_biblica', '').strip()
        anotacoes_culto = request.form.get('anotacoes_culto', '').strip()
        devocional = request.form.get('devocional', '').strip()

        # Validação dos dados
        if not (data and tema and passagem_biblica and anotacoes_culto and devocional):
            return "Todos os campos são obrigatórios!", 400

        # Verificar formato da data (simples)
        import re
        if not re.match(r"\d{2}/\d{2}/\d{4}", data):
            return "Formato de data inválido. Use DD/MM/AAAA.", 400

        anotacao = {
            "data": data,
            "tema": tema,
            "passagem_biblica": passagem_biblica,
            "anotacoes_culto": anotacoes_culto,
            "devocional": devocional
        }
        
        anotacoes = carregar_anotacoes()
        anotacoes.append(anotacao)
        salvar_anotacoes(anotacoes)
        
        return redirect(url_for('index'))
    
    return render_template('adicionar.html')

@app.route('/deletar/<int:index>', methods=['POST'])
def deletar(index):
    anotacoes = carregar_anotacoes()
    if 0 <= index < len(anotacoes):
        anotacoes.pop(index)
        salvar_anotacoes(anotacoes)
        logging.info(f"Anotação no índice {index} deletada com sucesso.")
    else:
        logging.error(f"Índice {index} inválido para exclusão.")
        abort(404)
    return redirect(url_for('index'))

def cruz_ascii():
    cruz = """
      +     
      |     
  +---+---+
      |     
      |     
    """
    return cruz

@app.route('/sair')
def sair():
    cruz = cruz_ascii()
    mensagem = "Deus primeiro me amou!"
    return render_template('sair.html', cruz=cruz, mensagem=mensagem)

def cli_adicionar(data, tema, passagem_biblica, anotacoes_culto, devocional):
    if not (data and tema and passagem_biblica and anotacoes_culto and devocional):
        print("Todos os campos são obrigatórios.")
        return

    import re
    if not re.match(r"\d{2}/\d{2}/\d{4}", data):
        print("Formato de data inválido. Use DD/MM/AAAA.")
        return

    anotacao = {
        "data": data,
        "tema": tema,
        "passagem_biblica": passagem_biblica,
        "anotacoes_culto": anotacoes_culto,
        "devocional": devocional
    }
    
    anotacoes = carregar_anotacoes()
    anotacoes.append(anotacao)
    salvar_anotacoes(anotacoes)
    print("Anotação adicionada com sucesso.")

def cli_listar():
    anotacoes = carregar_anotacoes()
    if not anotacoes:
        print("Nenhuma anotação encontrada.")
        return
    for idx, anotacao in enumerate(anotacoes):
        print(f"Anotação {idx + 1}:")
        print(f"  Data: {anotacao['data']}")
        print(f"  Tema: {anotacao['tema']}")
        print(f"  Passagem Bíblica: {anotacao['passagem_biblica']}")
        print(f"  Anotações do Culto: {anotacao['anotacoes_culto']}")
        print(f"  Devocional: {anotacao['devocional']}\n")

def cli_deletar(index):
    anotacoes = carregar_anotacoes()
    if 0 <= index < len(anotacoes):
        anotacoes.pop(index)
        salvar_anotacoes(anotacoes)
        print("Anotação deletada com sucesso.")
    else:
        print("Índice inválido.")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Gerenciador de Anotações de Culto')
    parser.add_argument('--start', action='store_true', help='Inicia o servidor web')
    parser.add_argument('--adicionar', nargs=5, metavar=('DATA', 'TEMA', 'PASSAGEM', 'ANOTACOES', 'DEVOCIONAL'), help='Adiciona uma nova anotação')
    parser.add_argument('--listar', action='store_true', help='Lista todas as anotações')
    parser.add_argument('--deletar', type=int, metavar='ÍNDICE', help='Deleta uma anotação pelo índice')

    args = parser.parse_args()

    if args.start:
        app.run(debug=True)
    elif args.adicionar:
        cli_adicionar(*args.adicionar)
    elif args.listar:
        cli_listar()
    elif args.deletar is not None:
        cli_deletar(args.deletar)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
