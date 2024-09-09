import qrcode
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import locale
import socket
from io import BytesIO
import base64
import os
import webbrowser
from tkinter import Tk, Label
from PIL import Image, ImageTk
import threading

locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')

app = Flask(__name__)

placar = {
    "quem-saca": 1,
    "pontos1": 0,
    "pontos2": 0,
    "set1": 0,
    "set2": 0,
    "cronometro": 0,
    "qr-code": 0
}

resultado = {
    "-1": {
    "ganhador": 1,
    "perdedor": 2,
    "nome-ganhador": "undefined",
    "nome-perdedor": "undefined",
    "sets-ganhador": 2,
    "sets-perdedor": 1
    }
}

partida = {
    "nome1": "undefined",
    "nome2": "undefined",
    "numero1": 2,
    "numero2": 1,
    "rodada": -1,
    "partida": -1,
    "situacao": 0
}
data_hoje_formatada = datetime.now().strftime('%d-%b-%y').lower()
data_campeonato = '17-ago-24'

@app.route('/')
def tabela_leitura():
    return render_template('tabelaLeitura.html', placar=placar)

@app.route('/placar')
def funcao_placar():
    rota = "/links"
    qr_code_image = generate_qr_rota_str(rota)
    rota_servidor = f"{get_rota_servidor()}{rota}"
    
    return render_template('placar.html', placar=placar)

@app.route('/campeonatos')
def campeonatos():
    campeonatos_index_path = 'json/campeonatos/campeonatos.json'
    
    if os.path.exists(campeonatos_index_path):
        with open(campeonatos_index_path, 'r') as f:
            campeonatos_index = json.load(f)
    else:
        campeonatos_index = {}
    return render_template('campeonatos.html', campeonatos_index=campeonatos_index)

@app.route('/tabela')
def tabela():
    return render_template('tabela.html', placar=placar)

@app.route('/tabela_v2')
def tabela_v2():
    jogadores_path = 'json/jogadores.json'
    # Verifica se o arquivo existe antes de tentar abri-lo
    if os.path.exists(jogadores_path):
        with open(jogadores_path, 'r') as f:
            jogadores = json.load(f)
    else:
        jogadores = {}
    
    resultados_path = 'json/resultados.json'
    if os.path.exists(resultados_path):
        with open(resultados_path, 'r') as f:
            resultados = json.load(f)
    else:
        resultados = {}
    return render_template('tabela_v2.html', resultados=resultados, placar_atual=placar, partida_atual=partida, jogadores=jogadores['jogadores'])

@app.route('/controle')
def controle():
    return render_template('controle.html', placar=placar, partida=partida)

@app.route('/jogadores')
def jogadores():
    return render_template('jogadores.html')

@app.route('/links')
def links():
    # Dicionário de links de HTMLs
    html_links = {
        "tabela": "/tabela",
        "tabela versão 2 (em construção)": "/tabela_v2",
        "placar": "/placar",
        "controle": "/controle",
        "campeonatos realizados": "/campeonatos"
    }
    keys = list(html_links.keys())
    qr_codes = {}
    for key in keys:
        qr_codes[f"{key}"] = generate_qr_rota_str(html_links[f"{key}"])
    return render_template('links.html', links=html_links, qr_codes=qr_codes)


@app.route('/post-placar', methods=['POST'])
def post_placar():
    data = request.json
    global placar
    placar = data
    if placar['qr-code'] == 1:
        show_qr_code_in_thread(generate_qr_rota("/links"), "/links", 10000)
    return jsonify(placar)

@app.route('/get-placar', methods=['GET'])
def get_placar():
    global placar
    return jsonify(placar)

@app.route('/get-partida', methods=['GET'])
def get_partida():
    global partida
    return jsonify(partida)

@app.route('/post-jogadores', methods=['POST'])
def post_jogadores():
    data = request.json
    atualiza_quantidade_jogadores_em_resultados(data['quantidade-jogadores'])
    with open('json/jogadores.json', 'w') as f:
        json.dump(data, f, indent=2)

    
    return jsonify({"status": "success", "data": data})

def atualiza_quantidade_jogadores_em_resultados(quantidade_jogadores):
    resultados_path = 'json/resultados.json'
    if os.path.exists(resultados_path):
        with open(resultados_path, 'r') as f:
            resultados = json.load(f)
    else:
        resultados = {}
    resultados.update({'quantidade-jogadores': quantidade_jogadores, 'data': data_hoje_formatada})
    with open(resultados_path, 'w') as f:
        json.dump(resultados, f, indent=2)
        
