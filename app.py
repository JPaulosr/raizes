# -*- coding: utf-8 -*-
# app.py — Árvore Genealógica com casais, fotos compartilhadas e Google Sheets

import streamlit as st
import json, os, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Raízes — Árvore Genealógica", page_icon="🌳", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
footer{display:none!important} #MainMenu{display:none!important} header{display:none!important}

.arvore-header { text-align:center; padding:36px 20px 20px; }
.arvore-header h1 { font-family:'Cormorant Garamond',serif; font-size:2.6rem; font-weight:600; color:rgba(255,255,255,.92); margin:0 0 8px; }
.arvore-header p  { font-size:.85rem; color:rgba(255,255,255,.35); margin:0; }

/* Nível da árvore */
.nivel-wrap { display:flex; justify-content:center; gap:12px; flex-wrap:wrap; margin:8px 0; }
.conector-v { width:2px; height:28px; background:rgba(255,255,255,.12); margin:0 auto; }

/* Card de CASAL */
.casal-card {
    background:rgba(255,255,255,.05);
    border:1px solid rgba(255,255,255,.1);
    border-radius:18px; padding:16px;
    min-width:200px; max-width:240px;
    text-align:center; position:relative;
}
.casal-card.ativo {
    border-color:rgba(110,232,170,.45);
    background:rgba(110,232,170,.07);
}

/* Fotos do casal lado a lado */
.casal-fotos {
    display:flex; justify-content:center;
    gap:8px; margin-bottom:10px; position:relative;
}
.pessoa-wrap {
    position:relative; cursor:pointer;
}
.pessoa-foto {
    width:56px; height:56px; border-radius:50%;
    object-fit:cover; border:2px solid rgba(255,255,255,.15);
    display:block;
}
.pessoa-placeholder {
    width:56px; height:56px; border-radius:50%;
    background:rgba(255,255,255,.08);
    border:2px dashed rgba(255,255,255,.2);
    display:flex; align-items:center;
    justify-content:center; font-size:1.4rem;
}
/* Tooltip com nome ao hover */
.pessoa-tooltip {
    visibility:hidden; opacity:0;
    position:absolute; bottom:calc(100% + 6px);
    left:50%; transform:translateX(-50%);
    background:rgba(20,20,30,.95);
    border:1px solid rgba(255,255,255,.15);
    border-radius:8px; padding:5px 10px;
    font-size:12px; font-weight:500;
    color:rgba(255,255,255,.9);
    white-space:nowrap; z-index:10;
    transition:opacity .15s;
    pointer-events:none;
}
.pessoa-wrap:hover .pessoa-tooltip {
    visibility:visible; opacity:1;
}

.casal-nomes {
    font-family:'Cormorant Garamond',serif;
    font-size:.92rem; font-weight:600; font-style:italic;
    color:rgba(255,255,255,.8); line-height:1.4;
    margin-bottom:2px;
}
.casal-rel {
    font-size:.7rem; color:rgba(255,255,255,.3);
    text-transform:uppercase; letter-spacing:.6px;
}
.fotos-badge {
    position:absolute; top:-6px; right:-6px;
    background:#6ee8aa; color:#0a2a1a;
    border-radius:10px; font-size:10px;
    font-weight:700; padding:2px 7px;
}

