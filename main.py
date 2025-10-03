from flask import Flask, request, jsonify
from collections import defaultdict
from typing import List, Dict, Tuple

app = Flask(__name__)

# =========================
# Constantes e utilidades
# =========================
PILLARS = {
    "funcionais": ["segurança","controle","desempenho","conveniência","otimização","cuidado"],
    "experienciais": ["hedonismo","convivio","transformacionais","criadoras","capacitadoras","sensoriais"],
    "sociais": ["superioridade","conformidade","tribais","reconhecimento","qualificação","conexão"],
    "expressao": ["personalidade","individualidade","independência","vanguarda","engajamento","visao_de_mundo"],
    "realizacao": ["unicidade","inspiração","transcendência","vitalidade","realização","auto-afirmação"],
}

# Palavras-chave simplificadas para classificar M1
M1_KEYWORDS = [
    # FUNCIONAIS
    (["whatsapp","app","pedido","pagamento","pix","cartão","cartao","todos os dias",
      "semi-pronta","semipronta","pizza store","entrega rápida","delivery rápido","varios meios de pagamento","muitos meios de pagamento"],
     ("funcionais","conveniência")),
    (["rastreamento","status","avisamos","a caminho","acompanhe","notificação"],
     ("funcionais","controle")),
    (["qualidade","massa","forno","fermentação","processo","padrão","padrao","insumos"],
     ("funcionais","desempenho")),
    (["pet friendly","pet-friendly","petfriendly"], ("funcionais","cuidado")),

    # EXPERIENCIAIS
    (["evento","eventos","serviço de eventos","levamos a experiência","no seu evento",
      "preparadas na hora","ao vivo"],
     ("experienciais","capacitadoras")),
    (["sabor","ingrediente","mozzarella de búfala","alho negro","pera","gorgonzola","pepperoni","textura","aroma"],
     ("experienciais","sensoriais")),
    (["experiência única","inesquecível","momento inesquecível","prazer"],
     ("experienciais","hedonismo")),

    # SOCIAIS
    (["mais desejada","prêmio","premio","selo","imprensa","matéria","ranking","destaque"],
     ("sociais","reconhecimento")),
    (["memória","memorável","compartilhar","comunidade","hashtag","ugc"],
     ("sociais","conexão")),

    # EXPRESSÃO
    (["reels","conteúdo","conteudo","promoção","siga o perfil","siga-nos","seguir"],
     ("expressao","engajamento")),
    (["manifesto","posicionamento","visão de mundo","visao de mundo","proposito","propósito"],
     ("expressao","visao_de_mundo")),

    # REALIZAÇÃO
    (["massa leve","levíssima","digestível","saudável","leveza"],
     ("realizacao","vitalidade")),
    (["experiência","experiencia","memória","memoria","família","amigos","inspiração","inspirador"],
     ("realizacao","inspiração")),
    (["secreta","exclusiva","unicidade","bairro charmoso","surpreendentes","surpreendente"],
     ("realizacao","unicidade")),
]

def classify_snippet(text: str) -> Tuple[str, str]:
    t = (text or "").lower()
    for keys, tag in M1_KEYWORDS:
        if any(k in t for k in keys):
            return tag
    return ("funcionais","conveniência")  # fallback conservador

def ensure(val, default):  # strings ou listas
    if isinstance(val, str):
        return val if val.strip() else default
    if isinstance(val, list):
        return val if len(val) > 0 else default
    return val if val else default


# =========================
# Health
# =========================
@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "brand-matrix"}), 200


