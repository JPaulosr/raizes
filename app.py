# -*- coding: utf-8 -*-
# app.py — Raízes v3

import streamlit as st
import json, os, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Raízes", page_icon="🌳", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
footer{display:none!important}#MainMenu{display:none!important}header{display:none!important}
.arv-header{text-align:center;padding:28px 20px 16px;}
.arv-header h1{font-family:'Cormorant Garamond',serif;font-size:2.4rem;font-weight:600;color:rgba(255,255,255,.92);margin:0 0 6px;}
.arv-header p{font-size:.82rem;color:rgba(255,255,255,.35);margin:0;}
.node-card{background:rgba(255,255,255,.05);border:1.5px solid rgba(255,255,255,.12);border-radius:16px;padding:14px 10px;text-align:center;position:relative;transition:border-color .2s;}
.node-card.ativo{border-color:rgba(110,232,170,.55);background:rgba(110,232,170,.06);}
.node-avatar{width:52px;height:52px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,.18);display:block;margin:0 auto 6px;}
.node-avatar-ph{width:52px;height:52px;border-radius:50%;background:rgba(255,255,255,.07);border:2px dashed rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-size:1.3rem;margin:0 auto 6px;}
.node-nome{font-family:'Cormorant Garamond',serif;font-size:.9rem;font-weight:600;color:rgba(255,255,255,.85);margin-bottom:2px;}
.node-rel{font-size:.65rem;color:rgba(255,255,255,.28);text-transform:uppercase;letter-spacing:.6px;}
.node-badge{position:absolute;top:-7px;right:-7px;background:#6ee8aa;color:#0a2a1a;border-radius:10px;font-size:9px;font-weight:700;padding:2px 6px;}
.rel-tag{font-size:.65rem;background:rgba(200,160,255,.15);color:rgba(200,160,255,.8);border-radius:8px;padding:2px 6px;margin:2px 1px;display:inline-block;}
.conector-v{width:2px;height:24px;background:rgba(255,255,255,.1);margin:0 auto;}
.det-panel{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:20px;}
.det-nome{font-family:'Cormorant Garamond',serif;font-size:1.6rem;font-weight:600;font-style:italic;color:rgba(255,255,255,.9);margin-bottom:3px;}
.det-rel{font-size:.75rem;color:rgba(255,255,255,.28);text-transform:uppercase;letter-spacing:.8px;margin-bottom:14px;}
.det-info{font-size:.82rem;color:rgba(255,255,255,.42);line-height:2;}
.foto-par{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;overflow:hidden;margin-bottom:10px;}
.foto-header{padding:9px 14px;border-bottom:1px solid rgba(255,255,255,.06);display:flex;justify-content:space-between;align-items:center;}
.foto-tit{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:.9rem;color:rgba(255,255,255,.72);}
.foto-data{font-size:10px;color:rgba(255,255,255,.18);}
.foto-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:rgba(255,255,255,.05);}
.foto-lado{position:relative;}
.foto-lado img{width:100%;height:160px;object-fit:cover;display:block;}
.foto-lado.antiga img{filter:sepia(.2) brightness(.88);}
.foto-badge{position:absolute;bottom:7px;left:7px;font-size:9px;font-weight:600;letter-spacing:.7px;text-transform:uppercase;padding:2px 9px;border-radius:20px;}
.badge-a{background:rgba(200,170,100,.3);color:#e8c97a;}
.badge-r{background:rgba(100,200,150,.25);color:#6ee8aa;}
.pessoas-tag{padding:7px 14px;font-size:.72rem;color:rgba(255,255,255,.35);background:rgba(255,255,255,.02);}
.pessoas-tag span{background:rgba(255,255,255,.07);border-radius:8px;padding:1px 7px;margin-right:3px;}
.empty-state{text-align:center;padding:50px 20px;color:rgba(255,255,255,.18);}
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.03)!important;border:1px dashed rgba(255,255,255,.14)!important;border-radius:10px!important;}
[data-testid="stTextInput"] input{background:rgba(255,255,255,.05)!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:8px!important;color:rgba(255,255,255,.85)!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# Cloudinary
# ─────────────────────────────────────────────────────────────────────
def _s(k, d=""):
    try:
        v = st.secrets.get(k, d)
        return str(v).strip() if v else d
    except:
        return os.environ.get(k, d)

CLOUD = _s("CLOUDINARY_CLOUD_NAME", "db8ipmete")
AKEY  = _s("CLOUDINARY_API_KEY")
ASEC  = _s("CLOUDINARY_API_SECRET")

def _upload(fb, fname, folder="Raizes"):
    ts  = str(int(time.time()))
    pid = folder + "/" + Path(fname).stem + "_" + ts
    sig = hashlib.sha1(("folder="+folder+"&public_id="+pid+"&timestamp="+ts+ASEC).encode()).hexdigest()
    b   = "----B" + ts
    body = ("--"+b+"\r\nContent-Disposition: form-data; name=\"file\"; filename=\""+fname+"\"\r\nContent-Type: image/jpeg\r\n\r\n").encode()
    body += fb
    body += ("\r\n--"+b+"\r\nContent-Disposition: form-data; name=\"api_key\"\r\n\r\n"+AKEY+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"timestamp\"\r\n\r\n"+ts+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\n"+folder+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"public_id\"\r\n\r\n"+pid+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"signature\"\r\n\r\n"+sig+"\r\n"
             "--"+b+"--\r\n").encode()
    req = urllib.request.Request(
        "https://api.cloudinary.com/v1_1/"+CLOUD+"/image/upload",
        data=body, headers={"Content-Type": "multipart/form-data; boundary="+b}
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())["secure_url"]

# ─────────────────────────────────────────────────────────────────────
# Google Sheets — persistência
# ─────────────────────────────────────────────────────────────────────
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def _gc():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["GCP_SERVICE_ACCOUNT"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def _get_ws():
    url = _s("PLANILHA_URL_RAIZES") or _s("PLANILHA_URL")
    gc  = _gc()
    sh  = gc.open_by_url(url) if url.startswith("http") else gc.open_by_key(url)
    try:
        return sh.worksheet("Raizes_Arvore")
    except:
        ws = sh.add_worksheet("Raizes_Arvore", rows=10, cols=2)
        ws.update("A1", [["chave", "dados"]])
        ws.update("A2", [["raizes", "{}"]])
        return ws

def _carregar():
    try:
        ws   = _get_ws()
        rows = ws.get_all_values()
        raw  = "{}"
        for row in rows:
            if row and row[0] == "raizes":
                raw = row[1] if len(row) > 1 else "{}"
                break
        d      = json.loads(raw) if raw.strip() else {}
        arvore = d.get("arvore", [])
        acervo = d.get("acervo", d.get("galeria", []))
        for p in arvore:
            p.setdefault("foto_ids",    [])
            p.setdefault("conjuge_id",  "")
            p.setdefault("pai_id",      "")
            p.setdefault("mae_id",      "")
        for f in acervo:
            f.setdefault("pessoas", [])
            if "id" not in f:
                f["id"] = "f" + str(int(time.time()*1000))
        return arvore, acervo
    except Exception as e:
        st.error("Erro ao carregar: " + str(e))
        return [], []

def _salvar(arvore, acervo):
    try:
        ws      = _get_ws()
        payload = json.dumps({"arvore": arvore, "acervo": acervo}, ensure_ascii=False)
        rows    = ws.get_all_values()
        linha   = None
        for i, row in enumerate(rows, start=1):
            if row and row[0] == "raizes":
                linha = i
                break
        if linha:
            ws.update(f"B{linha}", [[payload]])
        else:
            ws.append_row(["raizes", payload])
        return True
    except Exception as e:
        st.error("Erro ao salvar: " + str(e))
        return False

# ─────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────
if "carregado" not in st.session_state:
    arv, acv = _carregar()
    st.session_state.arvore    = arv
    st.session_state.acervo    = acv
    st.session_state.carregado = True

if "ativo" not in st.session_state: st.session_state.ativo = None
if "modo"  not in st.session_state: st.session_state.modo  = "ver"

def salvar_tudo():
    ok = _salvar(st.session_state.arvore, st.session_state.acervo)
    if ok:
        st.toast("Salvo com sucesso!", icon="💾")
    return ok

# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
NIVEL = {
    "Bisavô":0,"Bisavó":0,
    "Avô (paterno)":1,"Avó (paterna)":1,"Avô (materno)":1,"Avó (materna)":1,
    "Pai":2,"Mãe":2,"Tio":2,"Tia":2,
    "Eu":3,"Cônjuge":3,"Irmão":3,"Irmã":3,"Primo":3,"Prima":3,
    "Filho":4,"Filha":4,"Sobrinho":4,"Sobrinha":4,"Outro":3
}
EMOJIS = {
    "Pai":"👨","Mãe":"👩","Avô (paterno)":"👴","Avó (paterna)":"👵",
    "Avô (materno)":"👴","Avó (materna)":"👵","Bisavô":"🧓","Bisavó":"👵",
    "Eu":"🧑","Cônjuge":"💑","Irmão":"👦","Irmã":"👧",
    "Filho":"👦","Filha":"👧","Prima":"👩","Primo":"👦","Tia":"👩","Tio":"👨"
}

def _nivel(p):    return NIVEL.get(p.get("relacao","Outro"), 3)
def _p_by_id(pid): return next((p for p in st.session_state.arvore if p["id"]==pid), None)
def _nome_curto(pid):
    p = _p_by_id(pid)
    return p["nome"].split()[0] if p else "?"

def _fotos_pessoa(pid):
    return [f for f in st.session_state.acervo if pid in f.get("pessoas",[])]

def _avatar_html(p, sz=52):
    url   = p.get("foto_perfil","")
    emoji = EMOJIS.get(p.get("relacao",""),"👤")
    if url:
        return f'<img class="node-avatar" src="{url}" style="width:{sz}px;height:{sz}px;">'
    return f'<div class="node-avatar-ph" style="width:{sz}px;height:{sz}px;font-size:{int(sz*.48)}px;">{emoji}</div>'

def _node_html(p, ativo=False):
    arvore = st.session_state.arvore
    qtd    = len(_fotos_pessoa(p["id"]))
    badge  = f'<span class="node-badge">{qtd}📷</span>' if qtd else ""
    tags   = ""
    if p.get("conjuge_id"):
        tags += f'<span class="rel-tag">💍 {_nome_curto(p["conjuge_id"])}</span>'
    if p.get("pai_id"):
        tags += f'<span class="rel-tag">👨 {_nome_curto(p["pai_id"])}</span>'
    if p.get("mae_id"):
        tags += f'<span class="rel-tag">👩 {_nome_curto(p["mae_id"])}</span>'
    cls = "node-card ativo" if ativo else "node-card"
    return (f'<div class="{cls}">{badge}{_avatar_html(p)}'
            f'<div class="node-nome">{p["nome"].split()[0]}</div>'
            f'<div class="node-rel">{p.get("relacao","")}</div>'
            f'{tags}</div>')

def _foto_par_html(foto):
    arvore = st.session_state.arvore
    nomes  = [_nome_curto(pid) for pid in foto.get("pessoas",[]) if _p_by_id(pid)]
    header = (f'<div class="foto-header">'
              f'<span class="foto-tit">{foto.get("titulo","")}</span>'
              f'<span class="foto-data">{foto.get("data","")}</span></div>')
    grid   = (f'<div class="foto-grid">'
              f'<div class="foto-lado antiga"><img src="{foto.get("antiga","")}"><span class="foto-badge badge-a">Antiga</span></div>'
              f'<div class="foto-lado"><img src="{foto.get("restaurada","")}"><span class="foto-badge badge-r">Restaurada</span></div>'
              f'</div>')
    pess   = ""
    if nomes:
        tags = "".join(f"<span>{n}</span>" for n in nomes)
        pess = f'<div class="pessoas-tag">Nesta foto: {tags}</div>'
    return f'<div class="foto-par">{header}{grid}{pess}</div>'

# ─────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="arv-header"><h1>🌳 Raízes</h1>'
    '<p>Árvore Genealógica da Família</p></div>',
    unsafe_allow_html=True
)

tab_arv, tab_acervo, tab_debug = st.tabs(["🌳 Árvore", "📷 Acervo de Fotos", "🔧 Diagnóstico"])

# ═══════════════════════════════════════════════════════════════════════
# TAB DIAGNÓSTICO — verificar banco de dados
# ═══════════════════════════════════════════════════════════════════════
with tab_debug:
    st.markdown("### Diagnóstico da Base de Dados")
    st.caption("Use esta aba para verificar se os dados estão sendo salvos no Google Sheets.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Recarregar do banco", use_container_width=True):
            arv2, acv2 = _carregar()
            st.session_state.arvore    = arv2
            st.session_state.acervo    = acv2
            st.success(f"Carregado: {len(arv2)} pessoas, {len(acv2)} fotos")
    with c2:
        if st.button("💾 Forçar salvar agora", use_container_width=True, type="primary"):
            salvar_tudo()

    st.markdown(f"**Na memória:** {len(st.session_state.arvore)} pessoas · {len(st.session_state.acervo)} fotos")

    if st.session_state.arvore:
        st.markdown("**Pessoas:**")
        for p in st.session_state.arvore:
            conj = f" | 💍 {_nome_curto(p['conjuge_id'])}" if p.get("conjuge_id") else ""
            pai  = f" | 👨 {_nome_curto(p['pai_id'])}"     if p.get("pai_id")     else ""
            mae  = f" | 👩 {_nome_curto(p['mae_id'])}"     if p.get("mae_id")     else ""
            st.markdown(f"- **{p['nome']}** ({p.get('relacao','')}){conj}{pai}{mae}")

    with st.expander("Ver JSON completo"):
        st.json({"arvore": st.session_state.arvore, "acervo": st.session_state.acervo})

# ═══════════════════════════════════════════════════════════════════════
# TAB ÁRVORE
# ═══════════════════════════════════════════════════════════════════════
with tab_arv:
    col_arv, col_pain = st.columns([2.2, 1], gap="large")

    with col_arv:
        arvore = st.session_state.arvore
        if not arvore:
            st.markdown(
                '<div class="empty-state">'
                '<div style="font-size:3rem;opacity:.2;margin-bottom:12px">🌳</div>'
                '<p>Árvore vazia. Adicione a primeira pessoa →</p>'
                '</div>', unsafe_allow_html=True
            )
        else:
            niveis: dict = {}
            for p in arvore:
                niveis.setdefault(_nivel(p), []).append(p)
            for n in sorted(niveis.keys()):
                if n > min(niveis.keys()):
                    st.markdown('<div class="conector-v"></div>', unsafe_allow_html=True)
                pessoas_n = niveis[n]
                cols = st.columns(max(len(pessoas_n), 1))
                for col, p in zip(cols, pessoas_n):
                    with col:
                        ativo = (st.session_state.ativo == p["id"])
                        st.markdown(_node_html(p, ativo), unsafe_allow_html=True)
                        if st.button(p["nome"].split()[0], key="sel_"+p["id"], use_container_width=True):
                            st.session_state.ativo = p["id"]
                            st.session_state.modo  = "ver"
                            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Adicionar pessoa", use_container_width=True):
            st.session_state.modo  = "add"
            st.session_state.ativo = None
            st.rerun()

    with col_pain:
        arvore = st.session_state.arvore

        # ── Adicionar pessoa ──────────────────────────────────────────
        if st.session_state.modo == "add":
            st.markdown("#### ➕ Nova pessoa")
            nome_n  = st.text_input("Nome completo *", key="add_nome")
            rel_n   = st.selectbox("Relação na família", list(NIVEL.keys()), key="add_rel")
            gen_n   = st.radio("Gênero", ["Masculino","Feminino"], horizontal=True, key="add_gen")
            nasc_n  = st.text_input("Nascimento", placeholder="12/04/1945", key="add_nasc")
            falec_n = st.text_input("Falecimento (opcional)", key="add_falec")

            st.markdown("**Vínculos familiares**")
            nomes_map = {p["nome"]: p["id"] for p in arvore}
            opcoes    = ["(nenhum)"] + list(nomes_map.keys())
            conjuge_s = st.selectbox("💍 Cônjuge", opcoes, key="add_conjuge")
            pai_s     = st.selectbox("👨 Pai",     opcoes, key="add_pai")
            mae_s     = st.selectbox("👩 Mãe",     opcoes, key="add_mae")

            st.caption("Foto de perfil (opcional)")
            fp_f = st.file_uploader("", type=["jpg","jpeg","png","webp"], key="add_fp", label_visibility="collapsed")
            if fp_f: st.image(fp_f, use_container_width=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Salvar", use_container_width=True, type="primary", key="btn_add_sv"):
                    if not nome_n.strip():
                        st.warning("Digite o nome.")
                    else:
                        url_p = ""
                        if fp_f and AKEY:
                            with st.spinner("Enviando foto..."):
                                try:
                                    fp_f.seek(0)
                                    url_p = _upload(fp_f.read(), fp_f.name)
                                except Exception as e:
                                    st.error("Erro foto perfil: "+str(e))
                        nova_id = "p" + str(int(time.time()*1000))
                        nova = {
                            "id":          nova_id,
                            "nome":        nome_n.strip(),
                            "relacao":     rel_n,
                            "genero":      "F" if gen_n=="Feminino" else "M",
                            "nascimento":  nasc_n.strip(),
                            "falecimento": falec_n.strip(),
                            "foto_perfil": url_p,
                            "conjuge_id":  nomes_map.get(conjuge_s, ""),
                            "pai_id":      nomes_map.get(pai_s,    ""),
                            "mae_id":      nomes_map.get(mae_s,    ""),
                            "foto_ids":    []
                        }
                        st.session_state.arvore.append(nova)
                        # atualizar cônjuge reciprocamente
                        if nova["conjuge_id"]:
                            for p in st.session_state.arvore:
                                if p["id"] == nova["conjuge_id"]:
                                    p["conjuge_id"] = nova_id
                        ok = salvar_tudo()
                        if ok:
                            st.session_state.ativo = nova_id
                            st.session_state.modo  = "ver"
                            st.rerun()
            with c2:
                if st.button("Cancelar", use_container_width=True, key="btn_add_cancel"):
                    st.session_state.modo = "ver"
                    st.rerun()

        # ── Ver pessoa ────────────────────────────────────────────────
        elif st.session_state.ativo:
            pessoa = _p_by_id(st.session_state.ativo)
            if not pessoa:
                st.session_state.ativo = None
                st.rerun()

            fotos_p = _fotos_pessoa(pessoa["id"])
            qtd     = len(fotos_p)

            # Monta info
            info = ""
            if pessoa.get("nascimento"):  info += f"📅 {pessoa['nascimento']}<br>"
            if pessoa.get("falecimento"): info += f"✝️ {pessoa['falecimento']}<br>"
            if pessoa.get("conjuge_id"):  info += f"💍 Casado(a) com {_nome_curto(pessoa['conjuge_id'])}<br>"
            if pessoa.get("pai_id"):      info += f"👨 Pai: {_nome_curto(pessoa['pai_id'])}<br>"
            if pessoa.get("mae_id"):      info += f"👩 Mãe: {_nome_curto(pessoa['mae_id'])}<br>"
            filhos = [p for p in st.session_state.arvore
                      if p.get("pai_id")==pessoa["id"] or p.get("mae_id")==pessoa["id"]]
            if filhos:
                info += "👶 Filhos: " + ", ".join(p["nome"].split()[0] for p in filhos) + "<br>"
            info += f"📷 {qtd} foto{'s' if qtd!=1 else ''}"

            st.markdown(
                f'<div class="det-panel">'
                f'<div class="det-nome">{pessoa["nome"]}</div>'
                f'<div class="det-rel">{pessoa.get("relacao","")}</div>'
                f'<div class="det-info">{info}</div></div>',
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

            # Fotos
            if fotos_p:
                st.markdown(f"**📷 Fotos de {pessoa['nome'].split()[0]}**")
                for foto in fotos_p:
                    st.markdown(_foto_par_html(foto), unsafe_allow_html=True)
                    if st.button("Desvincular", key="desv_"+foto["id"]+"_"+pessoa["id"], use_container_width=True):
                        foto["pessoas"] = [x for x in foto.get("pessoas",[]) if x != pessoa["id"]]
                        salvar_tudo()
                        st.rerun()

            # Vincular foto existente
            outras = [f for f in st.session_state.acervo if pessoa["id"] not in f.get("pessoas",[])]
            if outras:
                with st.expander("🔗 Vincular foto existente do acervo"):
                    opcoes_f = {f["titulo"]+" ("+f.get("data","")+")": f["id"] for f in outras}
                    sel_f    = st.multiselect("Selecione", list(opcoes_f.keys()), key="vinc_"+pessoa["id"])
                    if st.button("✅ Vincular", use_container_width=True, type="primary", key="btn_vinc_"+pessoa["id"]):
                        for label, fid in opcoes_f.items():
                            if label in sel_f:
                                fo = next((f for f in st.session_state.acervo if f["id"]==fid), None)
                                if fo and pessoa["id"] not in fo.get("pessoas",[]):
                                    fo.setdefault("pessoas",[]).append(pessoa["id"])
                        salvar_tudo()
                        st.rerun()

            # Nova foto
            with st.expander(f"➕ Nova foto de {pessoa['nome'].split()[0]}"):
                tit_f = st.text_input("Nome da foto", placeholder="Casamento 1972", key="tit_f_"+pessoa["id"])
                outros_nomes = {p["nome"]: p["id"] for p in st.session_state.arvore if p["id"] != pessoa["id"]}
                tambem = st.multiselect("Quem mais aparece?", list(outros_nomes.keys()), key="tambem_"+pessoa["id"])
                fa = st.file_uploader("Foto antiga",    type=["jpg","jpeg","png","webp"], key="fa_"+pessoa["id"])
                fr = st.file_uploader("Foto restaurada", type=["jpg","jpeg","png","webp"], key="fr_"+pessoa["id"])
                if fa: st.image(fa, use_container_width=True)
                if fr: st.image(fr, use_container_width=True)
                if st.button("💾 Salvar foto", use_container_width=True, type="primary", key="btn_foto_"+pessoa["id"]):
                    if not fa or not fr:
                        st.warning("Selecione as duas fotos.")
                    elif not AKEY:
                        st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
                    else:
                        with st.spinner("Enviando fotos..."):
                            try:
                                fa.seek(0); fr.seek(0)
                                ua = _upload(fa.read(), fa.name)
                                ur = _upload(fr.read(), fr.name)
                                ids_pess = [pessoa["id"]] + [outros_nomes[n] for n in tambem]
                                nova_foto = {
                                    "id":         "f" + str(int(time.time()*1000)),
                                    "titulo":     tit_f.strip() or "Sem título",
                                    "antiga":     ua,
                                    "restaurada": ur,
                                    "data":       datetime.now().strftime("%d/%m/%Y"),
                                    "pessoas":    ids_pess
                                }
                                st.session_state.acervo.insert(0, nova_foto)
                                salvar_tudo()
                                st.rerun()
                            except Exception as e:
                                st.error("Erro: "+str(e))

            # Editar dados
            with st.expander("✏️ Editar dados"):
                nome_e  = st.text_input("Nome",        value=pessoa.get("nome",""),        key="ed_nome_"+pessoa["id"])
                rels    = list(NIVEL.keys())
                rel_idx = rels.index(pessoa.get("relacao","Outro")) if pessoa.get("relacao") in rels else 0
                rel_e   = st.selectbox("Relação",      rels, index=rel_idx,                key="ed_rel_"+pessoa["id"])
                nasc_e  = st.text_input("Nascimento",  value=pessoa.get("nascimento",""),  key="ed_nasc_"+pessoa["id"])
                falec_e = st.text_input("Falecimento", value=pessoa.get("falecimento",""), key="ed_falec_"+pessoa["id"])

                nomes2  = {p["nome"]: p["id"] for p in st.session_state.arvore if p["id"] != pessoa["id"]}
                opc2    = ["(nenhum)"] + list(nomes2.keys())

                def _idx2(val_id):
                    nome_v = next((p["nome"] for p in st.session_state.arvore if p["id"]==val_id), None)
                    return opc2.index(nome_v) if nome_v and nome_v in opc2 else 0

                conj_e = st.selectbox("💍 Cônjuge", opc2, index=_idx2(pessoa.get("conjuge_id","")), key="ed_conj_"+pessoa["id"])
                pai_e  = st.selectbox("👨 Pai",     opc2, index=_idx2(pessoa.get("pai_id","")),     key="ed_pai_"+pessoa["id"])
                mae_e  = st.selectbox("👩 Mãe",     opc2, index=_idx2(pessoa.get("mae_id","")),     key="ed_mae_"+pessoa["id"])

                if st.button("💾 Salvar edições", use_container_width=True, type="primary", key="btn_ed_"+pessoa["id"]):
                    pessoa["nome"]        = nome_e.strip()
                    pessoa["relacao"]     = rel_e
                    pessoa["nascimento"]  = nasc_e.strip()
                    pessoa["falecimento"] = falec_e.strip()
                    pessoa["conjuge_id"]  = nomes2.get(conj_e, "")
                    pessoa["pai_id"]      = nomes2.get(pai_e,  "")
                    pessoa["mae_id"]      = nomes2.get(mae_e,  "")
                    salvar_tudo()
                    st.rerun()

            with st.expander("🗑️ Remover pessoa"):
                st.warning(f"Remove **{pessoa['nome']}** permanentemente.")
                if st.button("Confirmar remoção", use_container_width=True, key="btn_del_"+pessoa["id"]):
                    st.session_state.arvore = [p for p in st.session_state.arvore if p["id"] != pessoa["id"]]
                    salvar_tudo()
                    st.session_state.ativo = None
                    st.rerun()

        else:
            st.markdown(
                '<div class="det-panel"><div class="empty-state">'
                '<div style="font-size:1.8rem;opacity:.2;margin-bottom:8px">👆</div>'
                '<p style="font-size:.85rem">Clique numa pessoa<br>para ver detalhes e fotos</p>'
                '</div></div>', unsafe_allow_html=True
            )

# ═══════════════════════════════════════════════════════════════════════
# TAB ACERVO
# ═══════════════════════════════════════════════════════════════════════
with tab_acervo:
    st.markdown("<br>", unsafe_allow_html=True)
    arvore = st.session_state.arvore
    acervo = st.session_state.acervo

    with st.expander("➕ Adicionar foto ao acervo", expanded=not bool(acervo)):
        tit_a = st.text_input("Nome da foto", placeholder="Família reunida, Natal 1980", key="tit_acervo")
        if arvore:
            nomes_t  = {p["nome"]: p["id"] for p in arvore}
            sel_pess = st.multiselect("👥 Quem aparece?", list(nomes_t.keys()), key="pess_acervo")
        else:
            sel_pess = []
            st.info("Adicione pessoas à árvore primeiro.")
        fa_a = st.file_uploader("Foto antiga",    type=["jpg","jpeg","png","webp"], key="fa_acervo")
        fr_a = st.file_uploader("Foto restaurada", type=["jpg","jpeg","png","webp"], key="fr_acervo")
        if fa_a: st.image(fa_a, use_container_width=True)
        if fr_a: st.image(fr_a, use_container_width=True)
        if st.button("💾 Salvar no acervo", use_container_width=True, type="primary", key="btn_acervo_add"):
            if not fa_a or not fr_a:
                st.warning("Selecione as duas fotos.")
            elif not AKEY:
                st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
            else:
                with st.spinner("Enviando fotos..."):
                    try:
                        fa_a.seek(0); fr_a.seek(0)
                        ua = _upload(fa_a.read(), fa_a.name)
                        ur = _upload(fr_a.read(), fr_a.name)
                        ids_s = [nomes_t[n] for n in sel_pess] if arvore else []
                        nova_foto = {
                            "id":         "f" + str(int(time.time()*1000)),
                            "titulo":     tit_a.strip() or "Sem título",
                            "antiga":     ua,
                            "restaurada": ur,
                            "date":       datetime.now().strftime("%d/%m/%Y"),
                            "data":       datetime.now().strftime("%d/%m/%Y"),
                            "pessoas":    ids_s
                        }
                        st.session_state.acervo.insert(0, nova_foto)
                        salvar_tudo()
                        st.rerun()
                    except Exception as e:
                        st.error("Erro: "+str(e))

    st.markdown("<br>", unsafe_allow_html=True)

    # Filtro por pessoa
    filtro_id = None
    if arvore:
        opcoes_fil = ["Todas as fotos"] + [p["nome"] for p in arvore]
        escolha    = st.selectbox("🔍 Filtrar por pessoa", opcoes_fil, key="filtro_acervo")
        if escolha != "Todas as fotos":
            filtro_id = next((p["id"] for p in arvore if p["nome"]==escolha), None)

    fotos_show = acervo if not filtro_id else [f for f in acervo if filtro_id in f.get("pessoas",[])]

    if not fotos_show:
        st.markdown(
            '<div class="empty-state">'
            '<div style="font-size:2rem;opacity:.2;margin-bottom:10px">🖼️</div>'
            '<p>Nenhuma foto encontrada.</p></div>', unsafe_allow_html=True
        )
    else:
        st.caption(f"{len(fotos_show)} foto(s)")
        for i, foto in enumerate(fotos_show):
            st.markdown(_foto_par_html(foto), unsafe_allow_html=True)

            with st.expander("👥 Editar pessoas nesta foto"):
                if arvore:
                    nms2   = {p["nome"]: p["id"] for p in arvore}
                    atuals = [p["nome"] for p in arvore if p["id"] in foto.get("pessoas",[])]
                    novos  = st.multiselect("Pessoas", list(nms2.keys()), default=atuals, key="ed_p_"+foto["id"])
                    if st.button("💾 Salvar", key="sv_p_"+foto["id"], use_container_width=True):
                        foto["pessoas"] = [nms2[n] for n in novos]
                        salvar_tudo()
                        st.rerun()

            b1, b2, b3, _ = st.columns([1,1,1,2])
            with b1: st.link_button("Antiga",     foto.get("antiga",""),     use_container_width=True)
            with b2: st.link_button("Restaurada", foto.get("restaurada",""), use_container_width=True)
            with b3:
                if st.button("🗑️ Excluir", key="del_ac_"+str(i), use_container_width=True):
                    st.session_state.acervo = [f for f in st.session_state.acervo if f["id"] != foto["id"]]
                    salvar_tudo()
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
