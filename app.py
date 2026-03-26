# -*- coding: utf-8 -*-
# app.py — Árvore Genealógica

import streamlit as st
import json, os, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Raízes", page_icon="🌳", layout="wide")

# CSS separado — sem f-string
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
.pessoa-placeholder{width:56px;height:56px;border-radius:50%;background:rgba(255,255,255,.08);border:2px dashed rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:1.4rem;}
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
.empty-arv{text-align:center;padding:60px 20px;color:rgba(255,255,255,.2);}
.empty-pain{text-align:center;padding:32px 0;color:rgba(255,255,255,.2);font-size:.88rem;}
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.03)!important;border:1px dashed rgba(255,255,255,.15)!important;border-radius:10px!important;}
[data-testid="stTextInput"] input{background:rgba(255,255,255,.05)!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:8px!important;color:rgba(255,255,255,.85)!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── helpers de HTML (strings puras, sem f-string no momento da renderização) ──
def h(tag, cls, content, extra=""):
    return "<" + tag + (' class="' + cls + '"' if cls else "") + ((" " + extra) if extra else "") + ">" + content + "</" + tag + ">"

def div(cls, content, extra=""):  return h("div", cls, content, extra)
def span(cls, content):           return h("span", cls, content)

def pessoa_html(p):
    url   = p.get("foto_perfil", "")
    emoji = {"Pai":"👨","Mãe":"👩","Avô (paterno)":"👴","Avó (paterna)":"👵",
             "Avô (materno)":"👴","Avó (materna)":"👵","Bisavô":"🧓","Bisavó":"👵",
             "Eu":"🧑","Cônjuge":"💑","Irmão":"👦","Irmã":"👧","Filho":"👦","Filha":"👧"}.get(p.get("relacao",""),"👤")
    nome  = p.get("nome","")
    if url:
        foto = '<img class="pessoa-foto" src="' + url + '">'
    else:
        foto = div("pessoa-foto-placeholder", emoji)
    tooltip = span("pessoa-tooltip", nome)
    return div("pessoa-wrap", foto + tooltip)

def casal_card_html(grupo, ativo):
    ids       = [p["id"] for p in grupo]
    qtd_fotos = sum(len(p.get("fotos",[])) for p in grupo)
    badge     = span("fotos-badge", str(qtd_fotos)) if qtd_fotos else ""
    fotos_h   = "".join(pessoa_html(p) for p in grupo)
    nomes     = " &amp; ".join(p["nome"].split()[0] for p in grupo)
    rels      = " · ".join(p.get("relacao","") for p in grupo)
    cls       = "casal-card ativo" if ativo else "casal-card"
    inner     = badge + div("casal-fotos", fotos_h) + div("casal-nomes", nomes) + div("casal-rel", rels)
    return div(cls, inner)

def det_panel_html(pessoa):
    nome  = pessoa.get("nome","")
    rel   = pessoa.get("relacao","")
    nasc  = pessoa.get("nascimento","")
    falec = pessoa.get("falecimento","")
    fotos = pessoa.get("fotos",[])
    info  = ""
    if nasc:  info += "📅 " + nasc + "<br>"
    if falec: info += "✝️ " + falec + "<br>"
    info += ("📷 " + str(len(fotos)) + " foto" + ("s" if len(fotos)!=1 else "")) if fotos else "Sem fotos ainda"
    inner = div("det-nome", nome) + div("det-rel", rel) + div("det-info", info)
    return div("det-panel", inner)

def foto_par_html(foto):
    tit   = foto.get("titulo","")
    data  = foto.get("data","")
    url_a = foto.get("antiga","")
    url_r = foto.get("restaurada","")
    header = div("foto-header",
        span("foto-tit", tit) + span("foto-data", data))
    img_a  = '<div class="foto-lado antiga"><img src="' + url_a + '"><span class="foto-badge badge-a">Antiga</span></div>'
    img_r  = '<div class="foto-lado"><img src="' + url_r + '"><span class="foto-badge badge-r">✨ Rest.</span></div>'
    grid   = div("foto-grid", img_a + img_r)
    return div("foto-par", header + grid)

# ── Cloudinary ──────────────────────────────────────────────────────────────
def _s(k, d=""):
    try:
        v = st.secrets.get(k, d)
        return str(v).strip() if v else d
    except:
        return os.environ.get(k, d)

CLOUD = _s("CLOUDINARY_CLOUD_NAME","db8ipmete")
AKEY  = _s("CLOUDINARY_API_KEY")
ASEC  = _s("CLOUDINARY_API_SECRET")

def _upload(fb, fname, folder="Fotos antigas"):
    ts  = str(int(time.time()))
    pid = folder + "/" + Path(fname).stem + "_" + ts
    sig = hashlib.sha1((
        "folder=" + folder + "&public_id=" + pid + "&timestamp=" + ts + ASEC
    ).encode()).hexdigest()
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

# ── Google Sheets ────────────────────────────────────────────────────────────
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
        ws.update("A1", [["arvore", "{}"]])
        return ws

@st.cache_data(ttl=10, show_spinner=False)
def _carregar():
    try:
        ws  = _get_ws()
        raw = ws.acell("B1").value or "{}"
        d   = json.loads(raw)
        return d.get("arvore",[]), d.get("galeria",[])
    except Exception as e:
        st.error("Erro ao carregar: " + str(e))
        return [], []

def _salvar(arvore, galeria=None):
    try:
        if galeria is None:
            _, galeria = _carregar()
        ws  = _get_ws()
        ws.update("B1", [[json.dumps({"arvore":arvore,"galeria":galeria or []},ensure_ascii=False)]])
        _carregar.clear()
    except Exception as e:
        st.error("Erro ao salvar: " + str(e))

# ── Session State ────────────────────────────────────────────────────────────
if "arvore" not in st.session_state:
    arv, gal = _carregar()
    st.session_state.arvore  = arv
    st.session_state.galeria = gal
if "ativo" not in st.session_state: st.session_state.ativo = None
if "modo"  not in st.session_state: st.session_state.modo  = "ver"

arvore = st.session_state.arvore

NIVEL = {"Bisavô":0,"Bisavó":0,"Avô (paterno)":1,"Avó (paterna)":1,
         "Avô (materno)":1,"Avó (materna)":1,"Pai":2,"Mãe":2,
         "Eu":3,"Cônjuge":3,"Irmão":3,"Irmã":3,"Filho":4,"Filha":4,"Outro":3}

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

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="arv-header"><h1>🌳 Árvore Genealógica</h1>'
    '<p>Passe o mouse para ver o nome · Clique para ver as fotos</p></div>',
    unsafe_allow_html=True
)

