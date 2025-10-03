from flask import Flask, request, jsonify
from collections import defaultdict
from typing import List, Dict, Tuple

app = Flask(__name__)

# =========================
# Regras base
# =========================
PILLARS = {
    "funcionais": ["segurança","controle","desempenho","conveniência","otimização","cuidado"],
    "experienciais": ["hedonismo","convívio","transformacionais","criadoras","capacitadoras","sensoriais"],
    "sociais": ["superioridade","conformidade","tribais","reconhecimento","qualificação","conexão"],
    "expressão": ["personalidade","individualidade","independência","vanguarda","engajamento","visão de mundo"],
    "realização": ["unicidade","inspiração","transcendência","vitalidade","realização","auto-afirmação"],
}

# Palavras-chave por sub-benefício (pizzaria + genéricos). Ajuste/expanda à vontade.
M1_KEYWORDS = [
    # FUNCIONAIS
    (["whatsapp","app","pedido","pagamento","pix","cartão","cartao","todos os dias",
      "semi-pronta","semipronta","pizza store","entrega rápida","delivery rápido","rastreamento","status","avisamos","a caminho"],
     ("funcionais","conveniência")),
    (["rastreamento","status","avisamos","acompanhe","notificação"], ("funcionais","controle")),
    (["qualidade","massa","fermentação","fermentacao","forno","processo","padrão","padrao","insumos","san marzano","napolitana","longa maturação","longa maturacao"],
     ("funcionais","desempenho")),
    (["pet friendly","pet-friendly","petfriendly","cuidado"], ("funcionais","cuidado")),
    (["otimização","otimizacao","agilidade","eficiência","eficiencia"], ("funcionais","otimização")),
    (["segurança","seguro","confiável","confiavel"], ("funcionais","segurança")),

    # EXPERIENCIAIS
    (["evento","eventos","serviço de eventos","levamos a experiência","preparadas na hora","ao vivo"],
     ("experienciais","capacitadoras")),
    (["sabor","ingrediente","mozzarella de búfala","alho negro","pera","gorgonzola","pepperoni","textura","aroma","cornicione"],
     ("experienciais","sensoriais")),
    (["experiência única","inesquecível","prazer","delícia","memória","memoria","desejo"],
     ("experienciais","hedonismo")),
    (["convivio","convívio","familiar","amigos","família","familia","acolhedor","acolhimento"],
     ("experienciais","convívio")),
    (["criamos","autoral","autorais","edição limitada","sazonal"],
     ("experienciais","criadoras")),
    (["transforma","transformacional","descoberta","aprendizado"],
     ("experienciais","transformacionais")),

    # SOCIAIS
    (["mais desejada","prêmio","premio","selo","imprensa","matéria","ranking","destaque","influenciador"],
     ("sociais","reconhecimento")),
    (["comunidade","grupo","pertencer","club","tribo","tribal"], ("sociais","tribais")),
    (["conexão","compartilhar","marcar","ugc","hashtag"], ("sociais","conexão")),
    (["superior","topo","elite","premium"], ("sociais","superioridade")),
    (["conforme","padrão do setor","obrigatório"], ("sociais","conformidade")),
    (["certificação","qualificado","qualificação"], ("sociais","qualificação")),

    # EXPRESSÃO
    (["reels","conteúdo","conteudo","promoção","siga","seguir","call to action"],
     ("expressão","engajamento")),
    (["manifesto","posicionamento","visão de mundo","proposito","propósito","vanguarda","independência","individualidade","personalidade"],
     ("expressão","visão de mundo")),

    # REALIZAÇÃO
    (["massa leve","levíssima","digestível","saudável","leveza","vitalidade"],
     ("realização","vitalidade")),
    (["inspiração","inspirador","orgulho","autoestima","auto-afirmação","auto afirmacao"],
     ("realização","inspiração")),
    (["única","secreta","exclusiva","unicidade","bairro charmoso","surpreendente"],
     ("realização","unicidade")),
    (["transcendência","transcendencia","superação"], ("realização","transcendência")),
    (["realização pessoal","objetivo atingido"], ("realização","realização")),
]

def classify_snippet(text: str) -> Tuple[str, str]:
    t = (text or "").lower()
    for keys, tag in M1_KEYWORDS:
        if any(k in t for k in keys):
            return tag
    # fallback bem conservador
    return ("funcionais","conveniência")

