from flask import Flask, request, jsonify

app = Flask(__name__)

# Healthcheck
@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "brand-matrix"}), 200


# =======================
# M1 – Classificação de Benefícios
# =======================
@app.post("/m1-beneficios")
def m1():
    data = request.get_json()
    return jsonify({
        "stage": "M1",
        "received": data,
        "classified": "Aqui o GPT irá classificar benefícios em: Funcional, Experiencial, Social."
    }), 200


# =======================
# M2 – Diferenciais & Benefícios (uso × relevância)
# =======================
@app.post("/m2-diferenciais")
def m2():
    data = request.get_json()
    return jsonify({
        "stage": "M2",
        "received": data,
        "classified": "Aqui o GPT irá avaliar uso × relevância de cada benefício."
    }), 200


# =======================
# M3 – Decisão Estratégica
# =======================
@app.post("/m3-decisao")
def m3():
    data = request.get_json()
    return jsonify({
        "stage": "M3",
        "received": data,
        "classified": "Aqui o GPT recomenda manter, melhorar ou implementar benefícios."
    }), 200


# =======================
# M4 – Detalhamento de Benefícios
# =======================
@app.post("/m4-detalhamento")
def m4():
    data = request.get_json()
    return jsonify({
        "stage": "M4",
        "received": data,
        "classified": "Aqui o GPT detalha cada benefício em camadas racionais e emocionais."
    }), 200


# =======================
# M5 – Priorização Final
# =======================
@app.post("/m5-priorizacao")
def m5():
    data = request.get_json()
    return jsonify({
        "stage": "M5",
        "received": data,
        "classified": "Aqui o GPT prioriza os benefícios em ordem estratégica final."
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