col_arv, col_pain = st.columns([2.3, 1], gap="large")

# ── ÁRVORE ───────────────────────────────────────────────────────────────────
with col_arv:
    if not arvore:
        st.markdown(
            '<div class="empty-arv">'
            '<div style="font-size:3rem;opacity:.25;margin-bottom:14px">🌳</div>'
            '<p style="font-size:14px">Árvore vazia. Adicione a primeira pessoa →</p>'
            '</div>',
            unsafe_allow_html=True
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
                    ids_g = [p["id"] for p in grupo]
                    ativo = st.session_state.ativo in ids_g
                    st.markdown(casal_card_html(grupo, ativo), unsafe_allow_html=True)

                    if len(grupo) == 2:
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button(grupo[0]["nome"].split()[0],
                                         key="s_"+grupo[0]["id"], use_container_width=True):
                                st.session_state.ativo = grupo[0]["id"]
                                st.session_state.modo  = "ver"
                                st.rerun()
                        with b2:
                            if st.button(grupo[1]["nome"].split()[0],
                                         key="s_"+grupo[1]["id"], use_container_width=True):
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

# ── PAINEL DIREITO ───────────────────────────────────────────────────────────
with col_pain:

    # MODO: Adicionar
    if st.session_state.modo == "add":
        st.markdown('<div class="det-panel"><div class="det-nome">Nova pessoa</div></div>',
                    unsafe_allow_html=True)
        nome_n = st.text_input("Nome completo", key="nome_n")
        rel_n  = st.selectbox("Relação", list(NIVEL.keys()), key="rel_n")
        nasc_n = st.text_input("Nascimento", placeholder="Ex: 12/04/1945", key="nasc_n")
        falec_n= st.text_input("Falecimento (opcional)", key="falec_n")
        gen_n  = st.radio("Gênero", ["Masculino","Feminino"], horizontal=True, key="gen_n")
        st.caption("Foto de perfil (opcional)")
        fp_f   = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                                  key="fp_n", label_visibility="collapsed")
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
                        "fotos":      []
                    }
                    st.session_state.arvore.append(nova)
                    _salvar(st.session_state.arvore)
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

        st.markdown(det_panel_html(pessoa), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        fotos = pessoa.get("fotos", [])
        if fotos:
            st.markdown("**📷 Fotos de " + pessoa["nome"].split()[0] + "**")
            for j, foto in enumerate(fotos):
                st.markdown(foto_par_html(foto), unsafe_allow_html=True)
                if st.button("🗑️ Remover foto", key="delf_"+str(j), use_container_width=True):
                    pessoa["fotos"].pop(j)
                    _salvar(st.session_state.arvore)
                    st.rerun()

        with st.expander("➕ Adicionar foto de " + pessoa["nome"].split()[0]):
            tit = st.text_input("Nome da foto", placeholder="Ex: Casamento 1972", key="tit_f")
            fa  = st.file_uploader("🕰️ Foto antiga",    type=["jpg","jpeg","png","webp"], key="fa")
            fr  = st.file_uploader("✨ Foto restaurada", type=["jpg","jpeg","png","webp"], key="fr")
            if fa: st.image(fa, use_container_width=True)
            if fr: st.image(fr, use_container_width=True)
            if st.button("💾 Salvar foto", use_container_width=True, type="primary", key="btn_sf"):
                if not fa or not fr:
                    st.warning("Selecione as duas fotos.")
                elif not AKEY:
                    st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
                else:
                    with st.spinner("Enviando fotos..."):
                        fa.seek(0); fr.seek(0)
                        ua = _upload(fa.read(), fa.name)
                        ur = _upload(fr.read(), fr.name)
                        pessoa["fotos"].append({
                            "titulo":     tit.strip() or "Sem título",
                            "antiga":     ua,
                            "restaurada": ur,
                            "data":       datetime.now().strftime("%d/%m/%Y")
                        })
                        _salvar(st.session_state.arvore)
                        st.success("✅ Salvo!")
                        st.rerun()

        with st.expander("⚙️ Opções"):
            if st.button("🗑️ Remover " + pessoa["nome"].split()[0] + " da árvore",
                         use_container_width=True):
                st.session_state.arvore = [
                    p for p in st.session_state.arvore if p["id"] != pessoa["id"]
                ]
                _salvar(st.session_state.arvore)
                st.session_state.ativo = None
                st.rerun()

    # MODO: Nenhum selecionado
    else:
        st.markdown(
            '<div class="det-panel">'
            '<div class="empty-pain">'
            '<div style="font-size:2rem;opacity:.2;margin-bottom:10px">👆</div>'
            '<p>Clique no nome de uma pessoa<br>para ver as fotos dela</p>'
            '</div></div>',
            unsafe_allow_html=True
        )
