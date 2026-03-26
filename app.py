# -*- coding: utf-8 -*-
# Arvore_Genealogica.py

import streamlit as st
import json, os, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Árvore Genealógica", page_icon="🌳", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
footer{display:none!important} #MainMenu{display:none!important} header{display:none!important}

.arvore-header {
    text-align:center; padding:36px 20px 20px;
}
.arvore-header h1 {
    font-family:'Cormorant Garamond',serif;
    font-size:2.8rem; font-weight:600;
    color:rgba(255,255,255,.92); margin:0 0 8px;
}
.arvore-header p { font-size:.88rem; color:rgba(255,255,255,.4); margin:0; }

/* ── Árvore SVG container ── */
.arvore-wrap {
    overflow-x:auto;
    padding:20px 0 40px;
}

/* ── Pessoa card ── */
.pessoa-node {
    background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.12);
    border-radius:16px;
    padding:14px 16px;
    text-align:center;
    cursor:pointer;
    transition:all .2s;
    min-width:120px;
    position:relative;
}
.pessoa-node:hover {
    background:rgba(255,255,255,.12);
    border-color:rgba(255,255,255,.3);
    transform:translateY(-2px);
}
.pessoa-node.ativo {
    background:rgba(110,232,170,.1);
    border-color:rgba(110,232,170,.4);
}
.pessoa-node.feminino { border-color:rgba(232,180,220,.3); }
.pessoa-node.feminino:hover { border-color:rgba(232,180,220,.6); background:rgba(232,180,220,.08); }
.pessoa-node.feminino.ativo { background:rgba(232,180,220,.1); border-color:rgba(232,180,220,.5); }

.pessoa-foto {
    width:70px; height:70px;
    border-radius:50%; object-fit:cover;
    margin:0 auto 8px; display:block;
    border:2px solid rgba(255,255,255,.15);
}
.pessoa-foto-placeholder {
    width:70px; height:70px; border-radius:50%;
    background:rgba(255,255,255,.08);
    border:2px dashed rgba(255,255,255,.2);
    margin:0 auto 8px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.6rem;
}
.pessoa-nome {
    font-family:'Cormorant Garamond',serif;
    font-size:.95rem; font-weight:600;
    color:rgba(255,255,255,.88); margin-bottom:2px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
    max-width:110px;
}
.pessoa-rel {
    font-size:.72rem; color:rgba(255,255,255,.35);
    text-transform:uppercase; letter-spacing:.5px;
}
.pessoa-fotos-badge {
    position:absolute; top:-6px; right:-6px;
    background:#6ee8aa; color:#0a2a1a;
    border-radius:10px; font-size:10px; font-weight:700;
    padding:2px 7px; line-height:1.4;
}

/* ── Linhas da árvore ── */
.arvore-container {
    display:flex; flex-direction:column; align-items:center; gap:0;
    padding:20px;
}
.nivel {
    display:flex; align-items:flex-start; justify-content:center;
    gap:16px; position:relative;
    padding:0 20px;
}
.conector-v {
    width:2px; height:32px;
    background:rgba(255,255,255,.15);
    margin:0 auto;
}
.conector-h {
    height:2px;
    background:rgba(255,255,255,.15);
    align-self:center;
}

