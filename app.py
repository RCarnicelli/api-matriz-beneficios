from flask import Flask, request, jsonify
from typing import List, Dict

app = Flask(__name__)

# ---------- Utilidades ----------
PILLARS = ["funcionais", "experienciais", "sociais", "expressao", "realizacao"]

SUBS = {
    "funcionais": ["segurança", "controle", "desempenho", "conveniência", "otimização", "cuidado"],
    "experienciais": ["hedonismo", "convivio", "transformacionais", "criadoras", "capacitadoras", "sensoriais"],
    "sociais": ["superioridade", "conformidade", "tribais", "reconhecimento", "qualificação", "conexão"],
    "expressao": ["personalidade", "individualidade", "independência", "vanguarda", "engajamento", "visao_de_mundo"],
    "realizacao": ["unicidade", "inspiração", "transcendência", "vitalidade", "realização", "auto-afirmação"]
}

# palavras-chave simples -> (pillar, sub)
KEYWORDS = [
    # funcionais
    (["entrega", "rapida", "rápida", "tempo", "eta", "rastreamento"], ("funcionais", "controle")),
    (["pagamento", "pix", "cartão", "cartao", "whatsapp", "app", "pedido"], ("funcionais", "conveniência")),
    (["qualidade", "fermentação", "fermentacao", "massa", "forno", "insumo"], ("funcionais", "desempenho")),
    # experienciais
    (["sabor", "autorais", "alho negro", "gorgonzola", "textura"], ("experienciais", "sensoriais")),
    (["evento", "noite temática", "experiência", "experiencia"], ("experienciais", "hedonismo")),
    # sociais
    (["hashtag", "ugc", "comunidade", "postar", "mural"], ("sociais", "conexão")),
    (["prêmio", "premio", "selo", "imprensa", "press", "ranking"], ("sociais", "reconhecimento")),
    # expressão
    (["manifesto", "valores", "propósito", "proposito"], ("expressao", "visao_de_mundo")),
    (["reels", "conteúdo", "conteudo", "editorial", "série", "serie"], ("expressao", "engajamento")),
    # realização
    (["leve", "leveza", "digestível", "digestivel", "saudável", "saudavel"], ("realizacao", "vitalidade")),
]

def auto_classify(diff: str):
    d = (diff or "").lower()
    for keys, pair in KEYWORDS:
        if any(k in d for k in keys):
            return pair
    # fallback seguro
    return ("funcionais", "conveniência")

def infer_usage_and_relevance(differential: str):
    """
    Heurística simples:
    - Se tiver 'novo', 'lançar', 'implementar' -> nao_tem
    - Se tiver 'temos', 'já', 'ja', 'sempre' -> temos_muito
    - Caso contrário -> temos_pouco
    Relevância:
    - se reconhecido como 'autorais', 'manifesto', 'selo' -> pode_gerar_muito_valor
    - se 'entrega', 'pagamento' -> gera_valor
    - senão -> um_pouco_comum
    """
    txt = (differential or "").lower()
    if any(w in txt for w in ["novo", "lançar", "lancar", "implementar", "criar"]):
        usage = "nao_tem"
    elif any(w in txt for w in ["temos", "já", "ja", "sempre", "oferecemos"]):
        usage = "temos_muito"
    else:
        usage = "temos_pouco"

    if any(w in txt for w in ["autorais", "manifesto", "selo", "prêmio", "premio", "imprensa", "ugc", "hashtag"]):
        rel = "pode_gerar_muito_valor"
    elif any(w in txt for w in ["entrega", "pagamento", "pedido", "app", "whatsapp"]):
        rel = "gera_valor"
    else:
        rel = "um_pouco_comum"

    # recomendação básica
    rec = "manter"
    if usage == "nao_tem":
        rec = "desenvolver" if rel in ["gera_valor", "pode_gerar_muito_valor"] else "ignorar"
    elif usage == "temos_pouco":
        rec = "aprimorar" if rel != "muito_comum" else "dar_clareza"
    elif usage == "temos_muito":
        rec = "proteger" if rel == "pode_gerar_muito_valor" else ("manter" if rel == "gera_valor" else "reduzir")

    priority = "alta" if rec in ["proteger", "desenvolver"] else ("media" if rec in ["aprimorar", "manter"] else "baixa")

    # normalizar enum
    if rec == "ignorar": rec = "reduzir"
    if rec == "dar_clareza": rec = "manter"

    return usage, rel, rec, priority

def map_decision(recommendation: str):
    """
    Mapeamento para a Matriz de Decisão Estratégica (transcrita):
    """
    rec = (recommendation or "").lower()
    if rec == "proteger":
        return "Protecao", "Planeje manutenção forte e evite comoditização (séries, naming, calendário)."
    if rec == "aprimorar":
        return "Reforco", "Com pouco esforço, capture mais resultado; dê destaque antes de virar commodity."
    if rec == "desenvolver":
        return "Prioridade_de_Construcao", "Maior potencial de diferenciação agora; planeje e implemente já."
    if rec == "manter":
        return "Manutencao", "É tático/obrigatório: mantenha com qualidade e foque no que diferencia."
    if rec == "reduzir":
        return "Minimo_Esforco", "Se for commodity, mantenha com mínimo esforço ou elimine."
    if rec == "eliminar":
        return "Eliminar", "Não obrigatório e comoditizado: elimine para abrir espaço ao que importa."
    # fallback
    return "Manutencao", "Mantenha até termos dados melhores."

# ---------- HEALTH ----------
@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "brand-matrix", "version": "1.0.0"}), 200

