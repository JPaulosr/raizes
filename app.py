# -*- coding: utf-8 -*-
# app.py — Árvore Genealógica "Raízes" (v2 — fotos vinculadas a múltiplas pessoas)

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
.arv-header{text-align:center;padding:36px 20px 20px;}
.arv-header h1{font-family:'Cormorant Garamond',serif;font-size:2.6rem;font-weight:600;color:rgba(255,255,255,.92);margin:0 0 8px;}
.arv-header p{font-size:.85rem;color:rgba(255,255,255,.35);margin:0;}
.conector-v{width:2px;height:28px;background:rgba(255,255,255,.12);margin:0 auto;}
.casal-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:16px;text-align:center;position:relative;}
.casal-card.ativo{border-color:rgba(110,232,170,.45);background:rgba(110,232,170,.07);}
.casal-fotos{display:flex;justify-content:center;gap:8px;margin-bottom:10px;}
.pessoa-wrap{position:relative;display:inline-block;}
.pessoa-foto{width:56px;height:56px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,.15);display:block;}
.pessoa-foto-placeholder{width:56px;height:56px;border-radius:50%;background:rgba(255,255,255,.08);border:2px dashed rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:1.4rem;}
.pessoa-tooltip{visibility:hidden;opacity:0;position:absolute;bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);background:rgba(20,20,30,.95);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:5px 10px;font-size:12px;font-weight:500;color:rgba(255,255,255,.9);white-space:nowrap;z-index:10;transition:opacity .15s;pointer-events:none;}
.pessoa-wrap:hover .pessoa-tooltip{visibility:visible;opacity:1;}
.casal-nomes{font-family:'Cormorant Garamond',serif;font-size:.92rem;font-weight:600;font-style:italic;color:rgba(255,255,255,.8);line-height:1.4;margin-bottom:2px;}
.casal-rel{font-size:.7rem;color:rgba(255,255,255,.3);text-transform:uppercase;letter-spacing:.6px;}
.fotos-badge{position:absolute;top:-6px;right:-6px;background:#6ee8aa;color:#0a2a1a;border-radius:10px;font-size:10px;font-weight:700;padding:2px 7px;}
.det-panel{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:24px;}
.det-nome{font-family:'Cormorant Garamond',serif;font-size:1.7rem;font-weight:600;font-style:italic;color:rgba(255,255,255,.9);margin-bottom:4px;}
.det-rel{font-size:.78rem;color:rgba(255,255,255,.3);text-transform:uppercase;letter-spacing:.8px;margin-bottom:18px;}
.det-info{font-size:.82rem;color:rgba(255,255,255,.45);line-height:1.9;}
.foto-par{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:14px;overflow:hidden;margin-bottom:12px;}
.foto-header{padding:10px 16px;border-bottom:1px solid rgba(255,255,255,.07);display:flex;justify-content:space-between;align-items:center;}
.foto-tit{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:.95rem;color:rgba(255,255,255,.75);}
.foto-data{font-size:11px;color:rgba(255,255,255,.2);}
.foto-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:rgba(255,255,255,.06);}
.foto-lado{position:relative;}
.foto-lado img{width:100%;height:170px;object-fit:cover;display:block;}
.foto-lado.antiga img{filter:sepia(.2) brightness(.9);}
.foto-badge{position:absolute;bottom:8px;left:8px;font-size:10px;font-weight:500;letter-spacing:.7px;text-transform:uppercase;padding:3px 10px;border-radius:20px;}
.badge-a{background:rgba(200,170,100,.3);color:#e8c97a;}
.badge-r{background:rgba(100,200,150,.25);color:#6ee8aa;}
.pessoas-na-foto{padding:8px 16px;font-size:.75rem;color:rgba(255,255,255,.4);background:rgba(255,255,255,.02);}
.pessoas-na-foto span{background:rgba(255,255,255,.08);border-radius:10px;padding:2px 8px;margin-right:4px;font-size:.72rem;}
.empty-arv{text-align:center;padding:60px 20px;color:rgba(255,255,255,.2);}
.empty-pain{text-align:center;padding:32px 0;color:rgba(255,255,255,.2);font-size:.88rem;}
.acervo-tab{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px;cursor:pointer;}
.acervo-thumb img{width:52px;height:40px;object-fit:cover;border-radius:6px;}
.acervo-info{flex:1;}
.acervo-tit{font-family:'Cormorant Garamond',serif;font-size:.9rem;color:rgba(255,255,255,.8);font-style:italic;}
.acervo-pessoas{font-size:.72rem;color:rgba(255,255,255,.3);margin-top:2px;}
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.03)!important;border:1px dashed rgba(255,255,255,.15)!important;border-radius:10px!important;}
[data-testid="stTextInput"] input{background:rgba(255,255,255,.05)!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:8px!important;color:rgba(255,255,255,.85)!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── helpers HTML ──────────────────────────────────────────────────────
def div(cls, content, extra=""):
    return "<div" + (' class="'+cls+'"' if cls else "") + ((" "+extra) if extra else "") + ">" + content + "</div>"
def span(cls, content):
    return "<span" + (' class="'+cls+'"' if cls else "") + ">" + content + "</span>"

def pessoa_html(p):
    url   = p.get("foto_perfil", "")
    emoji = {"Pai":"👨","Mãe":"👩","Avô (paterno)":"👴","Avó (paterna)":"👵",
             "Avô (materno)":"👴","Avó (materna)":"👵","Bisavô":"🧓","Bisavó":"👵",
             "Eu":"🧑","Cônjuge":"💑","Irmão":"👦","Irmã":"👧","Filho":"👦","Filha":"👧",
             "Prima":"👩","Primo":"👦","Tia":"👩","Tio":"👨"}.get(p.get("relacao",""),"👤")
    if url:
        foto = '<img class="pessoa-foto" src="' + url + '">'
    else:
        foto = div("pessoa-foto-placeholder", emoji)
    tooltip = span("pessoa-tooltip", p.get("nome",""))
    return div("pessoa-wrap", foto + tooltip)

def casal_card_html(grupo, ativo):
    qtd_fotos = 0
    for p in grupo:
        qtd_fotos += len(p.get("foto_ids", []))
    badge   = span("fotos-badge", str(qtd_fotos)) if qtd_fotos else ""
    fotos_h = "".join(pessoa_html(p) for p in grupo)
    nomes   = " &amp; ".join(p["nome"].split()[0] for p in grupo)
    rels    = " · ".join(p.get("relacao","") for p in grupo)
    cls     = "casal-card ativo" if ativo else "casal-card"
    inner   = badge + div("casal-fotos", fotos_h) + div("casal-nomes", nomes) + div("casal-rel", rels)
    return div(cls, inner)

def det_panel_html(pessoa, qtd_fotos):
    nome  = pessoa.get("nome","")
    rel   = pessoa.get("relacao","")
    nasc  = pessoa.get("nascimento","")
    falec = pessoa.get("falecimento","")
    info  = ""
    if nasc:  info += "📅 " + nasc + "<br>"
    if falec: info += "✝️ " + falec + "<br>"
    info += ("📷 " + str(qtd_fotos) + " foto" + ("s" if qtd_fotos!=1 else "")) if qtd_fotos else "Sem fotos ainda"
    inner = div("det-nome", nome) + div("det-rel", rel) + div("det-info", info)
    return div("det-panel", inner)

def foto_par_html(foto, arvore):
    """Renderiza um par de fotos com lista de quem aparece."""
    tit      = foto.get("titulo","")
    data     = foto.get("data","")
    url_a    = foto.get("antiga","")
    url_r    = foto.get("restaurada","")
    ids_pess = foto.get("pessoas", [])
    nomes_pess = []
    for pid in ids_pess:
        p = next((x for x in arvore if x["id"]==pid), None)
        if p: nomes_pess.append(p["nome"].split()[0])

    header = div("foto-header", span("foto-tit", tit) + span("foto-data", data))
    img_a  = '<div class="foto-lado antiga"><img src="'+url_a+'"><span class="foto-badge badge-a">Antiga</span></div>'
    img_r  = '<div class="foto-lado"><img src="'+url_r+'"><span class="foto-badge badge-r">✨ Rest.</span></div>'
    grid   = div("foto-grid", img_a + img_r)
    pessoas_html = ""
    if nomes_pess:
        tags = "".join(span("", n) for n in nomes_pess)
        pessoas_html = div("pessoas-na-foto", "👥 Nesta foto: " + tags)
    return div("foto-par", header + grid + pessoas_html)

# ── Cloudinary ────────────────────────────────────────────────────────
def _s(k, d=""):
    try:
        v = st.secrets.get(k, d); return str(v).strip() if v else d
    except: return os.environ.get(k, d)

CLOUD = _s("CLOUDINARY_CLOUD_NAME","db8ipmete")
AKEY  = _s("CLOUDINARY_API_KEY")
ASEC  = _s("CLOUDINARY_API_SECRET")

def _upload(fb, fname, folder="Fotos antigas"):
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
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["secure_url"]

# ── Google Sheets ─────────────────────────────────────────────────────
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
    try:    return sh.worksheet("Raizes_Arvore")
    except:
        ws = sh.add_worksheet("Raizes_Arvore", rows=10, cols=2)
        ws.update("A1", [["arvore", "{}"]])
        return ws

@st.cache_data(ttl=10, show_spinner=False)
def _carregar():
    try:
        ws  = _get_ws()
        raw = ws.acell("B1").value or "{}"
        d   = json.loads(raw)
        # d["arvore"]  → lista de pessoas
        # d["acervo"]  → lista de fotos (estrutura nova, substitui "galeria")
        arvore = d.get("arvore", [])
        # migração: se pessoa ainda usa "fotos" antigo, converte
        for p in arvore:
            if "fotos" in p and "foto_ids" not in p:
                p["foto_ids"] = []  # fotos antigas ficam no acervo global
        acervo = d.get("acervo", d.get("galeria", []))
        # garante campo "pessoas" em cada foto do acervo
        for f in acervo:
            if "pessoas" not in f:
                f["pessoas"] = []
            if "id" not in f:
                f["id"] = "f" + str(int(time.time()*1000))
        return arvore, acervo
    except Exception as e:
        st.error("Erro ao carregar: " + str(e))
        return [], []

def _salvar(arvore, acervo):
    try:
        ws  = _get_ws()
        ws.update("B1", [[json.dumps({"arvore": arvore, "acervo": acervo}, ensure_ascii=False)]])
        _carregar.clear()
    except Exception as e:
        st.error("Erro ao salvar: " + str(e))

# ── Session State ─────────────────────────────────────────────────────
if "arvore" not in st.session_state or "acervo" not in st.session_state:
    arv, acv = _carregar()
    st.session_state.arvore = arv
    st.session_state.acervo = acv
if "ativo" not in st.session_state: st.session_state.ativo = None
if "modo"  not in st.session_state: st.session_state.modo  = "ver"
if "aba"   not in st.session_state: st.session_state.aba   = "arvore"

arvore = st.session_state.arvore
acervo = st.session_state.acervo

NIVEL = {"Bisavô":0,"Bisavó":0,"Avô (paterno)":1,"Avó (paterna)":1,
         "Avô (materno)":1,"Avó (materna)":1,"Pai":2,"Mãe":2,
         "Eu":3,"Cônjuge":3,"Irmão":3,"Irmã":3,"Primo":3,"Prima":3,
         "Tio":2,"Tia":2,"Filho":4,"Filha":4,"Outro":3}

PARES = [{"Pai","Mãe"},{"Avô (paterno)","Avó (paterna)"},
         {"Avô (materno)","Avó (materna)"},{"Bisavô","Bisavó"},{"Eu","Cônjuge"}]

def _nivel(p): return NIVEL.get(p.get("relacao","Outro"), 3)

def _agrupar(pessoas):
    usados, grupos = set(), []
    for p in pessoas:
        if p["id"] in usados: continue
        rel = p.get("relacao","Outro")
        par = None
        for ps in PARES:
            if rel in ps:
                outro = list(ps - {rel})[0]
                for q in pessoas:
                    if q["id"] not in usados and q.get("relacao")==outro:
                        par = q; break
                break
        if par:
            grupos.append([p, par]); usados.add(p["id"]); usados.add(par["id"])
        else:
            grupos.append([p]); usados.add(p["id"])
    return grupos

def _fotos_da_pessoa(pid):
    """Retorna fotos do acervo onde essa pessoa aparece."""
    return [f for f in acervo if pid in f.get("pessoas", [])]

# ── Header ────────────────────────────────────────────────────────────
st.markdown(
    '<div class="arv-header"><h1>🌳 Raízes</h1>'
    '<p>Árvore Genealógica da Família</p></div>',
    unsafe_allow_html=True
)

# ── Abas principais ───────────────────────────────────────────────────
tab_arv, tab_acervo = st.tabs(["🌳 Árvore", "📷 Acervo de Fotos"])

# ════════════════════════════════════════════════════════════════════════
# ABA 1 — ÁRVORE
# ════════════════════════════════════════════════════════════════════════
with tab_arv:
    col_arv, col_pain = st.columns([2.3, 1], gap="large")

    # ── Árvore (esquerda) ─────────────────────────────────────────────
    with col_arv:
        if not arvore:
            st.markdown(
                '<div class="empty-arv">'
                '<div style="font-size:3rem;opacity:.25;margin-bottom:14px">🌳</div>'
                '<p style="font-size:14px">Árvore vazia. Adicione a primeira pessoa →</p>'
                '</div>', unsafe_allow_html=True
            )
        else:
            niveis_dict = {}
            for p in arvore:
                niveis_dict.setdefault(_nivel(p), []).append(p)

            for n in sorted(niveis_dict.keys()):
                if n > min(niveis_dict.keys()):
                    st.markdown('<div class="conector-v"></div>', unsafe_allow_html=True)
                grupos = _agrupar(niveis_dict[n])
                cols   = st.columns(max(len(grupos), 1))
                for col, grupo in zip(cols, grupos):
                    with col:
                        ativo = st.session_state.ativo in [p["id"] for p in grupo]
                        st.markdown(casal_card_html(grupo, ativo), unsafe_allow_html=True)
                        if len(grupo) == 2:
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button(grupo[0]["nome"].split()[0], key="s_"+grupo[0]["id"], use_container_width=True):
                                    st.session_state.ativo = grupo[0]["id"]
                                    st.session_state.modo  = "ver"
                                    st.rerun()
                            with b2:
                                if st.button(grupo[1]["nome"].split()[0], key="s_"+grupo[1]["id"], use_container_width=True):
                                    st.session_state.ativo = grupo[1]["id"]
                                    st.session_state.modo  = "ver"
                                    st.rerun()
                        else:
                            if st.button("Ver fotos", key="s_"+grupo[0]["id"], use_container_width=True):
                                st.session_state.ativo = grupo[0]["id"]
                                st.session_state.modo  = "ver"
                                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕  Adicionar pessoa", use_container_width=True):
            st.session_state.modo  = "add"
            st.session_state.ativo = None
            st.rerun()

    # ── Painel direito ────────────────────────────────────────────────
    with col_pain:

        # MODO: Adicionar pessoa
        if st.session_state.modo == "add":
            st.markdown('<div class="det-panel"><div class="det-nome">Nova pessoa</div></div>', unsafe_allow_html=True)
            nome_n = st.text_input("Nome completo", key="nome_n")
            rel_n  = st.selectbox("Relação", list(NIVEL.keys()), key="rel_n")
            nasc_n = st.text_input("Nascimento", placeholder="Ex: 12/04/1945", key="nasc_n")
            falec_n= st.text_input("Falecimento (opcional)", key="falec_n")
            gen_n  = st.radio("Gênero", ["Masculino","Feminino"], horizontal=True, key="gen_n")
            st.caption("Foto de perfil (opcional)")
            fp_f   = st.file_uploader("", type=["jpg","jpeg","png","webp"], key="fp_n", label_visibility="collapsed")
            if fp_f: st.image(fp_f, use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Salvar", use_container_width=True, type="primary"):
                    if not nome_n.strip():
                        st.warning("Digite o nome.")
                    else:
                        url_p = ""
                        if fp_f and AKEY:
                            with st.spinner("Enviando foto..."):
                                fp_f.seek(0)
                                url_p = _upload(fp_f.read(), fp_f.name)
                        nova = {
                            "id":         "p" + str(int(time.time()*1000)),
                            "nome":       nome_n.strip(),
                            "relacao":    rel_n,
                            "genero":     "F" if gen_n=="Feminino" else "M",
                            "nascimento": nasc_n.strip(),
                            "falecimento":falec_n.strip(),
                            "foto_perfil":url_p,
                            "foto_ids":   []
                        }
                        st.session_state.arvore.append(nova)
                        _salvar(st.session_state.arvore, st.session_state.acervo)
                        st.session_state.ativo = nova["id"]
                        st.session_state.modo  = "ver"
                        st.rerun()
            with c2:
                if st.button("Cancelar", use_container_width=True):
                    st.session_state.modo = "ver"
                    st.rerun()

        # MODO: Ver pessoa
        elif st.session_state.ativo:
            pessoa = next((p for p in arvore if p["id"]==st.session_state.ativo), None)
            if not pessoa:
                st.session_state.ativo = None
                st.rerun()

            fotos_pessoa = _fotos_da_pessoa(pessoa["id"])
            st.markdown(det_panel_html(pessoa, len(fotos_pessoa)), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # Fotos onde aparece
            if fotos_pessoa:
                st.markdown("**📷 Fotos de " + pessoa["nome"].split()[0] + "**")
                for foto in fotos_pessoa:
                    st.markdown(foto_par_html(foto, arvore), unsafe_allow_html=True)
                    if st.button("🔗 Desvincular esta foto", key="desv_"+foto["id"]+"_"+pessoa["id"], use_container_width=True):
                        foto["pessoas"] = [x for x in foto.get("pessoas",[]) if x != pessoa["id"]]
                        _salvar(st.session_state.arvore, st.session_state.acervo)
                        st.rerun()

            # Vincular foto existente do acervo
            outras_fotos = [f for f in acervo if pessoa["id"] not in f.get("pessoas",[])]
            if outras_fotos:
                with st.expander("🔗 Vincular foto existente do acervo"):
                    opcoes = {f["titulo"] + " (" + f.get("data","") + ")": f["id"] for f in outras_fotos}
                    sel = st.multiselect("Selecione fotos para vincular", list(opcoes.keys()), key="vinc_"+pessoa["id"])
                    if st.button("✅ Vincular selecionadas", use_container_width=True, type="primary", key="btn_vinc_"+pessoa["id"]):
                        for titulo_op, fid in opcoes.items():
                            if titulo_op in sel:
                                foto_obj = next((f for f in acervo if f["id"]==fid), None)
                                if foto_obj and pessoa["id"] not in foto_obj.get("pessoas",[]):
                                    foto_obj.setdefault("pessoas",[]).append(pessoa["id"])
                        _salvar(st.session_state.arvore, st.session_state.acervo)
                        st.success("✅ Vinculado!")
                        st.rerun()

            # Adicionar nova foto (vai para o acervo e já vincula)
            with st.expander("➕ Adicionar nova foto de " + pessoa["nome"].split()[0]):
                tit = st.text_input("Nome da foto", placeholder="Ex: Casamento 1972", key="tit_f_"+pessoa["id"])
                st.caption("Quem mais aparece nessa foto?")
                outros_nomes = {p["nome"]: p["id"] for p in arvore if p["id"] != pessoa["id"]}
                tambem = st.multiselect("Outras pessoas na foto", list(outros_nomes.keys()), key="tambem_"+pessoa["id"])
                fa = st.file_uploader("🕰️ Foto antiga",    type=["jpg","jpeg","png","webp"], key="fa_"+pessoa["id"])
                fr = st.file_uploader("✨ Foto restaurada", type=["jpg","jpeg","png","webp"], key="fr_"+pessoa["id"])
                if fa: st.image(fa, use_container_width=True)
                if fr: st.image(fr, use_container_width=True)
                if st.button("💾 Salvar foto no acervo", use_container_width=True, type="primary", key="btn_sf_"+pessoa["id"]):
                    if not fa or not fr:
                        st.warning("Selecione as duas fotos.")
                    elif not AKEY:
                        st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
                    else:
                        with st.spinner("Enviando fotos..."):
                            fa.seek(0); fr.seek(0)
                            ua = _upload(fa.read(), fa.name)
                            ur = _upload(fr.read(), fr.name)
                            pessoas_na_foto = [pessoa["id"]] + [outros_nomes[n] for n in tambem]
                            nova_foto = {
                                "id":         "f" + str(int(time.time()*1000)),
                                "titulo":     tit.strip() or "Sem título",
                                "antiga":     ua,
                                "restaurada": ur,
                                "data":       datetime.now().strftime("%d/%m/%Y"),
                                "pessoas":    pessoas_na_foto
                            }
                            st.session_state.acervo.insert(0, nova_foto)
                            _salvar(st.session_state.arvore, st.session_state.acervo)
                            st.success("✅ Salvo no acervo!")
                            st.rerun()

            with st.expander("⚙️ Opções"):
                if st.button("🗑️ Remover " + pessoa["nome"].split()[0] + " da árvore", use_container_width=True):
                    st.session_state.arvore = [p for p in st.session_state.arvore if p["id"] != pessoa["id"]]
                    _salvar(st.session_state.arvore, st.session_state.acervo)
                    st.session_state.ativo = None
                    st.rerun()

        # MODO: Nenhum selecionado
        else:
            st.markdown(
                '<div class="det-panel"><div class="empty-pain">'
                '<div style="font-size:2rem;opacity:.2;margin-bottom:10px">👆</div>'
                '<p>Clique no nome de uma pessoa<br>para ver as fotos dela</p>'
                '</div></div>', unsafe_allow_html=True
            )

# ════════════════════════════════════════════════════════════════════════
# ABA 2 — ACERVO COMPLETO DE FOTOS
# ════════════════════════════════════════════════════════════════════════
with tab_acervo:
    st.markdown("<br>", unsafe_allow_html=True)

    # Upload de nova foto no acervo (sem vincular a ninguém ainda, ou já vinculando)
    with st.expander("➕ Adicionar foto ao acervo", expanded=not bool(acervo)):
        tit_a = st.text_input("Nome da foto", placeholder="Ex: Família reunida em 1980", key="tit_acervo")
        st.caption("Quem aparece nessa foto?")
        if arvore:
            nomes_todos = {p["nome"]: p["id"] for p in arvore}
            selecionados = st.multiselect("Selecione as pessoas da foto", list(nomes_todos.keys()), key="pessoas_acervo")
        else:
            selecionados = []
            st.info("Adicione pessoas na árvore primeiro para vinculá-las às fotos.")
        fa_a = st.file_uploader("🕰️ Foto antiga",    type=["jpg","jpeg","png","webp"], key="fa_acervo")
        fr_a = st.file_uploader("✨ Foto restaurada", type=["jpg","jpeg","png","webp"], key="fr_acervo")
        if fa_a: st.image(fa_a, use_container_width=True)
        if fr_a: st.image(fr_a, use_container_width=True)
        if st.button("💾 Adicionar ao acervo", use_container_width=True, type="primary", key="btn_acervo"):
            if not fa_a or not fr_a:
                st.warning("Selecione as duas fotos.")
            elif not AKEY:
                st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
            else:
                with st.spinner("Enviando fotos..."):
                    fa_a.seek(0); fr_a.seek(0)
                    ua = _upload(fa_a.read(), fa_a.name)
                    ur = _upload(fr_a.read(), fr_a.name)
                    ids_selecionados = [nomes_todos[n] for n in selecionados] if arvore else []
                    nova_foto = {
                        "id":         "f" + str(int(time.time()*1000)),
                        "titulo":     tit_a.strip() or "Sem título",
                        "antiga":     ua,
                        "restaurada": ur,
                        "data":       datetime.now().strftime("%d/%m/%Y"),
                        "pessoas":    ids_selecionados
                    }
                    st.session_state.acervo.insert(0, nova_foto)
                    _salvar(st.session_state.arvore, st.session_state.acervo)
                    st.success("✅ Foto adicionada ao acervo!")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Filtro por pessoa
    filtro_pessoa = None
    if arvore:
        opcoes_filtro = ["Todas as fotos"] + [p["nome"] for p in arvore]
        escolha = st.selectbox("🔍 Filtrar por pessoa", opcoes_filtro, key="filtro_acervo")
        if escolha != "Todas as fotos":
            filtro_pessoa = next((p["id"] for p in arvore if p["nome"]==escolha), None)

    fotos_exibir = acervo if not filtro_pessoa else [f for f in acervo if filtro_pessoa in f.get("pessoas",[])]

    if not fotos_exibir:
        st.markdown(
            '<div style="text-align:center;padding:48px 20px;color:rgba(255,255,255,.2);">'
            '<div style="font-size:2.5rem;opacity:.3;margin-bottom:12px">🖼️</div>'
            '<p style="font-size:14px">Nenhuma foto aqui ainda.</p></div>',
            unsafe_allow_html=True
        )
    else:
        st.caption(str(len(fotos_exibir)) + " foto(s) encontrada(s)")
        for i, foto in enumerate(fotos_exibir):
            st.markdown(foto_par_html(foto, arvore), unsafe_allow_html=True)

            # Editar vínculos de pessoas
            with st.expander("👥 Editar pessoas nesta foto"):
                if arvore:
                    nomes_todos2 = {p["nome"]: p["id"] for p in arvore}
                    ids_atuais = foto.get("pessoas", [])
                    nomes_atuais = [p["nome"] for p in arvore if p["id"] in ids_atuais]
                    novos_nomes = st.multiselect(
                        "Quem aparece aqui?", list(nomes_todos2.keys()),
                        default=nomes_atuais, key="ed_pess_"+foto["id"]
                    )
                    if st.button("💾 Salvar vínculos", key="sv_pess_"+foto["id"], use_container_width=True):
                        foto["pessoas"] = [nomes_todos2[n] for n in novos_nomes]
                        _salvar(st.session_state.arvore, st.session_state.acervo)
                        st.success("✅ Salvo!")
                        st.rerun()
                else:
                    st.info("Adicione pessoas à árvore para vincular.")

            b1, b2, b3, _ = st.columns([1,1,1,2])
            with b1: st.link_button("🔗 Antiga",     foto["antiga"],     use_container_width=True)
            with b2: st.link_button("🔗 Restaurada", foto["restaurada"], use_container_width=True)
            with b3:
                if st.button("🗑️ Excluir", key="del_ac_"+str(i), use_container_width=True):
                    st.session_state.acervo = [f for f in st.session_state.acervo if f["id"] != foto["id"]]
                    _salvar(st.session_state.arvore, st.session_state.acervo)
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