/* ── Painel lateral de detalhes ── */
.detalhe-panel {
    background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.1);
    border-radius:20px; padding:24px;
    position:sticky; top:20px;
}
.detalhe-nome {
    font-family:'Cormorant Garamond',serif;
    font-size:1.8rem; font-weight:600; font-style:italic;
    color:rgba(255,255,255,.9); margin-bottom:4px;
}
.detalhe-rel {
    font-size:.8rem; color:rgba(255,255,255,.35);
    text-transform:uppercase; letter-spacing:.8px; margin-bottom:20px;
}
.detalhe-foto-grid {
    display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:16px;
}
.detalhe-foto-wrap { position:relative; border-radius:12px; overflow:hidden; }
.detalhe-foto-wrap img { width:100%; height:180px; object-fit:cover; display:block; }
.detalhe-foto-wrap.antiga img { filter:sepia(.2) brightness(.9); }
.detalhe-foto-label {
    position:absolute; bottom:8px; left:8px;
    font-size:10px; font-weight:500; letter-spacing:.8px;
    text-transform:uppercase; padding:3px 10px; border-radius:20px;
}
.label-antiga { background:rgba(200,170,100,.3); color:#e8c97a; }
.label-rest   { background:rgba(100,200,150,.25); color:#6ee8aa; }
.detalhe-info { font-size:.85rem; color:rgba(255,255,255,.5); line-height:1.8; }
.detalhe-vazio {
    text-align:center; padding:32px 0;
    color:rgba(255,255,255,.2); font-size:.9rem;
}

/* ── Formulário adicionar ── */
.form-box {
    background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.1);
    border-radius:16px; padding:20px;
    margin-top:16px;
}
.form-box h4 {
    font-family:'Cormorant Garamond',serif;
    font-size:1.1rem; color:rgba(255,255,255,.7);
    margin:0 0 14px;
}
[data-testid="stFileUploaderDropzone"] {
    background:rgba(255,255,255,.03)!important;
    border:1px dashed rgba(255,255,255,.15)!important;
    border-radius:10px!important;
}
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select {
    background:rgba(255,255,255,.05)!important;
    border:1px solid rgba(255,255,255,.12)!important;
    border-radius:8px!important;
    color:rgba(255,255,255,.85)!important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# DADOS
# ══════════════════════════════════════════════════════════
ARVORE_PATH = Path("arvore.json")
RELACOES = ["Avô (paterno)","Avó (paterna)","Avô (materno)","Avó (materna)",
            "Pai","Mãe","Eu","Irmão","Irmã","Filho","Filha","Tio","Tia","Primo","Prima","Outro"]

EMOJI_REL = {
    "Avô (paterno)":"👴","Avó (paterna)":"👵","Avô (materno)":"👴","Avó (materna)":"👵",
    "Pai":"👨","Mãe":"👩","Eu":"🧑","Irmão":"👦","Irmã":"👧",
    "Filho":"👦","Filha":"👧","Tio":"👨","Tia":"👩","Primo":"👦","Prima":"👧","Outro":"👤",
}

NIVEL_REL = {
    "Avô (paterno)":0,"Avó (paterna)":0,"Avô (materno)":0,"Avó (materna)":0,
    "Pai":1,"Mãe":1,
    "Eu":2,"Irmão":2,"Irmã":2,
    "Filho":3,"Filha":3,
}

def _carregar():
    if ARVORE_PATH.exists():
        try: return json.loads(ARVORE_PATH.read_text(encoding="utf-8"))
        except: pass
    return []

def _salvar(dados):
    ARVORE_PATH.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

def _get_secret(key, default=""):
    try:
        v = st.secrets.get(key, default)
        return str(v).strip() if v else default
    except:
        return os.environ.get(key, default)

CLOUD_NAME = _get_secret("CLOUDINARY_CLOUD_NAME","db8ipmete")
API_KEY    = _get_secret("CLOUDINARY_API_KEY")
API_SECRET = _get_secret("CLOUDINARY_API_SECRET")

def _upload_cloudinary(file_bytes, filename, folder="Fotos antigas"):
    ts        = str(int(time.time()))
    public_id = f"Fotos antigas/{Path(filename).stem}_{ts}"
    params    = f"folder={folder}&public_id={public_id}&timestamp={ts}"
    signature = hashlib.sha1(f"{params}{API_SECRET}".encode()).hexdigest()
    boundary  = "----Boundary" + ts
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: image/jpeg\r\n\r\n"
    ).encode() + file_bytes + (
        f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"api_key\"\r\n\r\n{API_KEY}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"timestamp\"\r\n\r\n{ts}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\n{folder}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"public_id\"\r\n\r\n{public_id}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"signature\"\r\n\r\n{signature}\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"
    req = urllib.request.Request(url, data=body,
          headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["secure_url"]

# ══════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════
if "arvore"       not in st.session_state: st.session_state.arvore = _carregar()
if "pessoa_ativa" not in st.session_state: st.session_state.pessoa_ativa = None
if "modo"         not in st.session_state: st.session_state.modo = "ver"  # ver | add_pessoa | add_foto

arvore = st.session_state.arvore

# ══════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="arvore-header">
    <h1>🌳 Árvore Genealógica</h1>
    <p>Clique em uma pessoa para ver as fotos dela</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL: árvore | painel
# ══════════════════════════════════════════════════════════
col_arvore, col_painel = st.columns([2.2, 1], gap="large")

# ── COLUNA ESQUERDA: Árvore ───────────────────────────────
with col_arvore:

    # Agrupa por nível
    niveis = {}
    for p in arvore:
        n = NIVEL_REL.get(p.get("relacao","Outro"), 2)
        niveis.setdefault(n, []).append(p)
    # Pessoas sem nível mapeado ficam no 2
    for p in arvore:
        if p.get("relacao","Outro") not in NIVEL_REL:
            niveis.setdefault(2, []).append(p)

    def _render_pessoa(p):
        pid      = p["id"]
        nome     = p["nome"]
        rel      = p.get("relacao","Outro")
        emoji    = EMOJI_REL.get(rel,"👤")
        qtd_fotos= len(p.get("fotos",[]))
        ativo    = st.session_state.pessoa_ativa == pid
        genero   = p.get("genero","M")
        cls_gen  = "feminino" if genero == "F" else ""
        cls_ativo= "ativo" if ativo else ""
        badge    = f'<span class="pessoa-fotos-badge">{qtd_fotos}</span>' if qtd_fotos else ""
        foto_url = p.get("foto_perfil","")
        if foto_url:
            foto_html = f'<img class="pessoa-foto" src="{foto_url}">'
        else:
            foto_html = f'<div class="pessoa-foto-placeholder">{emoji}</div>'

        st.markdown(f"""
        <div class="pessoa-node {cls_gen} {cls_ativo}" id="node-{pid}">
            {badge}
            {foto_html}
            <div class="pessoa-nome" title="{nome}">{nome}</div>
            <div class="pessoa-rel">{rel}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Selecionar", key=f"sel_{pid}", use_container_width=True,
                     help=f"Ver fotos de {nome}"):
            st.session_state.pessoa_ativa = pid
            st.session_state.modo = "ver"
            st.rerun()

    if not arvore:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:rgba(255,255,255,.25);">
            <div style="font-size:3rem;margin-bottom:16px;opacity:.3">🌳</div>
            <p style="font-size:14px">Sua árvore está vazia.<br>Adicione a primeira pessoa no painel ao lado.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Renderiza níveis de cima para baixo
        for nivel_num in sorted(niveis.keys()):
            pessoas_nivel = niveis[nivel_num]
            if nivel_num > min(niveis.keys()):
                st.markdown('<div class="conector-v" style="margin:0 auto;width:2px;height:28px;background:rgba(255,255,255,.12)"></div>', unsafe_allow_html=True)

            cols = st.columns(max(len(pessoas_nivel), 1))
            for col, p in zip(cols, pessoas_nivel):
                with col:
                    _render_pessoa(p)

    st.markdown("<br>", unsafe_allow_html=True)

    # Botão adicionar pessoa
    if st.button("➕  Adicionar pessoa", use_container_width=True):
        st.session_state.modo = "add_pessoa"
        st.session_state.pessoa_ativa = None
        st.rerun()

# ── COLUNA DIREITA: Painel de detalhes ───────────────────
with col_painel:

    # ── MODO: Adicionar pessoa ────────────────────────────
    if st.session_state.modo == "add_pessoa":
        st.markdown('<div class="form-box"><h4>👤 Nova pessoa</h4>', unsafe_allow_html=True)
        nome_novo  = st.text_input("Nome completo", placeholder="Ex: José da Silva")
        rel_nova   = st.selectbox("Relação com você", RELACOES)
        nascimento = st.text_input("Nascimento (opcional)", placeholder="Ex: 12/04/1945")
        falecimento= st.text_input("Falecimento (opcional)", placeholder="Deixe em branco se vivo")
        genero     = st.radio("Gênero", ["Masculino","Feminino"], horizontal=True)

        st.markdown("**Foto de perfil (opcional)**")
        foto_perfil_file = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                                            key="up_perfil", label_visibility="collapsed")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Salvar", use_container_width=True, type="primary"):
                if not nome_novo.strip():
                    st.warning("Digite o nome.")
                else:
                    pid = f"p{int(time.time()*1000)}"
                    url_perfil = ""
                    if foto_perfil_file and API_KEY:
                        with st.spinner("Enviando foto..."):
                            foto_perfil_file.seek(0)
                            url_perfil = _upload_cloudinary(foto_perfil_file.read(), foto_perfil_file.name)
                    nova = {
                        "id": pid, "nome": nome_novo.strip(),
                        "relacao": rel_nova, "genero": "F" if genero=="Feminino" else "M",
                        "nascimento": nascimento.strip(), "falecimento": falecimento.strip(),
                        "foto_perfil": url_perfil, "fotos": [],
                    }
                    st.session_state.arvore.append(nova)
                    _salvar(st.session_state.arvore)
                    st.session_state.pessoa_ativa = pid
                    st.session_state.modo = "ver"
                    st.success(f"✅ {nome_novo} adicionado!")
                    st.rerun()
        with c2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.modo = "ver"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── MODO: Ver pessoa ──────────────────────────────────
    elif st.session_state.pessoa_ativa:
        pessoa = next((p for p in arvore if p["id"]==st.session_state.pessoa_ativa), None)

        if not pessoa:
            st.session_state.pessoa_ativa = None
            st.rerun()

        nome = pessoa["nome"]
        rel  = pessoa.get("relacao","")
        nasc = pessoa.get("nascimento","")
        falec= pessoa.get("falecimento","")
        fotos= pessoa.get("fotos",[])

        # Header da pessoa
        st.markdown(f"""
        <div class="detalhe-panel">
            <div class="detalhe-nome">{nome}</div>
            <div class="detalhe-rel">{rel}</div>
            <div class="detalhe-info">
                {"📅 Nascimento: " + nasc + "<br>" if nasc else ""}
                {"✝️ Falecimento: " + falec + "<br>" if falec else ""}
                {"📷 " + str(len(fotos)) + " foto" + ("s" if len(fotos)!=1 else "") if fotos else "Sem fotos ainda"}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Fotos da pessoa
        if fotos:
            st.markdown(f"**📷 Fotos de {nome.split()[0]}**")
            for j, foto in enumerate(fotos):
                titulo_foto = foto.get("titulo","Sem título")
                data_foto   = foto.get("data","")
                url_antiga  = foto.get("antiga","")
                url_rest    = foto.get("restaurada","")

                st.markdown(f"""
                <div class="foto-par" style="border-radius:14px;overflow:hidden;margin-bottom:12px;border:1px solid rgba(255,255,255,.08);">
                    <div style="padding:10px 16px;border-bottom:1px solid rgba(255,255,255,.07);
                        display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-family:'Cormorant Garamond',serif;font-style:italic;
                            font-size:1rem;color:rgba(255,255,255,.8)">{titulo_foto}</span>
                        <span style="font-size:11px;color:rgba(255,255,255,.25)">{data_foto}</span>
                    </div>
                    <div class="foto-grid">
                        <div class="foto-lado antiga">
                            <img src="{url_antiga}" style="width:100%;height:180px;object-fit:cover;display:block">
                            <span class="foto-badge badge-antiga">Antiga</span>
                        </div>
                        <div class="foto-lado">
                            <img src="{url_rest}" style="width:100%;height:180px;object-fit:cover;display:block">
                            <span class="foto-badge badge-rest">✨ Rest.</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🗑️ Remover foto", key=f"delfoto_{j}", use_container_width=True):
                    pessoa["fotos"].pop(j)
                    _salvar(st.session_state.arvore)
                    st.rerun()
        else:
            st.markdown("""
            <div class="detalhe-vazio">
                <div style="font-size:2rem;opacity:.3;margin-bottom:10px">📷</div>
                <p>Nenhuma foto ainda.<br>Adicione abaixo!</p>
            </div>
            """, unsafe_allow_html=True)

        # Formulário: adicionar foto a esta pessoa
        with st.expander(f"➕ Adicionar foto de {nome.split()[0]}"):
            titulo_f = st.text_input("Nome da foto", placeholder="Ex: Casamento 1972", key="titulo_foto")
            f_antiga = st.file_uploader("🕰️ Foto antiga", type=["jpg","jpeg","png","webp"], key="f_antiga")
            f_rest   = st.file_uploader("✨ Foto restaurada", type=["jpg","jpeg","png","webp"], key="f_rest")
            if f_antiga: st.image(f_antiga, use_container_width=True)
            if f_rest:   st.image(f_rest,   use_container_width=True)

            if st.button("💾 Salvar foto", use_container_width=True, type="primary", key="btn_salvar_foto"):
                if not f_antiga or not f_rest:
                    st.warning("Selecione as duas fotos.")
                elif not API_KEY:
                    st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
                else:
                    with st.spinner("Enviando fotos..."):
                        f_antiga.seek(0); f_rest.seek(0)
                        url_a = _upload_cloudinary(f_antiga.read(), f_antiga.name)
                        url_r = _upload_cloudinary(f_rest.read(),   f_rest.name)
                        pessoa["fotos"].append({
                            "titulo":     titulo_f.strip() or "Sem título",
                            "antiga":     url_a,
                            "restaurada": url_r,
                            "data":       datetime.now().strftime("%d/%m/%Y"),
                        })
                        _salvar(st.session_state.arvore)
                        st.success("✅ Foto salva!")
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Ações da pessoa
        with st.expander("⚙️ Editar ou remover pessoa"):
            if st.button(f"🗑️ Remover {nome.split()[0]} da árvore", use_container_width=True):
                st.session_state.arvore = [p for p in st.session_state.arvore if p["id"]!=pessoa["id"]]
                _salvar(st.session_state.arvore)
                st.session_state.pessoa_ativa = None
                st.rerun()

    # ── MODO: Nenhum selecionado ──────────────────────────
    else:
        st.markdown("""
        <div class="detalhe-panel">
            <div style="text-align:center;padding:32px 0;color:rgba(255,255,255,.2);">
                <div style="font-size:2.5rem;opacity:.3;margin-bottom:12px">👆</div>
                <p style="font-size:.9rem;margin:0">
                    Clique em uma pessoa<br>na árvore para ver as fotos dela
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