@app.route('/salvar-campeonato', methods=['POST'])
def salvar_campeonato():
    data = request.json
    campeonato_path = f'json/campeonatos/{data_hoje_formatada}.json'
    with open(campeonato_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    campeonatos_index_path = 'json/campeonatos/campeonatos.json'
    if os.path.exists(campeonatos_index_path):
        with open(campeonatos_index_path, 'r') as f:
            campeonatos_index = json.load(f)
    else:
        campeonatos_index = {}

    max_index = len(campeonatos_index)
    campeonatos_index[str(max_index + 1)] = data_hoje_formatada

    with open(campeonatos_index_path, 'w') as f:
        json.dump(campeonatos_index, f, indent=2)
    
    return jsonify({"status": "success", "data": "aa"})

@app.route('/post-partida', methods=['POST'])
def post_partida():
    data = request.json
    global partida 
    partida = data
    return jsonify({"status": "success", "placar": placar})

@app.route('/post-data-campeonato', methods=['POST'])
def post_data_campeonato():
    data = request.json
    global data_campeonato
    data_campeonato = data['data']
    return jsonify({"status": "success"})

@app.route('/campeonato-salvo')
def campeonato_salvo():
    campeonato_path = f'json/campeonatos/{data_campeonato}.json'
    
    # Verifica se o arquivo existe antes de tentar abri-lo
    if os.path.exists(campeonato_path):
        with open(campeonato_path, 'r') as f:
            dados_campeonato = json.load(f)
    else:
        dados_campeonato = {}
    return render_template('campeonato.html', dados_campeonato=dados_campeonato)

@app.route('/reiniciar-campeonato', methods=['POST'])
def reiniciar_campeonato():
    if request.method == 'POST':
        # Atualiza o arquivo JSON com um objeto vazio
        try:
            with open('json/resultados.json', 'w') as file:
                json.dump({}, file)
            return jsonify({'message': 'Campeonato reiniciado com sucesso!'}), 200
        except Exception as e:
            print(f"Erro ao atualizar o arquivo JSON: {e}")
            return jsonify({'message': 'Erro ao reiniciar o campeonato'}), 500

@app.route('/get-partidas', methods=['GET'])
def get_partidas():
    partidas_path = 'json/partidas.json'
    
    # Verifica se o arquivo existe antes de tentar abri-lo
    if os.path.exists(partidas_path):
        with open(partidas_path, 'r') as f:
            partidas = json.load(f)
    else:
        partidas = {}

    return jsonify(partidas)

@app.route('/get-jogadores', methods=['GET'])
def get_jogadores():
    jogadores_path = 'json/jogadores.json'
    
    # Verifica se o arquivo existe antes de tentar abri-lo
    if os.path.exists(jogadores_path):
        with open(jogadores_path, 'r') as f:
            jogadores = json.load(f)
    else:
        jogadores = {}

    return jsonify(jogadores)

@app.route('/post-resultado', methods=['POST'])
def post_resultado():
    data = request.json
    
    resultados_path = 'json/resultados.json'
    
    if os.path.exists(resultados_path):
        with open(resultados_path, 'r') as f:
            resultados = json.load(f)
    else:
        resultados = {}

    resultados.update(data)

    with open(resultados_path, 'w') as f:
        json.dump(resultados, f, indent=2)
    
    partida['partida'] = -1
    return jsonify({"status": "success", "resultados": resultados})




@app.route('/get-tabela', methods=['GET'])
def get_tabela_campeonato():
    jogadores_path = 'json/jogadores.json'
    resultados_path = 'json/resultados.json'
    
    if os.path.exists(jogadores_path):
        with open(jogadores_path, 'r') as f:
            jogadores = json.load(f)
    else:
        jogadores = []
    if os.path.exists(resultados_path):
        with open(resultados_path, 'r') as f:
            resultados = json.load(f)
    else:
        resultados = []

    tabela = {
        'jogadores': jogadores,
        'resultados': resultados
    }
    return jsonify(tabela)

def get_rota_servidor():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    site_url = f"http://{local_ip}:5000"
    return site_url

def generate_qr_rota(rota = "/"):
    site_url = f"{get_rota_servidor()}{rota}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2
    )
    qr.add_data(site_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def generate_qr_rota_str(rota = "/"):
    img = generate_qr_rota(rota)
    buffered = BytesIO()
    img.save(buffered, format="png")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

def show_qr_code(qr, title, duration):
    root = Tk()
    root.title(title)
    
    qr_image = ImageTk.PhotoImage(qr)
    
    label = Label(root, image=qr_image)
    label.pack()
    
    window_width = qr_image.width()
    window_height = qr_image.height()

    screen_width = root.winfo_screenwidth()

    position_x = int((screen_width / 2) - (window_width / 2))
    position_y = 20

    root.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    root.after(duration, root.destroy)
    root.mainloop()

def show_qr_code_in_thread(qr, title="QR Code", duration=10000):
    thread = threading.Thread(target=show_qr_code, args=(qr, title, duration))
    thread.start()

def abrir_pagina_web(rota = "/"):
    url = f"{get_rota_servidor()}{rota}"
    webbrowser.open(url)

def main(): 
    app.run(host='0.0.0.0', debug=True, threaded=True)

if __name__ == '__main__':
    main()