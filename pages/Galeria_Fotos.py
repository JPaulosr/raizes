# -*- coding: utf-8 -*-
# pages/1_Galeria_Fotos.py — Galeria com lightbox, filtros e marcação de rostos

import streamlit as st
import streamlit.components.v1 as components
import json, os, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Galeria — Raízes", page_icon="📷", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
footer{display:none!important}#MainMenu{display:none!important}header{display:none!important}
.gal-header{text-align:center;padding:36px 20px 24px;}
.gal-header h1{font-family:'Cormorant Garamond',serif;font-size:2.6rem;font-weight:600;color:rgba(255,255,255,.92);margin:0 0 8px;}
.gal-header p{font-size:.85rem;color:rgba(255,255,255,.35);margin:0;}
/* Cards da galeria */
.foto-card{position:relative;cursor:pointer;border-radius:14px;overflow:hidden;background:#111;border:1px solid rgba(255,255,255,.08);transition:transform .2s,border-color .2s;}
.foto-card:hover{transform:scale(1.02);border-color:rgba(255,255,255,.22);}
.foto-card img{width:100%;height:220px;object-fit:cover;display:block;filter:sepia(.12) brightness(.9);}
.foto-card-info{padding:10px 14px 12px;}
.foto-card-titulo{font-family:'Cormorant Garamond',serif;font-size:.95rem;font-style:italic;color:rgba(255,255,255,.82);}
.foto-card-pessoas{font-size:.72rem;color:rgba(255,255,255,.35);margin-top:3px;}
.foto-card-pessoas span{background:rgba(255,255,255,.07);border-radius:8px;padding:1px 6px;margin-right:3px;}
/* Lightbox */
.lb-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.96);z-index:9999;align-items:center;justify-content:center;flex-direction:column;}
.lb-overlay.open{display:flex;}
.lb-close{position:absolute;top:18px;right:24px;font-size:1.8rem;color:rgba(255,255,255,.6);cursor:pointer;z-index:10001;background:none;border:none;line-height:1;}
.lb-close:hover{color:#fff;}
.lb-body{display:flex;gap:2px;width:95vw;max-height:80vh;}
.lb-side{flex:1;position:relative;overflow:hidden;background:#0a0a0a;}
.lb-side img{width:100%;height:100%;object-fit:contain;display:block;}
.lb-badge{position:absolute;bottom:12px;left:12px;font-size:10px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;padding:3px 10px;border-radius:20px;}
.lb-badge-a{background:rgba(200,170,100,.3);color:#e8c97a;}
.lb-badge-r{background:rgba(100,200,150,.25);color:#6ee8aa;}
.lb-info{text-align:center;padding:14px 0 4px;color:rgba(255,255,255,.7);font-family:'Cormorant Garamond',serif;font-size:1.1rem;}
.lb-pessoas{font-size:.8rem;color:rgba(255,255,255,.35);margin-top:4px;}
.lb-pessoas span{background:rgba(255,255,255,.08);border-radius:8px;padding:2px 9px;margin:0 3px;}
/* Face tags na foto */
.face-container{position:relative;display:inline-block;width:100%;}
.face-tag{position:absolute;border:2px solid rgba(110,232,170,.7);border-radius:6px;cursor:default;transition:border-color .15s;}
.face-tag:hover{border-color:#6ee8aa;}
.face-tag .face-label{position:absolute;bottom:calc(100% + 4px);left:50%;transform:translateX(-50%);background:rgba(10,20,15,.92);border:1px solid rgba(110,232,170,.4);border-radius:6px;padding:3px 10px;font-size:11px;font-weight:500;color:#6ee8aa;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .15s;}
.face-tag:hover .face-label{opacity:1;}
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.03)!important;border:1px dashed rgba(255,255,255,.14)!important;border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# Secrets
# ─────────────────────────────────────────────────────────────────────
def _s(k, d=""):
    try:
        return str(st.secrets[k]).strip() or d
    except: pass
    try:
        return str(st.secrets.get(k, d)).strip() or d
    except: pass
    # seção [CLOUDINARY]
    _MAP = {
        "CLOUDINARY_API_KEY":    ("CLOUDINARY","api_key"),
        "CLOUDINARY_API_SECRET": ("CLOUDINARY","api_secret"),
        "CLOUDINARY_CLOUD_NAME": ("CLOUDINARY","cloud_name"),
    }
    if k in _MAP:
        sec, sub = _MAP[k]
        try: return str(st.secrets[sec][sub]).strip() or d
        except: pass
    return os.environ.get(k, d)

# ─────────────────────────────────────────────────────────────────────
# Google Sheets — mesma lógica do app.py
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

def _extrair_key(url_ou_key):
    import re
    if not url_ou_key: raise ValueError("PLANILHA_URL_RAIZES não configurada.")
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url_ou_key)
    if m: return m.group(1)
    if "/" not in url_ou_key: return url_ou_key
    raise ValueError(f"Não consegui extrair ID de: {url_ou_key!r}")

def _get_planilha():
    url = _s("PLANILHA_URL_RAIZES") or _s("PLANILHA_URL")
    return _gc().open_by_key(_extrair_key(url))

_COLS_P = ["id","nome","relacao","genero","nascimento","falecimento",
           "foto_perfil","conjuge_id","conjuge_nome","pai_id","pai_nome",
           "mae_id","mae_nome","foto_ids"]
_COLS_F = ["id","titulo","data","antiga","restaurada","pessoas_ids","pessoas_nomes"]

@st.cache_data(ttl=30, show_spinner=False)
def _carregar():
    try:
        sh = _get_planilha()
        # Pessoas
        try:
            ws_p  = sh.worksheet("Pessoas")
            rows_p = ws_p.get_all_records(expected_headers=_COLS_P)
        except: rows_p = []
        arvore = []
        for r in rows_p:
            if not r.get("id") or not r.get("nome"): continue
            arvore.append({
                "id":    str(r["id"]),
                "nome":  str(r["nome"]),
                "relacao": str(r.get("relacao","")),
                "foto_perfil": str(r.get("foto_perfil","")),
            })
        # Fotos
        try:
            ws_f  = sh.worksheet("Fotos")
            rows_f = ws_f.get_all_records(expected_headers=_COLS_F)
        except: rows_f = []
        acervo = []
        for r in rows_f:
            if not r.get("id") or not r.get("antiga"): continue
            ids_str = str(r.get("pessoas_ids",""))
            acervo.append({
                "id":         str(r["id"]),
                "titulo":     str(r.get("titulo","")),
                "data":       str(r.get("data","")),
                "antiga":     str(r["antiga"]),
                "restaurada": str(r.get("restaurada","")),
                "pessoas":    [x.strip() for x in ids_str.split(",") if x.strip()],
                "faces":      json.loads(str(r.get("faces","[]")) or "[]"),
            })
        return arvore, acervo
    except Exception as e:
        st.error("Erro ao carregar: "+str(e))
        return [], []

def _salvar_faces(foto_id, faces):
    """Salva as marcações de rostos na aba Fotos."""
    try:
        sh   = _get_planilha()
        ws_f = sh.worksheet("Fotos")
        rows = ws_f.get_all_values()
        # Encontrar coluna "faces" — adiciona se não existir
        header = rows[0] if rows else []
        if "faces" not in header:
            col_idx = len(header) + 1
            ws_f.update_cell(1, col_idx, "faces")
        else:
            col_idx = header.index("faces") + 1
        # Encontrar linha do foto_id
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == foto_id:
                ws_f.update_cell(i, col_idx, json.dumps(faces, ensure_ascii=False))
                _carregar.clear()
                return True
        return False
    except Exception as e:
        st.error("Erro ao salvar rostos: "+str(e))
        return False

# ─────────────────────────────────────────────────────────────────────
# Upload Cloudinary
# ─────────────────────────────────────────────────────────────────────
def _upload(fb, fname, folder="Raizes"):
    cloud = _s("CLOUDINARY_CLOUD_NAME","db8ipmete")
    akey  = _s("CLOUDINARY_API_KEY")
    asec  = _s("CLOUDINARY_API_SECRET")
    if not akey: raise ValueError("CLOUDINARY_API_KEY não configurada.")
    ts  = str(int(time.time()))
    pid = folder+"/"+Path(fname).stem+"_"+ts
    sig = hashlib.sha1(("folder="+folder+"&public_id="+pid+"&timestamp="+ts+asec).encode()).hexdigest()
    b   = "----B"+ts
    body = ("--"+b+"\r\nContent-Disposition: form-data; name=\"file\"; filename=\""+fname+"\"\r\nContent-Type: image/jpeg\r\n\r\n").encode()
    body += fb
    body += ("\r\n--"+b+"\r\nContent-Disposition: form-data; name=\"api_key\"\r\n\r\n"+akey+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"timestamp\"\r\n\r\n"+ts+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\n"+folder+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"public_id\"\r\n\r\n"+pid+"\r\n"
             "--"+b+"\r\nContent-Disposition: form-data; name=\"signature\"\r\n\r\n"+sig+"\r\n"
             "--"+b+"--\r\n").encode()
    req = urllib.request.Request(
        "https://api.cloudinary.com/v1_1/"+cloud+"/image/upload",
        data=body, headers={"Content-Type":"multipart/form-data; boundary="+b}
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())["secure_url"]

def _salvar_foto_sheets(nova_foto, arvore):
    """Adiciona nova foto na aba Fotos do Google Sheets."""
    try:
        sh   = _get_planilha()
        ws_f = sh.worksheet("Fotos")
        ids_str   = ",".join(nova_foto.get("pessoas",[]))
        nomes_str = ",".join(
            next((p["nome"] for p in arvore if p["id"]==pid), "")
            for pid in nova_foto.get("pessoas",[])
        )
        ws_f.append_row([
            nova_foto["id"],
            nova_foto["titulo"],
            nova_foto["data"],
            nova_foto["antiga"],
            nova_foto["restaurada"],
            ids_str,
            nomes_str,
            "[]"  # faces vazias
        ])
        _carregar.clear()
        return True
    except Exception as e:
        st.error("Erro ao salvar foto: "+str(e))
        return False

# ─────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────
if "gal_carregado" not in st.session_state:
    arv, acv = _carregar()
    st.session_state.gal_arvore  = arv
    st.session_state.gal_acervo  = acv
    st.session_state.gal_carregado = True

if "lb_foto_id" not in st.session_state: st.session_state.lb_foto_id = None
if "face_modo"  not in st.session_state: st.session_state.face_modo  = None

def arvore(): return st.session_state.gal_arvore
def acervo(): return st.session_state.gal_acervo

def _nome_curto(pid):
    p = next((x for x in arvore() if x["id"]==pid), None)
    return p["nome"].split()[0] if p else "?"

# ─────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="gal-header"><h1>📷 Galeria da Família</h1>'
    '<p>Fotos antigas e suas versões restauradas</p></div>',
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────────────────────────────
# Lightbox (HTML puro embutido)
# ─────────────────────────────────────────────────────────────────────
lb_foto = None
if st.session_state.lb_foto_id:
    lb_foto = next((f for f in acervo() if f["id"]==st.session_state.lb_foto_id), None)

if lb_foto:
    nomes_lb = [_nome_curto(pid) for pid in lb_foto.get("pessoas",[]) if next((p for p in arvore() if p["id"]==pid), None)]
    tags_lb  = "".join(f"<span>{n}</span>" for n in nomes_lb)

    # Gera face tags HTML
    faces_html = ""
    for fc in lb_foto.get("faces",[]):
        lado = fc.get("lado","antiga")  # "antiga" ou "restaurada"
        x, y, w, h = fc.get("x",0), fc.get("y",0), fc.get("w",10), fc.get("h",10)
        nome = fc.get("nome","")
        faces_html += (
            f'<div class="face-tag" data-lado="{lado}" '
            f'style="left:{x}%;top:{y}%;width:{w}%;height:{h}%;">'
            f'<span class="face-label">{nome}</span></div>'
        )

    components.html(f"""
    <style>
    body{{margin:0;background:rgba(0,0,0,.97);display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:'DM Sans',sans-serif;}}
    .lb-body{{display:flex;gap:2px;width:98vw;max-height:78vh;}}
    .lb-side{{flex:1;position:relative;background:#050505;overflow:hidden;}}
    .lb-side img{{width:100%;height:100%;object-fit:contain;display:block;}}
    .lb-badge{{position:absolute;bottom:10px;left:10px;font-size:10px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;padding:3px 10px;border-radius:20px;}}
    .badge-a{{background:rgba(200,170,100,.3);color:#e8c97a;}}
    .badge-r{{background:rgba(100,200,150,.25);color:#6ee8aa;}}
    .lb-info{{color:rgba(255,255,255,.75);font-size:1rem;margin:12px 0 4px;font-family:serif;font-style:italic;}}
    .lb-pessoas span{{background:rgba(255,255,255,.09);border-radius:8px;padding:2px 9px;margin:0 3px;font-size:.78rem;color:rgba(255,255,255,.45);}}
    .face-tag{{position:absolute;border:2px solid rgba(110,232,170,.65);border-radius:5px;cursor:default;}}
    .face-tag:hover{{border-color:#6ee8aa;}}
    .face-label{{position:absolute;bottom:calc(100% + 3px);left:50%;transform:translateX(-50%);background:rgba(10,20,15,.95);border:1px solid rgba(110,232,170,.4);border-radius:5px;padding:2px 9px;font-size:11px;color:#6ee8aa;white-space:nowrap;opacity:0;transition:opacity .15s;pointer-events:none;}}
    .face-tag:hover .face-label{{opacity:1;}}
    </style>
    <div class="lb-body">
      <div class="lb-side" id="lado-antiga">
        <img src="{lb_foto['antiga']}" id="img-antiga">
        <span class="lb-badge badge-a">Foto antiga</span>
      </div>
      <div class="lb-side" id="lado-restaurada">
        <img src="{lb_foto['restaurada']}" id="img-restaurada">
        <span class="lb-badge badge-r">✨ Restaurada</span>
      </div>
    </div>
    <div class="lb-info">{lb_foto.get('titulo','')}</div>
    <div class="lb-pessoas">{tags_lb}</div>
    <script>
    // Injeta face tags nos lados corretos
    const faces = {json.dumps(lb_foto.get('faces',[]))};
    faces.forEach(fc => {{
      const container = document.getElementById('lado-' + fc.lado);
      if(!container) return;
      const tag = document.createElement('div');
      tag.className = 'face-tag';
      tag.style.cssText = 'left:'+fc.x+'%;top:'+fc.y+'%;width:'+fc.w+'%;height:'+fc.h+'%;';
      const label = document.createElement('span');
      label.className = 'face-label';
      label.textContent = fc.nome;
      tag.appendChild(label);
      container.appendChild(tag);
    }});
    </script>
    """, height=620)

    if st.button("✖ Fechar", use_container_width=True):
        st.session_state.lb_foto_id = None
        st.rerun()

    # Marcação de rostos
    with st.expander("🏷️ Marcar rostos nesta foto"):
        st.caption("Informe a posição aproximada do rosto (% da imagem) e o nome da pessoa.")
        faces_atuais = lb_foto.get("faces", [])

        c1,c2,c3 = st.columns(3)
        with c1:
            lado_n = st.selectbox("Lado", ["antiga","restaurada"], key="face_lado")
            nome_n = st.selectbox("Pessoa", ["(outro)"] + [p["nome"] for p in arvore()], key="face_nome_sel")
            if nome_n == "(outro)":
                nome_n = st.text_input("Nome manual", key="face_nome_manual")
        with c2:
            x_n = st.slider("← Posição horizontal (X %)", 0, 90, 30, key="face_x")
            y_n = st.slider("↕ Posição vertical (Y %)",   0, 90, 20, key="face_y")
        with c3:
            w_n = st.slider("↔ Largura (%)",  3, 40, 12, key="face_w")
            h_n = st.slider("↕ Altura (%)",   3, 50, 18, key="face_h")

        col_add, col_clear = st.columns(2)
        with col_add:
            if st.button("➕ Adicionar marcação", use_container_width=True, type="primary", key="btn_add_face"):
                if nome_n and nome_n != "(outro)":
                    faces_atuais.append({"lado":lado_n,"nome":nome_n,"x":x_n,"y":y_n,"w":w_n,"h":h_n})
                    lb_foto["faces"] = faces_atuais
                    _salvar_faces(lb_foto["id"], faces_atuais)
                    st.success(f"✅ {nome_n} marcado!")
                    st.rerun()
        with col_clear:
            if st.button("🗑️ Limpar todos os rostos", use_container_width=True, key="btn_clear_face"):
                lb_foto["faces"] = []
                _salvar_faces(lb_foto["id"], [])
                st.rerun()

        if faces_atuais:
            st.markdown("**Rostos marcados:**")
            for i, fc in enumerate(faces_atuais):
                colA, colB = st.columns([4,1])
                with colA:
                    st.markdown(f"- **{fc['nome']}** — lado: {fc['lado']} | X:{fc['x']}% Y:{fc['y']}% {fc['w']}×{fc['h']}%")
                with colB:
                    if st.button("✕", key=f"rm_face_{i}"):
                        faces_atuais.pop(i)
                        lb_foto["faces"] = faces_atuais
                        _salvar_faces(lb_foto["id"], faces_atuais)
                        st.rerun()

    st.divider()

# ─────────────────────────────────────────────────────────────────────
# Filtros
# ─────────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([2,2,1])
with col_f1:
    filtro_pessoa = st.selectbox(
        "🔍 Filtrar por pessoa",
        ["Todas"] + [p["nome"] for p in arvore()],
        key="gal_filtro_pessoa"
    )
with col_f2:
    busca = st.text_input("🔎 Buscar por título", placeholder="Ex: casamento, família...", key="gal_busca", label_visibility="collapsed")
with col_f3:
    if st.button("🔄 Atualizar", use_container_width=True):
        _carregar.clear()
        st.session_state.gal_carregado = False
        del st.session_state["gal_carregado"]
        st.rerun()

# Filtra
fotos = acervo()
if filtro_pessoa != "Todas":
    pid_fil = next((p["id"] for p in arvore() if p["nome"]==filtro_pessoa), None)
    if pid_fil:
        fotos = [f for f in fotos if pid_fil in f.get("pessoas",[])]
if busca.strip():
    fotos = [f for f in fotos if busca.lower() in f.get("titulo","").lower()]

# ─────────────────────────────────────────────────────────────────────
# Grid de fotos
# ─────────────────────────────────────────────────────────────────────
if not fotos:
    st.markdown(
        '<div style="text-align:center;padding:60px 20px;color:rgba(255,255,255,.18);">'
        '<div style="font-size:2.5rem;opacity:.25;margin-bottom:14px">🖼️</div>'
        '<p>Nenhuma foto encontrada.</p></div>', unsafe_allow_html=True
    )
else:
    st.caption(f"{len(fotos)} foto(s)")
    cols_por_linha = 3
    rows = [fotos[i:i+cols_por_linha] for i in range(0, len(fotos), cols_por_linha)]

    for row in rows:
        cols = st.columns(cols_por_linha)
        for col, foto in zip(cols, row):
            nomes = [_nome_curto(pid) for pid in foto.get("pessoas",[]) if next((p for p in arvore() if p["id"]==pid), None)]
            tags  = "".join(f"<span>{n}</span>" for n in nomes)
            pess_html = f'<div class="foto-card-pessoas">{tags}</div>' if tags else ""
            with col:
                st.markdown(
                    f'<div class="foto-card">'
                    f'<img src="{foto["antiga"]}" alt="{foto["titulo"]}">'
                    f'<div class="foto-card-info">'
                    f'<div class="foto-card-titulo">{foto.get("titulo","")}</div>'
                    f'{pess_html}'
                    f'</div></div>',
                    unsafe_allow_html=True
                )
                if st.button("🔍 Ver lado a lado", key="lb_"+foto["id"], use_container_width=True):
                    st.session_state.lb_foto_id = foto["id"]
                    st.rerun()

st.divider()

# ─────────────────────────────────────────────────────────────────────
# Adicionar nova foto
# ─────────────────────────────────────────────────────────────────────
with st.expander("➕ Adicionar nova foto ao acervo"):
    tit_n = st.text_input("Nome da foto", placeholder="Ex: Família reunida em 1980", key="gal_tit")
    if arvore():
        nomes_map = {p["nome"]: p["id"] for p in arvore()}
        sel_pess  = st.multiselect("👥 Quem aparece nessa foto?", list(nomes_map.keys()), key="gal_pess")
    else:
        sel_pess = []
        st.info("Adicione pessoas na árvore primeiro.")
    fa_n = st.file_uploader("🕰️ Foto antiga",    type=["jpg","jpeg","png","webp"], key="gal_fa")
    fr_n = st.file_uploader("✨ Foto restaurada", type=["jpg","jpeg","png","webp"], key="gal_fr")
    if fa_n: st.image(fa_n, use_container_width=True)
    if fr_n: st.image(fr_n, use_container_width=True)

    if st.button("💾 Salvar no acervo", use_container_width=True, type="primary", key="gal_btn_add"):
        if not fa_n or not fr_n:
            st.warning("Selecione as duas fotos.")
        else:
            with st.spinner("Enviando fotos..."):
                try:
                    fa_n.seek(0); fr_n.seek(0)
                    ua = _upload(fa_n.read(), fa_n.name)
                    ur = _upload(fr_n.read(), fr_n.name)
                    ids_sel = [nomes_map[n] for n in sel_pess] if arvore() else []
                    nova = {
                        "id":         "f"+str(int(time.time()*1000)),
                        "titulo":     tit_n.strip() or "Sem título",
                        "data":       datetime.now().strftime("%d/%m/%Y"),
                        "antiga":     ua,
                        "restaurada": ur,
                        "pessoas":    ids_sel,
                        "faces":      []
                    }
                    ok = _salvar_foto_sheets(nova, arvore())
                    if ok:
                        st.success("✅ Foto salva no acervo!")
                        st.session_state.gal_acervo.insert(0, nova)
                        st.rerun()
                except Exception as e:
                    st.error("Erro: "+str(e))
