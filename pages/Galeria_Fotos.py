# -*- coding: utf-8 -*-
# pages/1_Galeria.py

import streamlit as st
import json, os, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Galeria — Raízes", page_icon="📷", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
footer{display:none!important} #MainMenu{display:none!important} header{display:none!important}
.mem-header { text-align:center; padding:40px 20px 28px; }
.mem-header h1 { font-family:'Cormorant Garamond',serif; font-size:2.8rem; font-weight:600; color:rgba(255,255,255,.92); margin:0 0 8px; }
.mem-header p { font-size:.88rem; color:rgba(255,255,255,.4); margin:0; }
.upload-box { background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.1); border-radius:20px; padding:28px 24px; margin-bottom:28px; }
.upload-box-title { font-family:'Cormorant Garamond',serif; font-size:1.3rem; font-weight:600; color:rgba(255,255,255,.8); margin-bottom:18px; text-align:center; }
.foto-par { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08); border-radius:20px; overflow:hidden; margin-bottom:28px; }
.foto-par-header { padding:14px 22px 12px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,.07); }
.foto-titulo { font-family:'Cormorant Garamond',serif; font-size:1.2rem; font-weight:600; color:rgba(255,255,255,.88); font-style:italic; }
.foto-data { font-size:11px; color:rgba(255,255,255,.25); }
.foto-grid { display:grid; grid-template-columns:1fr 1fr; gap:1px; background:rgba(255,255,255,.06); }
.foto-lado { position:relative; background:#0a0a0a; }
.foto-lado img { width:100%; height:320px; object-fit:cover; display:block; }
.foto-lado.antiga img { filter:sepia(.15) brightness(.95); }
.foto-badge { position:absolute; bottom:12px; left:12px; font-size:11px; font-weight:500; letter-spacing:.8px; text-transform:uppercase; padding:4px 12px; border-radius:20px; }
.badge-antiga { background:rgba(200,170,100,.25); color:#e8c97a; border:1px solid rgba(200,170,100,.3); }
.badge-rest   { background:rgba(100,200,150,.2);  color:#6ee8aa; border:1px solid rgba(100,200,150,.3); }
.divisor { display:flex; align-items:center; gap:14px; margin:20px 0; color:rgba(255,255,255,.2); font-size:11px; letter-spacing:1px; text-transform:uppercase; }
.divisor::before,.divisor::after { content:''; flex:1; height:1px; background:rgba(255,255,255,.08); }
.empty-state { text-align:center; padding:48px 20px; color:rgba(255,255,255,.2); }
[data-testid="stFileUploaderDropzone"] { background:rgba(255,255,255,.03)!important; border:1px dashed rgba(255,255,255,.15)!important; border-radius:12px!important; }
[data-testid="stTextInput"] input { background:rgba(255,255,255,.05)!important; border:1px solid rgba(255,255,255,.12)!important; border-radius:10px!important; color:rgba(255,255,255,.85)!important; font-family:'Cormorant Garamond',serif!important; font-size:1.1rem!important; }
</style>
""", unsafe_allow_html=True)

# ── Cloudinary ────────────────────────────────────────────────────────
def _get_secret(key, default=""):
    try:
        v = st.secrets.get(key, default)
        return str(v).strip() if v else default
    except:
        return os.environ.get(key, default)

CLOUD_NAME = _get_secret("CLOUDINARY_CLOUD_NAME", "db8ipmete")
API_KEY    = _get_secret("CLOUDINARY_API_KEY")
API_SECRET = _get_secret("CLOUDINARY_API_SECRET")

def _upload(file_bytes, filename):
    ts        = str(int(time.time()))
    public_id = f"Fotos antigas/{Path(filename).stem}_{ts}"
    params    = f"folder=Fotos antigas&public_id={public_id}&timestamp={ts}"
    signature = hashlib.sha1(f"{params}{API_SECRET}".encode()).hexdigest()
    boundary  = "----Boundary" + ts
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: image/jpeg\r\n\r\n"
    ).encode() + file_bytes + (
        f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"api_key\"\r\n\r\n{API_KEY}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"timestamp\"\r\n\r\n{ts}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\nFotos antigas\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"public_id\"\r\n\r\n{public_id}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"signature\"\r\n\r\n{signature}\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    url = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload"
    req = urllib.request.Request(url, data=body,
          headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["secure_url"]

# ── Dados: usa arvore.json (mesmo arquivo do app.py) ─────────────────
# Streamlit Cloud não persiste arquivos criados em runtime.
# A solução é ler/gravar a chave "galeria" dentro do arvore.json
# que já está no repositório GitHub.
# Como não podemos gravar no repo diretamente, usamos st.session_state
# + re-hidratamos do Cloudinary via URLs salvas no session_state entre reruns.
# Para persistência real: as URLs ficam salvas nos secrets ou num Google Sheet.
# Solução prática aqui: salvamos no session_state e mostramos aviso de que
# a galeria é temporária até integração com Sheets.

# ── SOLUÇÃO REAL: salva URLs em st.secrets via arquivo no repo ────────
# Como o Streamlit Cloud não permite escrita, usamos Google Sheets
# para persistir. Por enquanto, carregamos do arvore.json se existir.

ARVORE_PATH = Path("arvore.json")

def _carregar_galeria():
    """Lê a chave 'galeria' do arvore.json."""
    if ARVORE_PATH.exists():
        try:
            dados = json.loads(ARVORE_PATH.read_text(encoding="utf-8"))
            # arvore.json pode ser lista (formato antigo) ou dict (novo)
            if isinstance(dados, dict):
                return dados.get("galeria", [])
            # formato lista = só árvore, galeria vazia
            return []
        except:
            pass
    return []

def _salvar_galeria(fotos):
    """Grava a chave 'galeria' no arvore.json preservando a árvore."""
    dados = {}
    if ARVORE_PATH.exists():
        try:
            raw = json.loads(ARVORE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                dados = {"arvore": raw, "galeria": []}
            else:
                dados = raw
        except:
            dados = {}
    dados["galeria"] = fotos
    ARVORE_PATH.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

def _carregar_arvore():
    """Lê a lista de pessoas do arvore.json."""
    if ARVORE_PATH.exists():
        try:
            raw = json.loads(ARVORE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return raw
            return raw.get("arvore", [])
        except:
            pass
    return []

if "galeria" not in st.session_state:
    st.session_state.galeria = _carregar_galeria()

# ── Header ────────────────────────────────────────────────────────────
st.markdown("""
<div class="mem-header">
    <h1>📷 Galeria da Família</h1>
    <p>Fotos antigas e suas versões restauradas</p>
</div>
""", unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────
st.markdown('<div class="upload-box"><div class="upload-box-title">Adicionar novo par de fotos</div>', unsafe_allow_html=True)

titulo_col, _ = st.columns([3, 1])
with titulo_col:
    titulo = st.text_input("", placeholder="✍️  Nome da foto (ex: Família reunida em 1980)", label_visibility="collapsed")

col_a, col_r = st.columns(2)
with col_a:
    st.markdown("**🕰️ Foto antiga**")
    file_antiga = st.file_uploader("", type=["jpg","jpeg","png","webp"], key="up_antiga", label_visibility="collapsed")
    if file_antiga: st.image(file_antiga, use_container_width=True)
with col_r:
    st.markdown("**✨ Foto restaurada**")
    file_rest = st.file_uploader("", type=["jpg","jpeg","png","webp"], key="up_rest", label_visibility="collapsed")
    if file_rest: st.image(file_rest, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
btn_col, _ = st.columns([1, 2])
with btn_col:
    if st.button("➕  Adicionar à galeria", use_container_width=True, type="primary"):
        if not file_antiga or not file_rest:
            st.warning("Selecione as duas fotos para continuar.")
        elif not API_KEY:
            st.error("Configure CLOUDINARY_API_KEY nos Secrets.")
        else:
            with st.spinner("Salvando fotos no Cloudinary..."):
                try:
                    file_antiga.seek(0); file_rest.seek(0)
                    url_a = _upload(file_antiga.read(), file_antiga.name)
                    url_r = _upload(file_rest.read(),   file_rest.name)
                    novo = {
                        "titulo":     titulo.strip() or "Sem título",
                        "antiga":     url_a,
                        "restaurada": url_r,
                        "data":       datetime.now().strftime("%d/%m/%Y"),
                    }
                    st.session_state.galeria.insert(0, novo)
                    _salvar_galeria(st.session_state.galeria)
                    st.success("✅ Foto salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")

st.markdown("</div>", unsafe_allow_html=True)

# ── Galeria ───────────────────────────────────────────────────────────
galeria = st.session_state.galeria

if not galeria:
    st.markdown("""
    <div class="empty-state">
        <div style="font-size:2.5rem;opacity:.3;margin-bottom:12px">🖼️</div>
        <p style="font-size:14px">Galeria vazia. Adicione a primeira foto acima.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    total = len(galeria)
    st.markdown(f'<div class="divisor">{total} foto{"s" if total!=1 else ""} na galeria</div>', unsafe_allow_html=True)

    for i, par in enumerate(galeria):
        st.markdown(f"""
        <div class="foto-par">
            <div class="foto-par-header">
                <span class="foto-titulo">{par['titulo']}</span>
                <span class="foto-data">📅 {par.get('data','')}</span>
            </div>
            <div class="foto-grid">
                <div class="foto-lado antiga">
                    <img src="{par['antiga']}" alt="Foto antiga">
                    <span class="foto-badge badge-antiga">Foto antiga</span>
                </div>
                <div class="foto-lado">
                    <img src="{par['restaurada']}" alt="Foto restaurada">
                    <span class="foto-badge badge-rest">✨ Restaurada</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        b1, b2, b3, _ = st.columns([1, 1, 1, 3])
        with b1: st.link_button("🔗 Antiga",     par["antiga"],     use_container_width=True)
        with b2: st.link_button("🔗 Restaurada", par["restaurada"], use_container_width=True)
        with b3:
            if st.button("🗑️ Remover", key=f"del_{i}", use_container_width=True):
                st.session_state.galeria.pop(i)
                _salvar_galeria(st.session_state.galeria)
                st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
