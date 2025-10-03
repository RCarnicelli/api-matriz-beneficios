from flask import Flask, request, jsonify

app = Flask(__name__)

# M1 - Classificação de Benefícios
@app.route("/m1-beneficios", methods=["POST"])
def m1():
    data = request.get_json()
    return jsonify({
        "stage": "M1",
        "received": data,
        "classified": "Aqui o GPT irá classificar pilares/sub-benefícios"
    }), 200

# M2 - Diferenciais & Benefícios
@app.route("/m2-diferenciais", methods=["POST"])
def m2():
    data = request.get_json()
    return jsonify({
        "stage": "M2",
        "received": data,
        "classified": "Aqui entra uso x relevância"
    }), 200

# M3 - Decisão Estratégica
@app.route("/m3-decisao", methods=["POST"])
def m3():
    data = request.get_json()
    return jsonify({
        "stage": "M3",
        "received": data,
        "classified": "Aqui entram recomendações de manter/melhorar/implementar"
    }), 200

# M4 - Detalhamento
@app.route("/m4-detalhamento", methods=["POST"])
def m4():
    data = request.get_json()
    return jsonify({
        "stage": "M4",
        "received": data,
        "classified": "Aqui entra detalhamento racional/emocional etc."
    }), 200

# M5 - Planejamento de Comunicação
@app.route("/m5-planejamento", methods=["POST"])
def m5():
    data = request.get_json()
    return jsonify({
        "stage": "M5",
        "received": data,
        "classified": "Aqui entra Dizer/Mostrar/Fazer"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