# =========================
# M0 — Pesquisa (normalização)
# =========================
@app.post("/m0-pesquisa")
def m0_pesquisa():
    """
    Espera:
    {
      "brand": "Arte della Pizza",
      "category": "Pizzarias artesanais - Zona Oeste SP",
      "findings": [
         {"text": "...", "source_type":"website|instagram|facebook|maps|news|menu|app",
          "source_name":"ARTEDELAPIZZA", "url":"https://..."}
      ]
    }
    Retorna findings normalizados + fontes obrigatórias que ficaram faltando.
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand","")
    category = b.get("category","")
    findings = b.get("findings") or []

    normalized = []
    must_sources = ["website","instagram","facebook","maps"]  # dá pra ampliar (news, menu, app…)
    seen_types = set()

    for f in findings:
        txt = ensure((f or {}).get("text","").strip(), "")
        if not txt:
            continue
        stype = ((f or {}).get("source_type","") or "").lower()
        sname = ensure((f or {}).get("source_name","").strip(), "N/A")
        url   = ensure((f or {}).get("url","").strip(), "")
        normalized.append({
            "text": txt,
            "source_type": stype or "unknown",
            "source_name": sname,
            "url": url
        })
        if stype:
            seen_types.add(stype)

    missing_sources = [s for s in must_sources if s not in seen_types]

    return jsonify({
        "brand": brand,
        "category": category,
        "stage": "research",
        "evidence": normalized,
        "missing_sources": missing_sources,
        "notes": "Servidor não pesquisa; o cliente (GPT) faz a busca e envia aqui."
    }), 200


# =========================
# M1 — Matriz de Benefícios
# =========================
@app.post("/m1-beneficios")
def m1_beneficios():
    """
    Espera:
    {
      "brand":"...", "scope":"...",
      "evidence":[{"text":"...", "source_name":"...", "source_type":"...", "url":"..."}]
    }
    """
    body = request.get_json(silent=True) or {}
    brand = body.get("brand","")
    scope = body.get("scope","")
    evidences = body.get("evidence") or []

    rows, covered = [], defaultdict(set)
    for ev in evidences:
        text = (ev or {}).get("text","").strip()
        if not text:
            continue
        source_name = ensure((ev or {}).get("source_name","").strip(), "N/A")
        source_type = ensure((ev or {}).get("source_type","").strip(), "unknown")
        url = ensure((ev or {}).get("url","").strip(), "")
        pillar, sub = classify_snippet(text)
        rows.append({
            "pillar": pillar,
            "sub_benefit": sub,
            "evidence": text,
            "source": source_name,
            "source_type": source_type,
            "url": url
        })
        covered[pillar].add(sub)

    missing_subs = {
        pillar: [s for s in subs if s not in covered[pillar]]
        for pillar, subs in PILLARS.items()
    }

    return jsonify({
        "brand": brand,
        "stage": "benefit_matrix",
        "attributes": rows,              # linhas classificadas
        "missing_subbenefits": missing_subs,  # checklist do que não apareceu
        "notes": f"classificação automática M1 — escopo: {scope}"
    }), 200


# =========================
# M2 — Uso × Relevância
# =========================
@app.post("/m2-diferenciais")
def m2_diferenciais():
    """
    Espera:
    {
      "brand":"...",
      "from_m1":{
        "attributes":[{ "pillar":"...", "sub_benefit":"...", "evidence":"...", "source":"...", "url":"..." }],
        "missing_subbenefits": { "funcionais":[...], ... }
      },
      "hints": { opcional, recomendações/observações do GPT }
    }
    Saída: todos os sub-benefícios (os encontrados e os faltantes) com:
    usage_level, relevance_level, recommendation, priority, found(bool), evidence(list)
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand","")
    m1 = b.get("from_m1") or {}
    attributes = m1.get("attributes") or []
    missing = m1.get("missing_subbenefits") or {}

    # index por (pillar, sub)
    idx = defaultdict(lambda: {"found": False, "evidence": []})
    for a in attributes:
        key = (a.get("pillar",""), a.get("sub_benefit",""))
        idx[key]["found"] = True
        idx[key]["evidence"].append({
            "quote": a.get("evidence",""),
            "source": a.get("source",""),
            "url": a.get("url","")
        })

    # monta a lista completa (inclui faltantes)
    out = []
    for pillar, subs in PILLARS.items():
        for sub in subs:
            key = (pillar, sub)
            found = idx[key]["found"]
            evidence = idx[key]["evidence"]
            # default conservador (não inventa)
            usage = "temos_muito" if found else "nao_tem"
            rel   = "gera_valor" if found else "um_pouco_comum"
            # recomendações conservadoras
            if not found:
                rec, prio = "avaliar", "baixa"
            else:
                rec, prio = "proteger", "alta"
            out.append({
                "pillar": pillar,
                "sub_benefit": sub,
                "found": found,
                "usage_level": usage,
                "relevance_level": rel,
                "recommendation": rec,
                "priority": prio,
                "evidence": evidence
            })

    return jsonify({
        "brand": brand,
        "stage": "diferenciais_matrix",
        "grid": out,
        "notes": "Sem inventar: os não encontrados permanecem como nao_tem + avaliar."
    }), 200


