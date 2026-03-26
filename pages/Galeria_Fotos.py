# -*- coding: utf-8 -*-
# pages/1_Galeria_Fotos.py

import streamlit as st
import streamlit.components.v1 as components
import json, os, hashlib, time, urllib.request, base64
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Galeria — Raízes", page_icon="📷", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
footer{display:none!important}#MainMenu{display:none!important}header{display:none!important}
.gal-header{text-align:center;padding:30px 20px 18px;}
.gal-header h1{font-family:'Cormorant Garamond',serif;font-size:2.4rem;font-weight:600;color:rgba(255,255,255,.92);margin:0 0 6px;}
.gal-header p{font-size:.82rem;color:rgba(255,255,255,.35);margin:0;}
.foto-card{border-radius:12px;overflow:hidden;background:#111;border:1px solid rgba(255,255,255,.08);cursor:pointer;transition:transform .2s,border-color .2s;}
.foto-card:hover{transform:translateY(-3px);border-color:rgba(255,255,255,.2);}
.foto-card img{width:100%;height:200px;object-fit:cover;display:block;}
.foto-card-info{padding:10px 12px 12px;}
.foto-card-tit{font-family:'Cormorant Garamond',serif;font-size:.92rem;font-style:italic;color:rgba(255,255,255,.8);}
.foto-card-pess{font-size:.7rem;color:rgba(255,255,255,.3);margin-top:3px;}
.foto-card-pess span{background:rgba(255,255,255,.07);border-radius:6px;padding:1px 6px;margin-right:2px;}
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.03)!important;border:1px dashed rgba(255,255,255,.14)!important;border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────
def _s(k, d=""):
    try: return str(st.secrets[k]).strip() or d
    except: pass
    _MAP = {"CLOUDINARY_API_KEY":("CLOUDINARY","api_key"),
            "CLOUDINARY_API_SECRET":("CLOUDINARY","api_secret"),
            "CLOUDINARY_CLOUD_NAME":("CLOUDINARY","cloud_name")}
    if k in _MAP:
        sec,sub = _MAP[k]
        try: return str(st.secrets[sec][sub]).strip() or d
        except: pass
    return os.environ.get(k, d)

