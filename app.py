from flask import Flask, request, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "brand-matrix", "version": "1.0.0"}), 200

@app.post("/m1-beneficios")
def m1():
    body = request.get_json(silent=True) or {}
    brand = body.get("brand", ""); scope = body.get("scope", "")
    diffs = (body.get("inputs") or {}).get("differentials") or body.get("differentials") or []
    attrs = [{"pillar": "funcionais", "sub_benefit": "conveniência",
              "differential": d, "evidence": f"Recebido via API para {brand} / {scope}"} for d in diffs]
    return jsonify({"brand": brand, "stage": "benefit_matrix", "attributes": attrs}), 200

@app.post("/m2-diferenciais")
def m2():
    body = request.get_json(silent=True) or {}
    brand = body.get("brand", ""); attributes = body.get("attributes") or []
    out = [{"differential": a.get("differential",""),
            "usage_level": a.get("usage_level","temos_pouco"),
            "relevance_level": a.get("relevance_level","gera_valor"),
            "recommendation": a.get("recommendation","aprimorar"),
            "priority": a.get("priority","media")} for a in attributes]
    return jsonify({"brand": brand, "stage": "diferenciais_matrix", "differentials": out}), 200

@app.post("/m3-decisao")
def m3():
    body = request.get_json(silent=True) or {}
    brand = body.get("brand", ""); diffs = body.get("differentials") or []
    decisions = [{"differential": d.get("differential",""),
                  "quadrant": "Prioridade_de_Construcao" if d.get("recommendation")=="desenvolver" else "Protecao",
                  "argument": "Justificativa gerada pelo modelo."} for d in diffs]
    return jsonify({"brand": brand, "stage": "decisao_estrategica", "decisions": decisions}), 200

@app.post("/m4-detalhamento")
def m4():
    body = request.get_json(silent=True) or {}
    brand = body.get("brand", ""); items = body.get("items") or body.get("detailed") or []
    detailed = [{"differential": it.get("differential",""),
                 "porque": it.get("porque","Por que isso é relevante?"),
                 "racional": it.get("racional","Prova objetiva."),
                 "emocional": it.get("emocional","Sensação desejada."),
                 "tangivel": it.get("tangivel","Entrega visível."),
                 "intangivel": it.get("intangivel","Significados."),
                 "positivo": it.get("positivo","Oportunidades."),
                 "negativo": it.get("negativo","Riscos.")} for it in items]
    return jsonify({"brand": brand, "stage": "detalhamento", "detailed": detailed}), 200

@app.post("/m5-planejamento")
def m5():
    body = request.get_json(silent=True) or {}
    brand = body.get("brand", ""); detailed = body.get("detailed") or []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