# ---------- M1 ----------
@app.post("/m1-beneficios")
def m1_beneficios():
    """
    Input: { brand, scope, inputs: { raw_text?, differentials?: [str] } }
    Output: { brand, stage: benefit_matrix, attributes: [{pillar, sub_benefit, differential, evidence}] }
    """
    body = request.get_json(force=True, silent=True) or {}
    brand = body.get("brand", "")
    scope = body.get("scope", "")
    diffs: List[str] = []
    inputs = body.get("inputs") or {}
    diffs = inputs.get("differentials") or body.get("differentials") or []

    attributes = []
    for d in diffs:
        pillar, sub = auto_classify(d)
        attributes.append({
            "pillar": pillar,
            "sub_benefit": sub,
            "differential": d,
            "evidence": f"Classificado automaticamente por palavras-chave no escopo: {scope}"
        })

    return jsonify({"brand": brand, "stage": "benefit_matrix", "attributes": attributes}), 200

# ---------- M2 ----------
@app.post("/m2-diferenciais")
def m2_diferenciais():
    """
    Input: { brand, attributes: [{differential, pillar, sub_benefit?}] }  ou { brand, differentials:[...] }
    Output: { brand, stage: diferenciais_matrix, differentials:[{differential, usage_level, relevance_level, recommendation, priority}] }
    """
    body = request.get_json(force=True, silent=True) or {}
    brand = body.get("brand", "")
    attrs = body.get("attributes") or []
    if not attrs and body.get("differentials"):
        attrs = [{"differential": d, "pillar": auto_classify(d)[0]} for d in body["differentials"]]

    out = []
    for a in attrs:
        d = a.get("differential")
        usage = a.get("usage_level")
        rel = a.get("relevance_level")
        rec = a.get("recommendation")
        pr = a.get("priority")
        if not (usage and rel and rec and pr):
            usage, rel, rec, pr = infer_usage_and_relevance(d)
        out.append({
            "differential": d,
            "usage_level": usage,
            "relevance_level": rel,
            "recommendation": rec,
            "priority": pr
        })
    return jsonify({"brand": brand, "stage": "diferenciais_matrix", "differentials": out}), 200

# ---------- M3 ----------
@app.post("/m3-decisao")
def m3_decisao():
    """
    Input: { brand, differentials: [{differential, recommendation}] }
    Output: { brand, stage: decisao_estrategica, decisions: [{differential, quadrant, argument}] }
    """
    body = request.get_json(force=True, silent=True) or {}
    brand = body.get("brand", "")
    diffs = body.get("differentials") or []
    decisions = []
    for d in diffs:
        name = d.get("differential")
        rec = d.get("recommendation", "manter")
        quadrant, arg = map_decision(rec)
        decisions.append({"differential": name, "quadrant": quadrant, "argument": arg})
    return jsonify({"brand": brand, "stage": "decisao_estrategica", "decisions": decisions}), 200

# ---------- M4 ----------
@app.post("/m4-detalhamento")
def m4_detalhamento():
    """
    Input: { brand, items: [{differential, ...}] }  (ou decisions/differentials)
    Output: { brand, stage: detalhamento, detailed:[{...}] }
    """
    body = request.get_json(force=True, silent=True) or {}
    brand = body.get("brand", "")
    items = body.get("items") or body.get("detailed") or []

    # Se vierem só os nomes (ex. da M3), gerar esqueleto
    if not items and body.get("decisions"):
        items = [{"differential": d.get("differential", "")} for d in body["decisions"]]

    detailed = []
    for it in items:
        name = it.get("differential", "")
        detailed.append({
            "differential": name,
            "porque": it.get("porque") or "Por que isso é relevante para a marca?",
            "racional": it.get("racional") or "Prova objetiva / argumento lógico.",
            "emocional": it.get("emocional") or "Sensação/memória que queremos provocar.",
            "tangivel": it.get("tangivel") or "O que será entregável e visível.",
            "intangivel": it.get("intangivel") or "Associações e significados.",
            "positivo": it.get("positivo") or "Oportunidades.",
            "negativo": it.get("negativo") or "Riscos a monitorar."
        })
    return jsonify({"brand": brand, "stage": "detalhamento", "detailed": detailed}), 200

# ---------- M5 ----------
@app.post("/m5-planejamento")
def m5_planejamento():
    """
    Input: { brand, plan: [...] }  ou { brand, detailed:[...] }  -> gera plano base de comunicação
    Output: { brand, stage: planejamento, plan:[{dizer, mostrar, fazer}] }
    """
    body = request.get_json(force=True, silent=True) or {}
    brand = body.get("brand", "")
    plan = body.get("plan")
    if not plan:
        # montar a partir do detalhamento
        detailed = body.get("detailed") or body.get("items") or []
        plan = []
        for d in detailed:
            name = d.get("differential", "Diferencial")
            plan.append({
                "differential": name,
                "dizer": {
                    "o_que": f"Mensagem principal sobre {name}",
                    "onde": ["site", "instagram", "cardapio"],
                    "como": "tom confiante e simples"
                },
                "mostrar": {
                    "o_que": f"Provas visuais de {name}",
                    "onde": ["reels", "stories", "landing"],
                    "como": "close, bastidores, social proof"
                },
                "fazer": {
                    "o_que": f"Ação prática para ativar {name}",
                    "onde": ["salão", "delivery", "eventos"],
                    "como": "rituais, edições limitadas, métricas claras"
                }
            })
    return jsonify({"brand": brand, "stage": "planejamento", "plan": plan}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