# =========================
# M3 — Decisão Estratégica
# =========================
@app.post("/m3-decisao")
def m3_decisao():
    """
    Espera:
    {
      "brand":"...",
      "from_m2": { "grid":[ { pillar, sub_benefit, found, recommendation, ... }, ... ] }
    }
    Saída: cada item com eixo (nível de uso x relevância) + decisão + argumento.
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand","")
    grid = (b.get("from_m2") or {}).get("grid") or []

    def decide(rec, found):
        rec = (rec or "").lower()
        if not found:
            return ("Nao_usamos","Irrelevante_ou_Esperar",
                    "Não encontrado nas fontes primárias; priorize provar antes de avançar.")
        if rec in ["proteger"]:
            return ("Usamos_bem","Potencial_estrategico",
                    "Proteja o diferencial; evite comoditização com calendário e provas.")
        if rec in ["aprimorar","reforcar","reforço","reforco"]:
            return ("Usamos_pouco","Potencial_estrategico",
                    "Com pouco esforço, capture mais resultado; dê destaque.")
        if rec in ["desenvolver","implementar"]:
            return ("Nao_usamos","Potencial_estrategico",
                    "Maior potencial de diferenciação; planeje e implemente.")
        if rec in ["manter"]:
            return ("Usamos_bem","Potencial_tatico",
                    "Obrigatório/tático; mantenha qualidade e foco em outros itens.")
        if rec in ["reduzir","eliminar"]:
            return ("Usamos_bem","Commodity",
                    "Comoditizado; mínimo esforço ou elimine.")
        return ("Usamos_pouco","Potencial_tatico","Padrão até termos dados melhores.")

    decisions = []
    for row in grid:
        rec = row.get("recommendation","avaliar")
        found = bool(row.get("found"))
        usage_axis, relevance_axis, arg = decide(rec, found)
        decisions.append({
            "pillar": row.get("pillar",""),
            "sub_benefit": row.get("sub_benefit",""),
            "decision_usage": usage_axis,
            "decision_relevance": relevance_axis,
            "argument": arg
        })

    return jsonify({
        "brand": brand,
        "stage": "decisao_estrategica",
        "decisions": decisions
    }), 200


# =========================
# M4 — Detalhamento
# =========================
@app.post("/m4-detalhamento")
def m4_detalhamento():
    """
    Espera:
    {
      "brand":"...",
      "from_m3": { "decisions":[ { pillar, sub_benefit, ... }, ... ] }
    }
    Gera esqueleto completo (sem inventar): campos vazios => marcados em 'missing'.
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand","")
    decisions = (b.get("from_m3") or {}).get("decisions") or []

    detailed, gaps = [], []
    for d in decisions:
        name = f"{d.get('pillar','')}/{d.get('sub_benefit','')}"
        item = {
            "differential": name,
            "porque": "",
            "racional": "",
            "emocional": "",
            "tangivel": "",
            "intangivel": "",
            "positivo": "",
            "negativo": "",
            "card_em_discussao": name,
            "observacao": ""
        }
        missing = [k for k,v in item.items() if k not in ["differential","card_em_discussao"] and not v]
        detailed.append(item)
        gaps.append({"differential": name, "missing": missing})

    return jsonify({
        "brand": brand,
        "stage": "detalhamento",
        "detailed": detailed,
        "gaps": gaps,
        "notes": "Preencha campos vazios com base em evidências aprovadas; não inventar."
    }), 200


# =========================
# M5 — Planejamento (Dizer/Mostrar/Fazer)
# =========================
@app.post("/m5-planejamento")
def m5_planejamento():
    """
    Espera:
    {
      "brand":"...",
      "from_m4": { "detailed":[ { differential, ... } ] }
    }
    Gera esqueleto de plano. Nada inventado: placeholders para o usuário completar.
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand","")
    detailed = (b.get("from_m4") or {}).get("detailed") or []

    plan = []
    for d in detailed:
        name = d.get("differential","")
        plan.append({
            "differential": name,
            "dizer":   {"o_que": "", "onde": [], "como": ""},
            "mostrar": {"o_que": "", "onde": [], "como": ""},
            "fazer":   {"o_que": "", "onde": [], "como": ""}
        })

    return jsonify({
        "brand": brand,
        "stage": "planejamento",
        "plan": plan,
        "notes": "Defina mensagens, canais e ações com base nos itens aprovados; sem extrapolações."
    }), 200


# Local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