def ensure(val, default):
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
# M0 — Pesquisa (cliente/GPT faz a busca; aqui só normaliza)
# =========================
@app.post("/m0-pesquisa")
def m0_pesquisa():
    """
    Espera:
    {
      "brand": "...",
      "category": "...",
      "findings": [
        { "text": "...", "source_type":"website|instagram|facebook|maps|news|menu|app",
          "source_name":"...", "url":"https://...", "captured_at":"2025-10-03" }
      ]
    }
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand",""); category = b.get("category","")
    findings = b.get("findings") or []
    normalized = []
    must = ["website","instagram","facebook","maps"]
    seen = set()

    for f in findings:
        txt = ensure((f or {}).get("text","").strip(), "")
        if not txt:
            continue
        st = (f or {}).get("source_type","").lower() or "unknown"
        sn = ensure((f or {}).get("source_name","").strip(), "N/A")
        url = ensure((f or {}).get("url","").strip(), "")
        dt  = ensure((f or {}).get("captured_at","").strip(), "")
        normalized.append({"text": txt, "source_type": st, "source_name": sn, "url": url, "captured_at": dt})
        if st: seen.add(st)

    missing_sources = [s for s in must if s not in seen]

    return jsonify({
        "brand": brand,
        "category": category,
        "stage": "research",
        "evidence": normalized,
        "missing_sources": missing_sources,
        "notes": "Servidor não navega; a coleta vem do cliente (GPT) e é normalizada aqui."
    }), 200

# =========================
# M0b — Competidores (normalização + base comparativa)
# =========================
@app.post("/m0-competidores")
def m0_competidores():
    """
    Espera:
    {
      "brand": "...",
      "category": "...",
      "competitors_findings": [
        { "competitor": "Concorrente A",
          "findings": [ {"text":"...","source_type":"maps","source_name":"Google Maps","url":"...","captured_at":"..."} ]
        }
      ]
    }
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand",""); category = b.get("category","")
    comp = b.get("competitors_findings") or []

    comps_norm = []
    # normaliza
    for c in comp:
        name = ensure((c or {}).get("competitor","").strip(), "")
        items = []
        for f in (c or {}).get("findings") or []:
            txt = ensure((f or {}).get("text","").strip(), "")
            if not txt: continue
            items.append({
                "text": txt,
                "source_type": (f or {}).get("source_type","").lower() or "unknown",
                "source_name": ensure((f or {}).get("source_name","").strip(), "N/A"),
                "url": ensure((f or {}).get("url","").strip(), ""),
                "captured_at": ensure((f or {}).get("captured_at","").strip(), "")
            })
        if name and items:
            comps_norm.append({"competitor": name, "evidence": items})

    # base comparativa (apenas marca ✓/– por sub-benefício, sem “inventar”)
    def classify_all(ev_list):
        covered = defaultdict(set)
        for ev in ev_list:
            pillar, sub = classify_snippet(ev.get("text",""))
            covered[pillar].add(sub)
        return covered

    comparison = []
    for c in comps_norm:
        covered = classify_all(c["evidence"])
        rows = []
        for pillar, subs in PILLARS.items():
            for sub in subs:
                rows.append({
                    "pillar": pillar,
                    "sub_benefit": sub,
                    "found": sub in covered[pillar]
                })
        comparison.append({"competitor": c["competitor"], "matrix": rows})

    return jsonify({
        "brand": brand,
        "category": category,
        "stage": "competitors_research",
        "competitors": comps_norm,
        "comparison": comparison
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
      "evidence":[{"text":"...","source_name":"...","source_type":"...","url":"...","captured_at":"..."}],
      "suggestions": [ {"text":"...","from":"category_pattern"} ]   # opcional
    }
    """
    body = request.get_json(silent=True) or {}
    brand = body.get("brand",""); scope = body.get("scope","")
    evidences = body.get("evidence") or []
    suggestions = body.get("suggestions") or []

    rows, covered = [], defaultdict(set)
    for ev in evidences:
        text = (ev or {}).get("text","").strip()
        if not text: continue
        pillar, sub = classify_snippet(text)
        row = {
            "pillar": pillar,
            "sub_benefit": sub,
            "evidence": text,
            "source": ensure((ev or {}).get("source_name","").strip(), "N/A"),
            "source_type": ensure((ev or {}).get("source_type","").strip(), "unknown"),
            "url": ensure((ev or {}).get("url","").strip(), ""),
            "captured_at": ensure((ev or {}).get("captured_at","").strip(), ""),
            "found": True,
            "approved": False,   # a aprovação é do usuário, no GPT
            "suggested": False
        }
        rows.append(row)
        covered[pillar].add(sub)

    # sugestões (sem evidência; aguardam aprovação explícita)
    suggested_rows = []
    for s in suggestions:
        txt = ensure((s or {}).get("text","").strip(), "")
        if not txt: continue
        pillar, sub = classify_snippet(txt)
        suggested_rows.append({
            "pillar": pillar, "sub_benefit": sub,
            "evidence": "", "source":"", "source_type":"", "url":"", "captured_at":"",
            "found": False, "approved": False, "suggested": True, "suggested_from": (s or {}).get("from","")
        })

    missing_subs = { pillar: [s for s in subs if s not in covered[pillar]] for pillar, subs in PILLARS.items() }

    return jsonify({
        "brand": brand,
        "stage": "benefit_matrix",
        "attributes": rows,                 # encontrados
        "suggested": suggested_rows,        # sugeridos (pendentes)
        "missing_subbenefits": missing_subs,
        "notes": f"M1 classificada automaticamente — escopo: {scope}"
    }), 200

# =========================
# M2 — Uso × Relevância (inclui não encontrados)
# =========================
@app.post("/m2-diferenciais")
def m2_diferenciais():
    """
    Espera:
    {
      "brand":"...",
      "from_m1": {
        "attributes":[{...}], "suggested":[{...}], "missing_subbenefits":{...}
      },
      "use_only_approved": true|false,
      "from_competitors": { "comparison":[ {"competitor":"...", "matrix":[{pillar,sub_benefit,found}]} ] }  # opcional
    }
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand","")
    m1 = b.get("from_m1") or {}
    attrs = m1.get("attributes") or []
    suggested = m1.get("suggested") or []
    missing = m1.get("missing_subbenefits") or {}
    only_approved = bool(b.get("use_only_approved", False))

    # índice por (pillar,sub)
    idx = {(a.get("pillar",""), a.get("sub_benefit","")): a for a in attrs}
    sug_idx = {(s.get("pillar",""), s.get("sub_benefit","")): s for s in suggested}

    # info competitiva simples: paridade vs oportunidade
    comp = (b.get("from_competitors") or {}).get("comparison") or []
    comp_count = defaultdict(int)
    for compo in comp:
        for row in compo.get("matrix", []):
            if row.get("found"):
                comp_count[(row.get("pillar",""), row.get("sub_benefit",""))] += 1

    grid = []
    for pillar, subs in PILLARS.items():
        for sub in subs:
            key = (pillar, sub)
            a = idx.get(key)
            s = sug_idx.get(key)
            found = bool(a)
            approved = bool(a and a.get("approved"))
            suggested_flag = bool(s)

            # regras conservadoras (sem inventar)
            if only_approved and not approved:
                base_usage = "nao_tem"
                base_rel = "um_pouco_comum"
            else:
                base_usage = "temos_muito" if found and (not only_approved or approved) else "nao_tem"
                base_rel = "gera_valor" if found and (not only_approved or approved) else "um_pouco_comum"

            # competitividade
            competitors_have = comp_count.get(key, 0)
            parity = competitors_have >= 2
            opportunity = competitors_have <= 1

            if not found and not suggested_flag:
                rec, prio = "avaliar", "baixa"
            elif found and (approved or not only_approved):
                if opportunity:   rec, prio = "proteger", "alta"
                elif parity:      rec, prio = "manter", "média"
                else:             rec, prio = "aprimorar", "média"
            else:
                # sugerido (sem evidência aprovada)
                rec, prio = "avaliar", "baixa"

            evidence = []
            if a:
                evidence.append({
                    "quote": a.get("evidence",""),
                    "source": a.get("source",""),
                    "url": a.get("url",""),
                    "captured_at": a.get("captured_at","")
                })

            grid.append({
                "pillar": pillar,
                "sub_benefit": sub,
                "found": found,
                "approved": approved,
                "suggested": suggested_flag,
                "usage_level": base_usage,
                "relevance_level": base_rel,
                "recommendation": rec,
                "priority": prio,
                "parity": parity,
                "opportunity": opportunity,
                "evidence": evidence
            })

    return jsonify({
        "brand": brand,
        "stage": "diferenciais_matrix",
        "grid": grid,
        "notes": "Sem invenção: aprovados conduzem; sugeridos ficam como avaliar."
    }), 200

# =========================
# M3 — Decisão Estratégica (apenas aprovados; pendentes ficam sem quadrante)
# =========================
@app.post("/m3-decisao")
def m3_decisao():
    """
    Espera:
    {
      "brand":"...",
      "from_m2": { "grid":[{...}] }
    }
    """
    b = request.get_json(silent=True) or {}
    brand = b.get("brand","")
    grid = (b.get("from_m2") or {}).get("grid") or []

    decisions = []
    for row in grid:
        approved = bool(row.get("approved"))
        found = bool(row.get("found"))
        rec = (row.get("recommendation","") or "").lower()

        if not (approved and found):
            decisions.append({
                "pillar": row.get("pillar",""),
                "sub_benefit": row.get("sub_benefit",""),
                "decision_usage": "pendente",
                "decision_relevance": "pendente",
                "argument": "Pendente de aprovação e/ou evidência."
            })
            continue

        # eixos conforme briefing
        if rec == "proteger":
            use_axis, rel_axis, arg = "Usamos bem e queremos manter", "Tem potencial estratégico", \
                "Proteja o diferencial com calendário e provas para evitar comoditização."
        elif rec in ["aprimorar","reforçar","reforcar","destaque"]:
            use_axis, rel_axis, arg = "Usamos pouco e queremos melhorar", "Tem potencial estratégico", \
                "Com pouco esforço é possível extrair mais resultado; dê destaque."
        elif rec in ["desenvolver","implementar","oportunidade","urgente"]:
            use_axis, rel_axis, arg = "Ainda não usamos, mas queremos implementar", "Tem potencial estratégico", \
                "Maior potencial de reforço agora; priorize e implemente."
        elif rec in ["manter","mínimo esforço","minimo esforço"]:
            use_axis, rel_axis, arg = "Usamos bem e queremos manter", "Tem potencial tático", \
                "É obrigatório/tático; mantenha com qualidade."
        elif rec in ["reduzir","eliminar","ignorar"]:
            use_axis, rel_axis, arg = "Não iremos usar", "É commodity (mais do obrigatório)", \
                "Reduza/esvazie para focar no que diferencia."
        else:
            use_axis, rel_axis, arg = "Usamos pouco", "Tem potencial tático", "Padrão até termos dados melhores."

        decisions.append({
            "pillar": row.get("pillar",""),
            "sub_benefit": row.get("sub_benefit",""),
            "decision_usage": use_axis,
            "decision_relevance": rel_axis,
            "argument": arg
        })

    return jsonify({
        "brand": brand,
        "stage": "decisao_estrategica",
        "decisions": decisions
    }), 200

# =========================
# M4 — Detalhamento (marca gaps)
# =========================
@app.post("/m4-detalhamento")
def m4_detalhamento():
    """
    Espera: { "brand":"...", "from_m3": { "decisions":[...] } }
    Retorna esqueleto completo; onde não há evidência, marca em 'gaps'.
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
        detail_gaps = [k for k,v in item.items() if k not in ["differential","card_em_discussao"] and not v]
        detailed.append(item)
        gaps.append({"differential": name, "missing": detail_gaps})

    return jsonify({
        "brand": brand,
        "stage": "detalhamento",
        "detailed": detailed,
        "gaps": gaps,
        "notes": "Preencher com evidências aprovadas; nada de inferências."
    }), 200

# =========================
# M5 — Planejamento (Dizer/Mostrar/Fazer) — só aprovados
# =========================
@app.post("/m5-planejamento")
def m5_planejamento():
    """
    Espera: { "brand":"...", "from_m4": { "detailed":[...] } }
    Constrói placeholders de plano; campos vazios permanecem até serem preenchidos com base nas evidências aprovadas.
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
        "notes": "Completar com mensagens, canais e ações baseadas apenas em aprovados."
    }), 200

# Local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
