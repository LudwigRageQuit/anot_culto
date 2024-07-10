from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import logging
import atexit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anotacoes_culto.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Definir o modelo de Anotação
class Anotacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10), nullable=False)
    tema = db.Column(db.String(100), nullable=False)
    passagem_biblica = db.Column(db.String(200), nullable=False)
    anotacoes_culto = db.Column(db.Text, nullable=False)
    devocional = db.Column(db.Text, nullable=False)

# Criar o banco de dados
@app.before_first_request
def criar_banco():
    db.create_all()

@app.route('/')
def index():
    anotacoes = Anotacao.query.all()
    return render_template('index.html', anotacoes=anotacoes)

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

        anotacao = Anotacao(
            data=data,
            tema=tema,
            passagem_biblica=passagem_biblica,
            anotacoes_culto=anotacoes_culto,
            devocional=devocional
        )
        
        db.session.add(anotacao)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('adicionar.html')

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    anotacao = Anotacao.query.get(id)
    if anotacao:
        db.session.delete(anotacao)
        db.session.commit()
        logging.info(f"Anotação com ID {id} deletada com sucesso.")
    else:
        logging.error(f"Anotação com ID {id} não encontrada para exclusão.")
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

if __name__ == '__main__':
    app.run(debug=True)