# ── Google Sheets ─────────────────────────────────────────────────────
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def _gc():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["GCP_SERVICE_ACCOUNT"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

def _extrair_key(u):
    import re
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", u)
    return m.group(1) if m else u

def _get_sh():
    return _gc().open_by_key(_extrair_key(_s("PLANILHA_URL_RAIZES") or _s("PLANILHA_URL")))

_COLS_P = ["id","nome","relacao","genero","nascimento","falecimento","foto_perfil",
           "conjuge_id","conjuge_nome","pai_id","pai_nome","mae_id","mae_nome",
           "irmao_de_id","irmao_de_nome","foto_ids"]
_COLS_F = ["id","titulo","data","antiga","restaurada","pessoas_ids","pessoas_nomes"]

@st.cache_data(ttl=30, show_spinner=False)
def _carregar():
    try:
        sh = _get_sh()
        try:
            rows_p = sh.worksheet("Pessoas").get_all_records(expected_headers=_COLS_P)
        except: rows_p = []
        arvore = [{"id":str(r["id"]),"nome":str(r["nome"]),"relacao":str(r.get("relacao","")),
                   "foto_perfil":str(r.get("foto_perfil",""))}
                  for r in rows_p if r.get("id") and r.get("nome")]
        try:
            rows_f = sh.worksheet("Fotos").get_all_records(expected_headers=_COLS_F)
        except: rows_f = []
        acervo = []
        for r in rows_f:
            if not r.get("id") or not r.get("antiga"): continue
            ids_str = str(r.get("pessoas_ids",""))
            acervo.append({
                "id":str(r["id"]), "titulo":str(r.get("titulo","")),
                "data":str(r.get("data","")), "antiga":str(r["antiga"]),
                "restaurada":str(r.get("restaurada","")),
                "pessoas":[x.strip() for x in ids_str.split(",") if x.strip()],
                "faces":json.loads(str(r.get("faces","[]") or "[]")),
            })
        return arvore, acervo
    except Exception as e:
        st.error("Erro ao carregar: "+str(e)); return [],[]

def _salvar_titulo(foto_id, titulo):
    try:
        ws = _get_sh().worksheet("Fotos")
        rows = ws.get_all_values()
        header = rows[0] if rows else []
        col = header.index("titulo")+1 if "titulo" in header else None
        if not col: return
        for i,row in enumerate(rows[1:],start=2):
            if row and row[0]==foto_id:
                ws.update_cell(i, col, titulo)
                _carregar.clear(); return
    except Exception as e: st.error("Erro: "+str(e))

def _salvar_foto_perfil(pessoa_id, url):
    try:
        ws = _get_sh().worksheet("Pessoas")
        rows = ws.get_all_values()
        header = rows[0] if rows else []
        col = header.index("foto_perfil")+1 if "foto_perfil" in header else None
        if not col: return
        for i,row in enumerate(rows[1:],start=2):
            if row and row[0]==pessoa_id:
                ws.update_cell(i, col, url)
                _carregar.clear(); return
    except Exception as e: st.error("Erro: "+str(e))

def _salvar_foto_sheets(nova, arvore):
    try:
        ws = _get_sh().worksheet("Fotos")
        ids_str   = ",".join(nova.get("pessoas",[]))
        nomes_str = ",".join(next((p["nome"] for p in arvore if p["id"]==pid),"") for pid in nova.get("pessoas",[]))
        ws.append_row([nova["id"],nova["titulo"],nova["data"],nova["antiga"],nova["restaurada"],ids_str,nomes_str,"[]"])
        _carregar.clear(); return True
    except Exception as e: st.error("Erro: "+str(e)); return False

# ── Cloudinary ────────────────────────────────────────────────────────
def _upload(fb, fname, folder="Raizes"):
    cloud=_s("CLOUDINARY_CLOUD_NAME","db8ipmete"); akey=_s("CLOUDINARY_API_KEY"); asec=_s("CLOUDINARY_API_SECRET")
    if not akey: raise ValueError("CLOUDINARY_API_KEY não configurada.")
    ts=str(int(time.time())); pid=folder+"/"+Path(fname).stem+"_"+ts
    sig=hashlib.sha1(("folder="+folder+"&public_id="+pid+"&timestamp="+ts+asec).encode()).hexdigest()
    b="----B"+ts
    body=("--"+b+"\r\nContent-Disposition: form-data; name=\"file\"; filename=\""+fname+"\"\r\nContent-Type: image/jpeg\r\n\r\n").encode()
    body+=fb
    body+=("\r\n--"+b+"\r\nContent-Disposition: form-data; name=\"api_key\"\r\n\r\n"+akey+"\r\n"
           "--"+b+"\r\nContent-Disposition: form-data; name=\"timestamp\"\r\n\r\n"+ts+"\r\n"
           "--"+b+"\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\n"+folder+"\r\n"
           "--"+b+"\r\nContent-Disposition: form-data; name=\"public_id\"\r\n\r\n"+pid+"\r\n"
           "--"+b+"\r\nContent-Disposition: form-data; name=\"signature\"\r\n\r\n"+sig+"\r\n"
           "--"+b+"--\r\n").encode()
    req=urllib.request.Request("https://api.cloudinary.com/v1_1/"+cloud+"/image/upload",
        data=body,headers={"Content-Type":"multipart/form-data; boundary="+b})
    with urllib.request.urlopen(req,timeout=40) as r: return json.loads(r.read())["secure_url"]

# ── Session state ─────────────────────────────────────────────────────
if "gal_ok" not in st.session_state:
    arv,acv = _carregar()
    st.session_state.gal_arv = arv
    st.session_state.gal_acv = acv
    st.session_state.gal_ok  = True
if "viewer_id"   not in st.session_state: st.session_state.viewer_id   = None
if "crop_pid"    not in st.session_state: st.session_state.crop_pid    = None

def arv(): return st.session_state.gal_arv
def acv(): return st.session_state.gal_acv
def _nc(pid): 
    p=next((x for x in arv() if x["id"]==pid),None)
    return p["nome"].split()[0] if p else "?"

# ═════════════════════════════════════════════════════════════════════
# VIEWER FULLSCREEN com zoom + slider comparação
# ═════════════════════════════════════════════════════════════════════
if st.session_state.viewer_id:
    foto = next((f for f in acv() if f["id"]==st.session_state.viewer_id), None)
    if foto:
        nomes = [_nc(pid) for pid in foto.get("pessoas",[]) if next((p for p in arv() if p["id"]==pid),None)]
        tags  = "".join(f"<span style='background:rgba(255,255,255,.1);border-radius:8px;padding:2px 10px;margin:0 4px;font-size:.8rem;color:rgba(255,255,255,.6)'>{n}</span>" for n in nomes)

        components.html(f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#0a0a0a;color:#fff;font-family:'DM Sans',sans-serif;overflow:hidden;height:100vh;display:flex;flex-direction:column;}}
.toolbar{{display:flex;align-items:center;gap:10px;padding:10px 16px;background:rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.08);flex-shrink:0;}}
.btn{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);color:rgba(255,255,255,.85);border-radius:8px;padding:5px 14px;cursor:pointer;font-size:.8rem;transition:background .15s;}}
.btn:hover{{background:rgba(255,255,255,.2);}}
.btn.active{{background:rgba(110,232,170,.2);border-color:rgba(110,232,170,.4);color:#6ee8aa;}}
.titulo{{font-family:serif;font-style:italic;font-size:1rem;color:rgba(255,255,255,.7);flex:1;}}
.pessoas{{font-size:.75rem;}}
.viewer{{flex:1;position:relative;overflow:hidden;display:flex;}}
/* Modo lado a lado */
#modo-lado{{display:flex;width:100%;height:100%;}}
.lado{{flex:1;position:relative;overflow:hidden;cursor:zoom-in;}}
.lado img{{width:100%;height:100%;object-fit:contain;display:block;transform-origin:center center;transition:transform .1s;}}
.lado-badge{{position:absolute;bottom:12px;left:12px;font-size:10px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;padding:3px 10px;border-radius:20px;pointer-events:none;}}
.badge-a{{background:rgba(200,170,100,.3);color:#e8c97a;}}
.badge-r{{background:rgba(100,200,150,.25);color:#6ee8aa;}}
/* Modo slider */
#modo-slider{{display:none;width:100%;height:100%;position:relative;cursor:col-resize;overflow:hidden;}}
#slider-antiga{{position:absolute;inset:0;}}
#slider-antiga img{{width:100%;height:100%;object-fit:contain;}}
#slider-restaurada{{position:absolute;inset:0;overflow:hidden;}}
#slider-restaurada img{{width:100%;height:100%;object-fit:contain;}}
#slider-linha{{position:absolute;top:0;bottom:0;width:3px;background:#6ee8aa;cursor:col-resize;z-index:10;}}
#slider-handle{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:36px;height:36px;border-radius:50%;background:#6ee8aa;display:flex;align-items:center;justify-content:center;color:#0a2a1a;font-size:1rem;font-weight:700;box-shadow:0 2px 8px rgba(0,0,0,.4);}}
/* Zoom info */
.zoom-info{{position:absolute;bottom:12px;right:12px;background:rgba(0,0,0,.6);border-radius:8px;padding:4px 10px;font-size:.72rem;color:rgba(255,255,255,.5);z-index:20;}}
</style></head><body>

<div class="toolbar">
  <span class="titulo">{foto.get('titulo','Sem título')}</span>
  <span class="pessoas">{tags}</span>
  <button class="btn active" id="btn-lado" onclick="setModo('lado')">⬛⬛ Lado a lado</button>
  <button class="btn" id="btn-slider" onclick="setModo('slider')">◧ Comparar</button>
  <button class="btn" onclick="resetZoom()">🔍 Reset zoom</button>
</div>

<div class="viewer">
  <!-- MODO LADO A LADO -->
  <div id="modo-lado">
    <div class="lado" id="lado-a" onwheel="zoom(event,'a')" onmousedown="startPan(event,'a')" style="border-right:1px solid rgba(255,255,255,.05);">
      <img id="img-a" src="{foto['antiga']}" draggable="false">
      <span class="lado-badge badge-a">ANTIGA</span>
      <span class="zoom-info" id="zoom-a">100%</span>
    </div>
    <div class="lado" id="lado-r" onwheel="zoom(event,'r')" onmousedown="startPan(event,'r')">
      <img id="img-r" src="{foto['restaurada']}" draggable="false">
      <span class="lado-badge badge-r">✨ RESTAURADA</span>
      <span class="zoom-info" id="zoom-r">100%</span>
    </div>
  </div>

  <!-- MODO SLIDER -->
  <div id="modo-slider">
    <div id="slider-antiga"><img src="{foto['antiga']}"></div>
    <div id="slider-restaurada" style="width:50%">
      <img src="{foto['restaurada']}" style="min-width:calc(100vw);position:absolute;left:0;">
    </div>
    <div id="slider-linha" style="left:50%">
      <div id="slider-handle">⇔</div>
    </div>
  </div>
</div>

<script>
// ── Estado de zoom/pan ──────────────────────────────────────────────
const state = {{
  a: {{scale:1, x:0, y:0, panning:false, startX:0, startY:0, ox:0, oy:0}},
  r: {{scale:1, x:0, y:0, panning:false, startX:0, startY:0, ox:0, oy:0}}
}};

function applyTransform(id) {{
  const s = state[id];
  const img = document.getElementById('img-'+id);
  img.style.transform = `scale(${{s.scale}}) translate(${{s.x}}px, ${{s.y}}px)`;
  document.getElementById('zoom-'+id).textContent = Math.round(s.scale*100)+'%';
}}

function zoom(e, id) {{
  e.preventDefault();
  const s = state[id];
  const delta = e.deltaY > 0 ? 0.85 : 1.18;
  s.scale = Math.min(Math.max(s.scale * delta, 0.5), 8);
  applyTransform(id);
}}

function startPan(e, id) {{
  const s = state[id];
  s.panning = true; s.startX = e.clientX; s.startY = e.clientY;
  s.ox = s.x; s.oy = s.y;
  document.getElementById('lado-'+id[0]=='a'?'a':'r').style.cursor='grabbing';
}}

document.addEventListener('mousemove', e => {{
  ['a','r'].forEach(id => {{
    const s = state[id];
    if(!s.panning) return;
    s.x = s.ox + (e.clientX - s.startX) / s.scale;
    s.y = s.oy + (e.clientY - s.startY) / s.scale;
    applyTransform(id);
  }});
}});
document.addEventListener('mouseup', () => {{
  state.a.panning = false; state.r.panning = false;
  document.querySelectorAll('.lado').forEach(el => el.style.cursor='zoom-in');
}});

function resetZoom() {{
  ['a','r'].forEach(id => {{ state[id]={{scale:1,x:0,y:0,panning:false,startX:0,startY:0,ox:0,oy:0}}; applyTransform(id); }});
}}

// ── Slider comparação ───────────────────────────────────────────────
const sliderDiv = document.getElementById('modo-slider');
const linha = document.getElementById('slider-linha');
const restaurada = document.getElementById('slider-restaurada');
let sliderDragging = false;
let sliderPct = 50;

function setSliderPct(pct) {{
  sliderPct = Math.min(Math.max(pct, 2), 98);
  linha.style.left = sliderPct + '%';
  restaurada.style.width = sliderPct + '%';
}}

linha.addEventListener('mousedown', e => {{ sliderDragging = true; e.preventDefault(); }});
sliderDiv.addEventListener('mousemove', e => {{
  if(!sliderDragging) return;
  const r = sliderDiv.getBoundingClientRect();
  setSliderPct((e.clientX - r.left) / r.width * 100);
}});
document.addEventListener('mouseup', () => {{ sliderDragging = false; }});

// Touch support
linha.addEventListener('touchstart', e => {{ sliderDragging = true; }});
sliderDiv.addEventListener('touchmove', e => {{
  if(!sliderDragging) return;
  const r = sliderDiv.getBoundingClientRect();
  setSliderPct((e.touches[0].clientX - r.left) / r.width * 100);
}});
document.addEventListener('touchend', () => {{ sliderDragging = false; }});

// ── Trocar modo ─────────────────────────────────────────────────────
function setModo(modo) {{
  document.getElementById('modo-lado').style.display = modo==='lado' ? 'flex' : 'none';
  document.getElementById('modo-slider').style.display = modo==='slider' ? 'block' : 'none';
  document.getElementById('btn-lado').classList.toggle('active', modo==='lado');
  document.getElementById('btn-slider').classList.toggle('active', modo==='slider');
}}
</script>
</body></html>
        """, height=680, scrolling=False)

        if st.button("✖ Fechar viewer", use_container_width=True):
            st.session_state.viewer_id = None
            st.rerun()

        # Editar título inline
        c1, c2 = st.columns([3,1])
        with c1:
            novo_tit = st.text_input("✏️ Título da foto", value=foto.get("titulo",""), key="vw_tit")
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Salvar título", use_container_width=True):
                foto["titulo"] = novo_tit.strip() or "Sem título"
                _salvar_titulo(foto["id"], foto["titulo"])
                st.rerun()
        st.divider()

# ═════════════════════════════════════════════════════════════════════
# RECORTE DE ROSTO para foto de perfil
# ═════════════════════════════════════════════════════════════════════
if st.session_state.crop_pid:
    pessoa_crop = next((p for p in arv() if p["id"]==st.session_state.crop_pid), None)
    if pessoa_crop:
        st.markdown(f"### ✂️ Recortar foto de perfil — {pessoa_crop['nome'].split()[0]}")
        st.caption("Faça upload de uma foto, arraste para selecionar o rosto e clique em Recortar & Salvar.")

        crop_file = st.file_uploader("Envie a foto", type=["jpg","jpeg","png","webp"], key="crop_file")

        if crop_file:
            img_bytes = crop_file.read()
            img_b64   = base64.b64encode(img_bytes).decode()
            img_ext   = crop_file.name.rsplit(".",1)[-1].lower()
            mime      = "image/png" if img_ext=="png" else "image/jpeg"

            st.markdown("**1. Arraste para selecionar o rosto → clique Recortar**")
            components.html(f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#111;padding:10px;font-family:sans-serif;color:#fff;}}
#wrap{{position:relative;display:inline-block;max-width:100%;}}
#src{{max-width:100%;max-height:380px;display:block;cursor:crosshair;user-select:none;border-radius:8px;}}
#sel{{position:absolute;border:2px dashed #6ee8aa;background:rgba(110,232,170,.15);pointer-events:none;display:none;border-radius:4px;}}
canvas{{display:none;}}
.row{{display:flex;align-items:center;gap:12px;margin-top:10px;}}
.btn{{background:#6ee8aa;color:#0a2a1a;border:none;border-radius:8px;padding:8px 18px;font-size:.85rem;font-weight:700;cursor:pointer;}}
.hint{{font-size:.75rem;color:rgba(255,255,255,.4);}}
#pw{{display:none;align-items:center;gap:10px;margin-top:8px;}}
#preview{{width:72px;height:72px;border-radius:50%;object-fit:cover;border:3px solid #6ee8aa;}}
#b64area{{width:100%;height:55px;font-size:.58rem;background:#1a1a2e;color:#6ee8aa;border:1px solid #6ee8aa;border-radius:6px;padding:6px;resize:none;margin-top:8px;display:none;}}
</style></head><body>
<div id="wrap"><img id="src" src="data:{mime};base64,{img_b64}" draggable="false"><div id="sel"></div></div>
<canvas id="cv"></canvas>
<div class="row">
  <button class="btn" onclick="recortar()">✂️ Recortar</button>
  <span class="hint" id="hint">Arraste para marcar o rosto</span>
</div>
<div id="pw"><img id="preview"><span style="font-size:.8rem;color:#6ee8aa">✅ Pronto! Copie o texto abaixo (Ctrl+A, Ctrl+C)</span></div>
<textarea id="b64area" readonly onclick="this.select()"></textarea>
<script>
const img=document.getElementById("src"),sel=document.getElementById("sel");
let sx=0,sy=0,ex=0,ey=0,drag=false;
img.addEventListener("mousedown",e=>{{const r=img.getBoundingClientRect();sx=e.clientX-r.left;sy=e.clientY-r.top;drag=true;sel.style.display="block";sel.style.left=sx+"px";sel.style.top=sy+"px";sel.style.width="0";sel.style.height="0";}});
document.addEventListener("mousemove",e=>{{if(!drag)return;const r=img.getBoundingClientRect();ex=Math.min(Math.max(e.clientX-r.left,0),img.width);ey=Math.min(Math.max(e.clientY-r.top,0),img.height);sel.style.left=Math.min(sx,ex)+"px";sel.style.top=Math.min(sy,ey)+"px";sel.style.width=Math.abs(ex-sx)+"px";sel.style.height=Math.abs(ey-sy)+"px";}});
document.addEventListener("mouseup",()=>{{drag=false;}});
function recortar(){{
  const cv=document.getElementById("cv");
  const scaleX=img.naturalWidth/img.width,scaleY=img.naturalHeight/img.height;
  const x=Math.min(sx,ex)*scaleX,y=Math.min(sy,ey)*scaleY,w=Math.abs(ex-sx)*scaleX,h=Math.abs(ey-sy)*scaleY;
  if(w<5||h<5){{document.getElementById("hint").textContent="⚠️ Selecione uma área primeiro!";return;}}
  cv.width=200;cv.height=200;
  const ctx=cv.getContext("2d");
  ctx.beginPath();ctx.arc(100,100,100,0,Math.PI*2);ctx.clip();
  ctx.drawImage(img,x,y,w,h,0,0,200,200);
  const d=cv.toDataURL("image/jpeg",0.9);
  document.getElementById("preview").src=d;
  document.getElementById("pw").style.display="flex";
  const ta=document.getElementById("b64area");
  ta.style.display="block";ta.value=d;
  setTimeout(()=>{{ta.select();ta.setSelectionRange(0,99999);}},100);
  document.getElementById("hint").textContent="✅ Texto selecionado — pressione Ctrl+C para copiar!";
}}
</script>
</body></html>""", height=560)

            st.markdown("**2. Cole aqui e salve:**")
            b64_input = st.text_area(
                "Cole o código aqui", placeholder="data:image/jpeg;base64,/9j/...",
                key="b64_in_"+pessoa_crop["id"], height=70, label_visibility="collapsed"
            )
            if b64_input and b64_input.strip().startswith("data:image"):
                try:
                    _, encoded = b64_input.strip().split(",", 1)
                    img_data = base64.b64decode(encoded)
                    c1, c2 = st.columns([1,3])
                    with c1: st.image(b64_input.strip(), width=80)
                    with c2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("💾 Salvar como perfil", use_container_width=True,
                                     type="primary", key="sv_b64_"+pessoa_crop["id"]):
                            with st.spinner("Salvando..."):
                                try:
                                    url_p = _upload(img_data, "perfil.jpg", "Perfis")
                                    pessoa_crop["foto_perfil"] = url_p
                                    _salvar_foto_perfil(pessoa_crop["id"], url_p)
                                    for p in st.session_state.gal_arv:
                                        if p["id"] == pessoa_crop["id"]:
                                            p["foto_perfil"] = url_p
                                    st.success("✅ Foto de perfil salva!")
                                    st.session_state.crop_pid = None
                                    st.rerun()
                                except Exception as e:
                                    st.error("Erro: "+str(e))
                except Exception:
                    st.warning("Texto inválido. Copie tudo a partir de 'data:image...'")

            st.markdown("---")
            st.markdown("**Ou envie uma foto já cortada:**")
            perfil_file = st.file_uploader("Foto pronta", type=["jpg","jpeg","png","webp"], key="perfil_pronto_"+pessoa_crop["id"])
            if perfil_file:
                st.image(perfil_file, width=90)
                if st.button("💾 Salvar como perfil", use_container_width=True,
                             type="primary", key="sv_pf_"+pessoa_crop["id"]):
                    with st.spinner("Enviando..."):
                        try:
                            perfil_file.seek(0)
                            url_p = _upload(perfil_file.read(), perfil_file.name, "Perfis")
                            pessoa_crop["foto_perfil"] = url_p
                            _salvar_foto_perfil(pessoa_crop["id"], url_p)
                            for p in st.session_state.gal_arv:
                                if p["id"] == pessoa_crop["id"]:
                                    p["foto_perfil"] = url_p
                            st.success("✅ Salvo!")
                            st.session_state.crop_pid = None
                            st.rerun()
                        except Exception as e:
                            st.error("Erro: "+str(e))

        if st.button("✖ Cancelar", use_container_width=True, key="cancel_crop"):
            st.session_state.crop_pid = None
            st.rerun()
        st.divider()

# ═════════════════════════════════════════════════════════════════════
# HEADER + FILTROS
# ═════════════════════════════════════════════════════════════════════
st.markdown(
    '<div class="gal-header"><h1>📷 Galeria da Família</h1>'
    '<p>Clique em qualquer foto para abrir o viewer com zoom e comparação</p></div>',
    unsafe_allow_html=True
)

col_f1, col_f2, col_f3 = st.columns([2,2,1])
with col_f1:
    filtro = st.selectbox("👤 Pessoa", ["Todas"]+[p["nome"] for p in arv()], key="gal_fil")
with col_f2:
    busca  = st.text_input("🔎 Buscar título", placeholder="nome, data, evento...", key="gal_busca", label_visibility="collapsed")
with col_f3:
    if st.button("🔄 Atualizar", use_container_width=True):
        _carregar.clear()
        del st.session_state["gal_ok"]
        st.rerun()

fotos = acv()
if filtro != "Todas":
    pid_f = next((p["id"] for p in arv() if p["nome"]==filtro), None)
    fotos = [f for f in fotos if pid_f and pid_f in f.get("pessoas",[])]
if busca.strip():
    fotos = [f for f in fotos if busca.lower() in f.get("titulo","").lower()]

# ═════════════════════════════════════════════════════════════════════
# GRID DE FOTOS
# ═════════════════════════════════════════════════════════════════════
if not fotos:
    st.markdown(
        '<div style="text-align:center;padding:60px;color:rgba(255,255,255,.18);">'
        '<div style="font-size:2.5rem;margin-bottom:12px;opacity:.3">🖼️</div>'
        '<p>Nenhuma foto encontrada.</p></div>', unsafe_allow_html=True
    )
else:
    st.caption(f"{len(fotos)} foto(s)")
    cols_n = 3
    for i in range(0, len(fotos), cols_n):
        cols = st.columns(cols_n)
        for col, foto in zip(cols, fotos[i:i+cols_n]):
            nomes = [_nc(pid) for pid in foto.get("pessoas",[]) if next((p for p in arv() if p["id"]==pid),None)]
            tags  = "".join(f"<span>{n}</span>" for n in nomes)
            pess_html = f'<div class="foto-card-pess">{tags}</div>' if tags else ""
            with col:
                st.markdown(
                    f'<div class="foto-card">'
                    f'<img src="{foto["antiga"]}">'
                    f'<div class="foto-card-info">'
                    f'<div class="foto-card-tit">{foto.get("titulo","") or "Sem título"}</div>'
                    f'{pess_html}</div></div>', unsafe_allow_html=True
                )
                if st.button("🔍 Abrir viewer", key="vw_"+foto["id"], use_container_width=True):
                    st.session_state.viewer_id = foto["id"]
                    st.rerun()

st.divider()

# ═════════════════════════════════════════════════════════════════════
# FOTO DE PERFIL — recortar
# ═════════════════════════════════════════════════════════════════════
st.markdown("### 👤 Foto de perfil")
st.caption("Selecione uma pessoa para definir ou atualizar a foto de perfil.")
if arv():
    cols_perf = st.columns(min(len(arv()), 5))
    for col, p in zip(cols_perf, arv()):
        with col:
            url = p.get("foto_perfil","")
            if url:
                st.markdown(f'<img src="{url}" style="width:60px;height:60px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,.2);display:block;margin:0 auto 6px;">', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="width:60px;height:60px;border-radius:50%;background:rgba(255,255,255,.07);border:2px dashed rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:1.4rem;margin:0 auto 6px;">👤</div>', unsafe_allow_html=True)
            st.caption(p["nome"].split()[0])
            if st.button("✏️ Foto", key="crop_"+p["id"], use_container_width=True):
                st.session_state.crop_pid = p["id"]
                st.rerun()

st.divider()

# ═════════════════════════════════════════════════════════════════════
# ADICIONAR NOVA FOTO
# ═════════════════════════════════════════════════════════════════════
with st.expander("➕ Adicionar nova foto ao acervo"):
    tit_n = st.text_input("Nome da foto", placeholder="Ex: Família reunida em 1980", key="gal_tit")
    if arv():
        nomes_map = {p["nome"]: p["id"] for p in arv()}
        sel_p = st.multiselect("👥 Quem aparece?", list(nomes_map.keys()), key="gal_pess")
    else:
        sel_p = []; st.info("Adicione pessoas na árvore primeiro.")
    fa_n = st.file_uploader("🕰️ Foto antiga",    type=["jpg","jpeg","png","webp"], key="gal_fa")
    fr_n = st.file_uploader("✨ Foto restaurada", type=["jpg","jpeg","png","webp"], key="gal_fr")
    if fa_n: st.image(fa_n, use_container_width=True)
    if fr_n: st.image(fr_n, use_container_width=True)
    if st.button("💾 Salvar no acervo", use_container_width=True, type="primary", key="gal_btn"):
        if not fa_n or not fr_n:
            st.warning("Selecione as duas fotos.")
        else:
            with st.spinner("Enviando fotos..."):
                try:
                    fa_n.seek(0); fr_n.seek(0)
                    ua = _upload(fa_n.read(), fa_n.name)
                    ur = _upload(fr_n.read(), fr_n.name)
                    nova = {"id":"f"+str(int(time.time()*1000)),"titulo":tit_n.strip() or "Sem título",
                            "data":datetime.now().strftime("%d/%m/%Y"),"antiga":ua,"restaurada":ur,
                            "pessoas":[nomes_map[n] for n in sel_p],"faces":[]}
                    if _salvar_foto_sheets(nova, arv()):
                        st.success("✅ Foto salva!")
                        st.session_state.gal_acv.insert(0, nova)
                        st.rerun()
                except Exception as e: st.error("Erro: "+str(e))