/* Painel direito */
.detalhe-panel {
    background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.1);
    border-radius:20px; padding:24px;
}
.detalhe-nome {
    font-family:'Cormorant Garamond',serif;
    font-size:1.7rem; font-weight:600; font-style:italic;
    color:rgba(255,255,255,.9); margin-bottom:4px;
}
.detalhe-rel { font-size:.78rem; color:rgba(255,255,255,.3); text-transform:uppercase; letter-spacing:.8px; margin-bottom:18px; }
.foto-par { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08); border-radius:14px; overflow:hidden; margin-bottom:12px; }
.foto-par-header { padding:10px 16px; border-bottom:1px solid rgba(255,255,255,.07); display:flex; justify-content:space-between; align-items:center; }
.foto-par-titulo { font-family:'Cormorant Garamond',serif; font-style:italic; font-size:.95rem; color:rgba(255,255,255,.75); }
.foto-grid { display:grid; grid-template-columns:1fr 1fr; gap:1px; background:rgba(255,255,255,.06); }
.foto-lado { position:relative; }
.foto-lado img { width:100%; height:170px; object-fit:cover; display:block; }
.foto-lado.antiga img { filter:sepia(.2) brightness(.9); }
.foto-badge { position:absolute; bottom:8px; left:8px; font-size:10px; font-weight:500; letter-spacing:.7px; text-transform:uppercase; padding:3px 10px; border-radius:20px; }
.badge-antiga { background:rgba(200,170,100,.3); color:#e8c97a; }
.badge-rest   { background:rgba(100,200,150,.25); color:#6ee8aa; }
.divisor { display:flex; align-items:center; gap:12px; margin:12px 0; color:rgba(255,255,255,.2); font-size:11px; text-transform:uppercase; letter-spacing:1px; }
.divisor::before,.divisor::after { content:''; flex:1; height:1px; background:rgba(255,255,255,.08); }
.empty-panel { text-align:center; padding:32px 0; color:rgba(255,255,255,.2); font-size:.88rem; }

[data-testid="stFileUploaderDropzone"] { background:rgba(255,255,255,.03)!important; border:1px dashed rgba(255,255,255,.15)!important; border-radius:10px!important; }
[data-testid="stTextInput"] input { background:rgba(255,255,255,.05)!important; border:1px solid rgba(255,255,255,.12)!important; border-radius:8px!important; color:rgba(255,255,255,.85)!important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# CLOUDINARY
# ═══════════════════════════════════════════════════
def _secret(k, d=""):
    try:
        v = st.secrets.get(k, d)
        return str(v).strip() if v else d
    except:
        return os.environ.get(k, d)

CLOUD = _secret("CLOUDINARY_CLOUD_NAME","db8ipmete")
AKEY  = _secret("CLOUDINARY_API_KEY")
ASEC  = _secret("CLOUDINARY_API_SECRET")

def _upload(fb, fname, folder="Fotos antigas"):
    ts  = str(int(time.time()))
    pid = f"{folder}/{Path(fname).stem}_{ts}"
    sig = hashlib.sha1(f"folder={folder}&public_id={pid}&timestamp={ts}{ASEC}".encode()).hexdigest()
    b   = "----B" + ts
    body = (
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname}\"\r\nContent-Type: image/jpeg\r\n\r\n"
    ).encode() + fb + (
        f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"api_key\"\r\n\r\n{AKEY}\r\n"
        f"--{b}\r\nContent-Disposition: form-data; name=\"timestamp\"\r\n\r\n{ts}\r\n"
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\n{folder}\r\n"
        f"--{b}\r\nContent-Disposition: form-data; name=\"public_id\"\r\n\r\n{pid}\r\n"
        f"--{b}\r\nContent-Disposition: form-data; name=\"signature\"\r\n\r\n{sig}\r\n"
        f"--{b}--\r\n"
    ).encode()
    req = urllib.request.Request(
        f"https://api.cloudinary.com/v1_1/{CLOUD}/image/upload",
        data=body, headers={"Content-Type": f"multipart/form-data; boundary={b}"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["secure_url"]

# ═══════════════════════════════════════════════════
# PERSISTÊNCIA: Google Sheets como banco de dados
# A árvore inteira fica numa célula A1 como JSON.
# Sem dependência de arquivo local que some no Cloud.
# ═══════════════════════════════════════════════════
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def _gc():
    info = st.secrets["GCP_SERVICE_ACCOUNT"]
    creds = Credentials.from_service_account_info(
        dict(info), scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    )
    return gspread.authorize(creds)

def _get_ws():
    url = _secret("PLANILHA_URL_RAIZES") or _secret("PLANILHA_URL")
    gc  = _gc()
    sh  = gc.open_by_url(url) if url.startswith("http") else gc.open_by_key(url)
    try:
        return sh.worksheet("Raizes_Arvore")
    except:
        ws = sh.add_worksheet("Raizes_Arvore", rows=10, cols=2)
        ws.update("A1", [["arvore"], ["{}"]])
        return ws

@st.cache_data(ttl=10, show_spinner=False)
def _carregar():
    try:
        ws  = _get_ws()
        raw = ws.acell("B1").value or "{}"
        dados = json.loads(raw)
        return dados.get("arvore",[]), dados.get("galeria",[])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return [], []

def _salvar(arvore, galeria=None):
    try:
        if galeria is None:
            _, galeria = _carregar()
        ws  = _get_ws()
        raw = json.dumps({"arvore": arvore, "galeria": galeria or []},
                         ensure_ascii=False)
        ws.update("B1", [[raw]])
        _carregar.clear()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

# ═══════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════
if "arvore"  not in st.session_state:
    arvore_raw, galeria_raw = _carregar()
    st.session_state.arvore   = arvore_raw
    st.session_state.galeria  = galeria_raw
if "ativo"   not in st.session_state: st.session_state.ativo = None
if "modo"    not in st.session_state: st.session_state.modo  = "ver"

arvore = st.session_state.arvore

NIVEL = {"Bisavô":0,"Bisavó":0,"Avô (paterno)":1,"Avó (paterna)":1,
         "Avô (materno)":1,"Avó (materna)":1,"Pai":2,"Mãe":2,
         "Eu":3,"Cônjuge":3,"Irmão":3,"Irmã":3,"Filho":4,"Filha":4,"Outro":3}
EMOJI = {"Pai":"👨","Mãe":"👩","Avô (paterno)":"👴","Avó (paterna)":"👵",
         "Avô (materno)":"👴","Avó (materna)":"👵","Bisavô":"🧓","Bisavó":"👵",
         "Eu":"🧑","Cônjuge":"💑","Irmão":"👦","Irmã":"👧",
         "Filho":"👦","Filha":"👧","Outro":"👤"}

def _nivel(p): return NIVEL.get(p.get("relacao","Outro"), 3)

# ═══════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════
st.markdown("""
<div class="arvore-header">
    <h1>🌳 Árvore Genealógica</h1>
    <p>Passe o mouse para ver o nome · Clique para ver as fotos</p>
</div>
""", unsafe_allow_html=True)

col_arv, col_pain = st.columns([2.3, 1], gap="large")

# ═══════════════════════════════════════════════════
# COLUNA ESQUERDA — ÁRVORE
# ═══════════════════════════════════════════════════
with col_arv:

    def _foto_html(pessoa):
        url = pessoa.get("foto_perfil","")
        emoji = EMOJI.get(pessoa.get("relacao","Outro"),"👤")
        nome  = pessoa.get("nome","")
        if url:
            inner = f'<img class="pessoa-foto" src="{url}">'
        else:
            inner = f'<div class="pessoa-placeholder">{emoji}</div>'
        return f'<div class="pessoa-wrap">{inner}<span class="pessoa-tooltip">{nome}</span></div>'

    # Agrupa em pares (casal) ou individual por nível
    def _agrupar_casais(pessoas):
        """
        Tenta parear Pai+Mãe, Avô+Avó, etc.
        Retorna lista de grupos: cada grupo é lista de 1 ou 2 pessoas.
        """
        pares_rel = [
            {"Pai","Mãe"}, {"Avô (paterno)","Avó (paterna)"},
            {"Avô (materno)","Avó (materna)"}, {"Bisavô","Bisavó"},
            {"Eu","Cônjuge"}
        ]
        usados = set()
        grupos = []
        for p in pessoas:
            if p["id"] in usados: continue
            rel = p.get("relacao","Outro")
            parceiro = None
            for par in pares_rel:
                if rel in par:
                    outro_rel = list(par - {rel})[0]
                    for q in pessoas:
                        if q["id"] not in usados and q.get("relacao") == outro_rel:
                            parceiro = q
                            break
                    break
            if parceiro:
                grupos.append([p, parceiro])
                usados.add(p["id"]); usados.add(parceiro["id"])
            else:
                grupos.append([p])
                usados.add(p["id"])
        return grupos

    if not arvore:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:rgba(255,255,255,.2);">
            <div style="font-size:3rem;opacity:.25;margin-bottom:14px">🌳</div>
            <p style="font-size:14px">Árvore vazia. Adicione a primeira pessoa →</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Organiza por nível
        niveis_dict = {}
        for p in arvore:
            n = _nivel(p)
            niveis_dict.setdefault(n,[]).append(p)

        for n in sorted(niveis_dict.keys()):
            if n > min(niveis_dict.keys()):
                st.markdown('<div class="conector-v"></div>', unsafe_allow_html=True)

            grupos = _agrupar_casais(niveis_dict[n])
            cols = st.columns(max(len(grupos),1))

            for col, grupo in zip(cols, grupos):
                with col:
                    ids_grupo  = [p["id"] for p in grupo]
                    ativo      = st.session_state.ativo in ids_grupo
                    qtd_fotos  = sum(len(p.get("fotos",[])) for p in grupo)
                    badge      = f'<span class="fotos-badge">{qtd_fotos}</span>' if qtd_fotos else ""
                    nomes_txt  = " & ".join(p["nome"].split()[0] for p in grupo)
                    rels_txt   = " · ".join(p.get("relacao","") for p in grupo)
                    fotos_html = "".join(_foto_html(p) for p in grupo)
                    cls_ativo  = "ativo" if ativo else ""

                    st.markdown(f"""
                    <div class="casal-card {cls_ativo}">
                        {badge}
                        <div class="casal-fotos">{fotos_html}</div>
                        <div class="casal-nomes">{nomes_txt}</div>
                        <div class="casal-rel">{rels_txt}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Botões individuais para cada pessoa
                    if len(grupo) == 2:
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button(grupo[0]["nome"].split()[0], key=f"s_{grupo[0]['id']}", use_container_width=True):
                                st.session_state.ativo = grupo[0]["id"]; st.session_state.modo="ver"; st.rerun()
                        with b2:
                            if st.button(grupo[1]["nome"].split()[0], key=f"s_{grupo[1]['id']}", use_container_width=True):
                                st.session_state.ativo = grupo[1]["id"]; st.session_state.modo="ver"; st.rerun()
                    else:
                        if st.button("Ver fotos", key=f"s_{grupo[0]['id']}", use_container_width=True):
                            st.session_state.ativo = grupo[0]["id"]; st.session_state.modo="ver"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕  Adicionar pessoa", use_container_width=True):
        st.session_state.modo="add"; st.session_state.ativo=None; st.rerun()

# ═══════════════════════════════════════════════════
# COLUNA DIREITA — PAINEL
# ═══════════════════════════════════════════════════
with col_pain:

    # ── MODO: Adicionar pessoa ──────────────────────
    if st.session_state.modo == "add":
        st.markdown('<div class="detalhe-panel">', unsafe_allow_html=True)
        st.markdown("**👤 Nova pessoa**")
        nome_n  = st.text_input("Nome completo", key="nome_novo")
        rel_n   = st.selectbox("Relação", list(NIVEL.keys()), key="rel_nova")
        nasc_n  = st.text_input("Nascimento", placeholder="Ex: 12/04/1945", key="nasc_nova")
        falec_n = st.text_input("Falecimento (opcional)", key="falec_nova")
        gen_n   = st.radio("Gênero", ["Masculino","Feminino"], horizontal=True, key="gen_nova")
        st.markdown("**Foto de perfil (opcional)**")
        fp_file = st.file_uploader("", type=["jpg","jpeg","png","webp"], key="fp_nova", label_visibility="collapsed")
        if fp_file: st.image(fp_file, use_container_width=True)

        c1,c2 = st.columns(2)
        with c1:
            if st.button("✅ Salvar", use_container_width=True, type="primary"):
                if not nome_n.strip(): st.warning("Digite o nome.")
                else:
                    url_p = ""
                    if fp_file and AKEY:
                        with st.spinner("Enviando foto..."):
                            fp_file.seek(0)
                            url_p = _upload(fp_file.read(), fp_file.name)
                    nova = {
                        "id": f"p{int(time.time()*1000)}",
                        "nome": nome_n.strip(), "relacao": rel_n,
                        "genero": "F" if gen_n=="Feminino" else "M",
                        "nascimento": nasc_n.strip(), "falecimento": falec_n.strip(),
                        "foto_perfil": url_p, "fotos": []
                    }
                    st.session_state.arvore.append(nova)
                    _salvar(st.session_state.arvore)
                    st.session_state.ativo = nova["id"]; st.session_state.modo="ver"
                    st.rerun()
        with c2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.modo="ver"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── MODO: Ver pessoa ────────────────────────────
    elif st.session_state.ativo:
        pessoa = next((p for p in arvore if p["id"]==st.session_state.ativo), None)
        if not pessoa:
            st.session_state.ativo=None; st.rerun()

        nome  = pessoa["nome"]
        rel   = pessoa.get("relacao","")
        nasc  = pessoa.get("nascimento","")
        falec = pessoa.get("falecimento","")
        fotos = pessoa.get("fotos",[])

        st.markdown(f"""
        <div class="detalhe-panel">
            <div class="detalhe-nome">{nome}</div>
            <div class="detalhe-rel">{rel}</div>
            <div style="font-size:.82rem;color:rgba(255,255,255,.45);line-height:1.9;">
                {"📅 " + nasc + "<br>" if nasc else ""}
                {"✝️ " + falec + "<br>" if falec else ""}
                {"📷 " + str(len(fotos)) + " foto" + ("s" if len(fotos)!=1 else "") if fotos else "Sem fotos ainda"}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Fotos
        if fotos:
            st.markdown(f"**📷 Fotos de {nome.split()[0]}**")
            for j, foto in enumerate(fotos):
                st.markdown(f"""
                <div class="foto-par">
                    <div class="foto-par-header">
                        <span class="foto-par-titulo">{foto.get('titulo','')}</span>
                        <span style="font-size:11px;color:rgba(255,255,255,.2)">{foto.get('data','')}</span>
                    </div>
                    <div class="foto-grid">
                        <div class="foto-lado antiga">
                            <img src="{foto['antiga']}">
                            <span class="foto-badge badge-antiga">Antiga</span>
                        </div>
                        <div class="foto-lado">
                            <img src="{foto['restaurada']}">
                            <span class="foto-badge badge-rest">✨ Rest.</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Remover foto", key=f"delf_{j}", use_container_width=True):
                    pessoa["fotos"].pop(j)
                    _salvar(st.session_state.arvore)
                    st.rerun()

        # Adicionar foto
        with st.expander(f"➕ Adicionar foto de {nome.split()[0]}"):
            tit = st.text_input("Nome da foto", placeholder="Ex: Casamento 1972", key="tit_foto")
            fa  = st.file_uploader("🕰️ Foto antiga",    type=["jpg","jpeg","png","webp"], key="fa")
            fr  = st.file_uploader("✨ Foto restaurada", type=["jpg","jpeg","png","webp"], key="fr")
            if fa: st.image(fa, use_container_width=True)
            if fr: st.image(fr, use_container_width=True)
            if st.button("💾 Salvar", use_container_width=True, type="primary", key="btn_sf"):
                if not fa or not fr: st.warning("Selecione as duas fotos.")
                elif not AKEY: st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
                else:
                    with st.spinner("Enviando..."):
                        fa.seek(0); fr.seek(0)
                        ua = _upload(fa.read(), fa.name)
                        ur = _upload(fr.read(), fr.name)
                        pessoa["fotos"].append({
                            "titulo": tit.strip() or "Sem título",
                            "antiga": ua, "restaurada": ur,
                            "data": datetime.now().strftime("%d/%m/%Y")
                        })
                        _salvar(st.session_state.arvore)
                        st.success("✅ Salvo!"); st.rerun()

        # Remover pessoa
        with st.expander("⚙️ Opções"):
            if st.button(f"🗑️ Remover {nome.split()[0]} da árvore", use_container_width=True):
                st.session_state.arvore = [p for p in st.session_state.arvore if p["id"]!=pessoa["id"]]
                _salvar(st.session_state.arvore)
                st.session_state.ativo=None; st.rerun()

    # ── Nenhum selecionado ──────────────────────────
    else:
        st.markdown("""
        <div class="detalhe-panel">
            <div class="empty-panel">
                <div style="font-size:2rem;opacity:.2;margin-bottom:10px">👆</div>
                <p>Clique no nome de uma pessoa<br>para ver as fotos dela</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
