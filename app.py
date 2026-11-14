"""
Maré Boa, assistente de surf do Rio de Janeiro.
Interface Streamlit do agente construido no notebook do projeto.

Execucao local:
    pip install -r requirements.txt
    streamlit run app.py

Execucao no Colab (com tunel):
    !pip install -q streamlit pyngrok
    !streamlit run app.py --server.port 8501 &>/dev/null&
    from pyngrok import ngrok; print(ngrok.connect(8501))
"""
import os, json, re, math, sqlite3
from datetime import date, timedelta

import requests
import streamlit as st

# ----------------------------------------------------------------------------
# 1. PAGINA E IDENTIDADE VISUAL
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Maré Boa", page_icon="🌊", layout="wide",
                   initial_sidebar_state="expanded")

CORES = {
    "creme":       "#F2EFE4",   # off-white, fundo
    "creme_claro": "#FAF8F1",
    "chumbo":      "#2E3338",   # texto principal
    "chumbo_sutil":"#6B7278",
    "azul_fundo":  "#15406B",   # azul profundo
    "azul_medio":  "#2E6DA4",   # azul principal
    "azul_claro":  "#A9C9E4",   # azul azulejo
    "amarelo":     "#E0B04A",   # acento
    "amarelo_sutil":"#F4E4BC",
    "verde":       "#4A7C59",
    "vermelho":    "#A8432F",
}

FONTES = ("https://fonts.googleapis.com/css2?family=Bebas+Neue&"
          "family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700&"
          "family=Caveat:wght@600&display=swap")

# O CSS precisa ser uma string SEM linhas em branco: o markdown do Streamlit
# trata linha vazia como fim do bloco HTML e o restante vaza como texto na tela.
_CSS = (
  "@import url('" + FONTES + "');"
  ":root{"
  f"--creme:{CORES['creme']};--creme-claro:{CORES['creme_claro']};"
  f"--chumbo:{CORES['chumbo']};--chumbo-sutil:{CORES['chumbo_sutil']};"
  f"--azul-fundo:{CORES['azul_fundo']};--azul-medio:{CORES['azul_medio']};"
  f"--azul-claro:{CORES['azul_claro']};--amarelo:{CORES['amarelo']};"
  f"--amarelo-sutil:{CORES['amarelo_sutil']};"
  "}"
  ".stApp{background:var(--creme);}"
  "html,body,[class*='css'],.stMarkdown,p,li,span,div{font-family:'DM Sans',system-ui,sans-serif;color:var(--chumbo);}"
  "h1,h2,h3{font-family:'Bebas Neue',Impact,sans-serif!important;letter-spacing:.035em;color:var(--azul-fundo)!important;}"
  ".marca{display:flex;align-items:center;gap:1rem;padding:1.1rem 1.4rem;margin-bottom:1.3rem;background:var(--azul-fundo);border-radius:14px;}"
  ".marca h1{margin:0;font-size:2.6rem;line-height:1;color:var(--creme)!important;}"
  ".marca .sub{font-family:'Caveat',cursive;font-size:1.2rem;color:var(--azul-claro);margin-top:.1rem;}"
  ".card{background:var(--creme-claro);border:1px solid rgba(46,109,164,.22);border-left:6px solid var(--azul-medio);border-radius:14px;padding:1.15rem 1.3rem;margin-bottom:1.5rem;}"
  ".card.topo{border-left-color:var(--amarelo);background:#FCF7E9;}"
  ".card-cabeca{display:flex;justify-content:space-between;align-items:center;margin-bottom:.7rem;}"
  ".card-nome{font-family:'Bebas Neue',sans-serif;font-size:2rem;line-height:1;letter-spacing:.035em;color:var(--azul-fundo);}"
  ".card-nota{display:flex;flex-direction:column;align-items:flex-end;line-height:1;}"
  ".card-nota b{font-size:2rem;font-weight:700;color:var(--azul-medio);}"
  ".card-nota small{font-size:.62rem;letter-spacing:.09em;text-transform:uppercase;color:var(--chumbo-sutil);margin-top:.18rem;}"
  ".card.topo .card-nota b{color:#B8860B;}"
  ".card-dados{display:flex;flex-wrap:wrap;gap:.45rem;margin-bottom:.65rem;}"
  ".pilula{background:var(--azul-claro);color:var(--azul-fundo);padding:.22rem .68rem;border-radius:999px;font-size:.78rem;font-weight:500;}"
  ".pilula.alerta{background:#F2C9C0;color:#7A2E1E;}"
  ".pilula.bom{background:#CFE3D4;color:#2F5438;}"
  ".card-motivos{font-size:.85rem;color:var(--chumbo-sutil);line-height:1.6;border-top:1px solid rgba(46,109,164,.14);padding-top:.6rem;}"
  ".stChatMessage{background:var(--creme-claro)!important;border:1px solid rgba(46,109,164,.16);border-radius:12px;}"
  "[data-testid='stSidebar']{background:var(--creme-claro);border-right:1px solid rgba(46,109,164,.18);}"
  ".stButton button{background:var(--azul-medio);color:var(--creme);border:none;border-radius:9px;font-weight:500;}"
  ".stButton button:hover{background:var(--azul-fundo);color:#fff;}"
  ".legenda{font-size:.8rem;color:var(--chumbo-sutil);line-height:1.6;}"
  "hr{border-color:rgba(46,109,164,.18);}"
  "#MainMenu,footer,header{visibility:hidden;}"
)
st.markdown("<style>" + _CSS + "</style>", unsafe_allow_html=True)


LOGO_SVG = f"""<svg class="marca-logo" width="48" height="48" viewBox="0 0 48 48" fill="none">
  <circle cx="24" cy="24" r="23" fill="{CORES['creme']}"/>
  <path d="M6 30c4-7 9-11 14-11 6 0 8 5 8 9 0 3-2 6-5 6-2 0-4-2-4-4 0-2 1-3 3-3"
        stroke="{CORES['azul_fundo']}" stroke-width="2.6" stroke-linecap="round" fill="none"/>
  <path d="M5 36c3 0 3 2 6 2s3-2 6-2 3 2 6 2 3-2 6-2 3 2 6 2 3-2 6-2"
        stroke="{CORES['azul_medio']}" stroke-width="2.2" stroke-linecap="round" fill="none"/>
  <circle cx="34" cy="15" r="4.5" fill="{CORES['amarelo']}"/>
</svg>"""

st.markdown(
    '<div class="marca">' + LOGO_SVG +
    '<div style="display:flex;flex-direction:column;justify-content:center">'
    "<span style=\"font-family:'Bebas Neue',Impact,sans-serif;font-size:2.7rem;"
    "line-height:1;letter-spacing:.04em;color:" + CORES["creme"] + "\">MARÉ BOA</span>"
    "<span style=\"font-family:'Caveat',cursive;font-size:1.2rem;margin-top:.15rem;"
    "color:" + CORES["azul_claro"] + "\">onde surfar hoje, no Rio</span>"
    '</div></div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# 2. DADOS DO DOMINIO
# ----------------------------------------------------------------------------
PRAIAS = [
    {"nome": "Arpoador", "lat": -23.002, "lon": -43.193, "orientacao": 170,
     "regiao": "Zona Sul", "fundo": "areia", "nivel_min": "iniciante",
     "swell_ideal": [135, 200], "mare_ideal": "qualquer",
     "obs": "Pico classico, pega quase todo swell de sul e sudeste, bastante gente na agua."},
    {"nome": "Leblon", "lat": -23.000, "lon": -43.222, "orientacao": 180,
     "regiao": "Zona Sul", "fundo": "areia", "nivel_min": "iniciante",
     "swell_ideal": [150, 210], "mare_ideal": "enchente",
     "obs": "Ondas menores que o Arpoador, o canto protege do vento leste."},
    {"nome": "Barra da Tijuca", "lat": -23.020, "lon": -43.330, "orientacao": 185,
     "regiao": "Zona Oeste", "fundo": "areia", "nivel_min": "iniciante",
     "swell_ideal": [150, 220], "mare_ideal": "qualquer",
     "obs": "Praia extensa com varios picos, a condicao varia ao longo da orla."},
    {"nome": "Recreio", "lat": -23.035, "lon": -43.470, "orientacao": 200,
     "regiao": "Zona Oeste", "fundo": "areia", "nivel_min": "intermediario",
     "swell_ideal": [160, 230], "mare_ideal": "vazante",
     "obs": "Pega bem sul e sudoeste, correnteza forte quando o mar cresce."},
    {"nome": "Macumba", "lat": -23.040, "lon": -43.510, "orientacao": 210,
     "regiao": "Zona Oeste", "fundo": "areia", "nivel_min": "iniciante",
     "swell_ideal": [170, 240], "mare_ideal": "enchente",
     "obs": "Onda mais lenta e longa, uma das melhores da cidade para aprender."},
    {"nome": "Prainha", "lat": -23.055, "lon": -43.505, "orientacao": 180,
     "regiao": "Zona Oeste", "fundo": "areia e pedra", "nivel_min": "avancado",
     "swell_ideal": [150, 210], "mare_ideal": "qualquer",
     "obs": "Onda potente em area de protecao ambiental, nao indicada para iniciantes."},
    {"nome": "Grumari", "lat": -23.058, "lon": -43.530, "orientacao": 200,
     "regiao": "Zona Oeste", "fundo": "areia", "nivel_min": "intermediario",
     "swell_ideal": [160, 230], "mare_ideal": "qualquer",
     "obs": "Praia preservada, sem estrutura de apoio, acesso so de carro."},
    {"nome": "Itacoatiara", "lat": -22.985, "lon": -43.030, "orientacao": 135,
     "regiao": "Niteroi", "fundo": "areia e pedra", "nivel_min": "avancado",
     "swell_ideal": [90, 180], "mare_ideal": "qualquer",
     "obs": "Pega swell de leste que nao entra no Rio, onda pesada, so para experientes."},
]
NOMES_PRAIAS = [p["nome"] for p in PRAIAS]

SERVICOS = [
    ("Arpoador","aluguel_prancha","Galeria River",50.0,"09h-18h","Varias lojas no quarteirao"),
    ("Arpoador","escola","Escola de Surf Rico de Souza",120.0,"07h-16h","Aula com prancha inclusa"),
    ("Arpoador","comida","Quiosque do Arpoador",35.0,"08h-20h","Acai e sanduiche"),
    ("Leblon","aluguel_prancha","Posto 12 Surf",45.0,"08h-17h","Aluguel por hora"),
    ("Leblon","comida","Quiosque Leblon Posto 11",40.0,"08h-22h","Petisco e agua de coco"),
    ("Barra da Tijuca","aluguel_prancha","Barra Surf Center",40.0,"07h-19h","Softboard para iniciante"),
    ("Barra da Tijuca","escola","Escola de Surf da Barra",100.0,"06h-17h","Turma de iniciante aos sabados"),
    ("Barra da Tijuca","comida","Quiosque Pepe",45.0,"08h-21h","Sanduiche natural"),
    ("Recreio","aluguel_prancha","Recreio Surf Shop",45.0,"07h-18h","Prancha e longboard"),
    ("Recreio","comida","Quiosque Posto 12 Recreio",30.0,"08h-19h","Peixe frito e caldinho"),
    ("Macumba","aluguel_prancha","Macumba Surf House",35.0,"06h-18h","Mais barato da cidade"),
    ("Macumba","escola","Escolinha da Macumba",90.0,"06h-15h","Melhor pico para aprender"),
    ("Macumba","comida","Barraca da Praia da Macumba",25.0,"08h-18h","Comida caseira"),
    ("Prainha","comida","Quiosque da Prainha",50.0,"09h-17h","Unica opcao, area de protecao"),
    ("Itacoatiara","aluguel_prancha","Ita Surf",55.0,"08h-17h","Pranchas para onda grande"),
    ("Itacoatiara","comida","Restaurante de Itacoatiara",60.0,"11h-20h","Frutos do mar"),
]
ACESSOS = [
    ("Arpoador","dificil, rua","metro Gal. Osorio + 10 min a pe",25),
    ("Leblon","dificil, rua","metro Antero de Quental + 8 min",30),
    ("Barra da Tijuca","facil, gratuito na orla","BRT Jardim Oceanico",40),
    ("Recreio","facil, gratuito","BRT Recreio Shopping",55),
    ("Macumba","facil, gratuito","onibus, pouca oferta",60),
    ("Prainha","limitado, enche cedo","nao ha",70),
    ("Grumari","limitado","nao ha",75),
    ("Itacoatiara","pago, cerca de 30 reais","onibus de Niteroi",70),
]


# ----------------------------------------------------------------------------
# 3. PREVISAO E PONTUACAO
# ----------------------------------------------------------------------------
PREVISAO_SIMULADA = {
    "wave_height": 1.3, "wave_period": 11.0, "wave_direction": 185.0,
    "swell_wave_height": 1.1, "swell_wave_period": 12.5, "swell_wave_direction": 190.0,
    "sea_surface_temperature": 23.4, "wind_speed_10m": 11.0,
    "wind_direction_10m": 25.0, "wind_gusts_10m": 18.0, "temperature_2m": 27.5,
}

@st.cache_data(ttl=1800, show_spinner=False)
def buscar_previsao(lat, lon, dia_offset=0, hora=9, demo=False):
    if demo:
        return {**PREVISAO_SIMULADA, "_fonte": "simulado",
                "_quando": (date.today()+timedelta(days=dia_offset)).isoformat()+f" {hora:02d}h"}
    alvo = date.today() + timedelta(days=dia_offset)
    idx = dia_offset * 24 + hora
    saida = {"_fonte": "open-meteo", "_quando": f"{alvo.isoformat()} {hora:02d}h"}
    try:
        v = ("wave_height,wave_period,wave_direction,swell_wave_height,"
             "swell_wave_period,swell_wave_direction,sea_surface_temperature")
        r = requests.get("https://marine-api.open-meteo.com/v1/marine",
                         params={"latitude": lat, "longitude": lon, "hourly": v,
                                 "forecast_days": 7, "timezone": "America/Sao_Paulo"},
                         timeout=20)
        r.raise_for_status(); h = r.json()["hourly"]
        for k in v.split(","):
            s = h.get(k) or []
            saida[k] = s[idx] if idx < len(s) else None
    except Exception as e:
        saida["_erro_marine"] = str(e)
    try:
        v = "wind_speed_10m,wind_direction_10m,wind_gusts_10m,temperature_2m"
        r = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": lat, "longitude": lon, "hourly": v,
                                 "forecast_days": 7, "timezone": "America/Sao_Paulo"},
                         timeout=20)
        r.raise_for_status(); h = r.json()["hourly"]
        for k in v.split(","):
            s = h.get(k) or []
            saida[k] = s[idx] if idx < len(s) else None
    except Exception as e:
        saida["_erro_forecast"] = str(e)
    return saida


def _dif_ang(a, b):
    d = abs((a - b) % 360); return min(d, 360 - d)

def _na_faixa(a, f):
    i, j = f; return (i <= a <= j) if i <= j else (a >= i or a <= j)

NIVEL_MAX = {"iniciante": 1.2, "intermediario": 2.0, "avancado": 4.0}
ORDEM = {"iniciante": 0, "intermediario": 1, "avancado": 2}

def pontuar(praia, prev, nivel="iniciante"):
    h = prev.get("swell_wave_height") or prev.get("wave_height") or 0
    per = prev.get("swell_wave_period") or prev.get("wave_period") or 0
    dsw = prev.get("swell_wave_direction") or prev.get("wave_direction") or 0
    vv = prev.get("wind_speed_10m") or 0
    dv = prev.get("wind_direction_10m") or 0
    notas, motivos = {}, []

    if _na_faixa(dsw, praia["swell_ideal"]):
        notas["swell"] = 30.0; motivos.append(f"swell de {dsw:.0f}° entra bem aqui")
    else:
        i, j = praia["swell_ideal"]
        fora = min(_dif_ang(dsw, i), _dif_ang(dsw, j))
        notas["swell"] = max(0.0, 30.0 - fora*0.5)
        motivos.append(f"swell de {dsw:.0f}° está {fora:.0f}° fora da faixa ideal")

    terral = (praia["orientacao"] + 180) % 360
    desvio = _dif_ang(dv, terral)
    if vv < 5:
        notas["vento"] = 30.0; motivos.append("vento calmo, mar liso")
    elif desvio < 60:
        notas["vento"] = 30.0 - (vv/40)*5; motivos.append(f"terral de {vv:.0f} km/h, alisa a onda")
    elif desvio > 120:
        notas["vento"] = max(0.0, 18.0 - vv*0.7); motivos.append(f"maral de {vv:.0f} km/h, mar mexido")
    else:
        notas["vento"] = max(0.0, 20.0 - vv*0.4); motivos.append(f"vento cruzado de {vv:.0f} km/h")

    teto = NIVEL_MAX.get(nivel, 1.2)
    if h < 0.3:
        notas["tamanho"] = 5.0; motivos.append(f"mar muito pequeno ({h:.1f} m)")
    elif h <= teto:
        notas["tamanho"] = 25.0; motivos.append(f"{h:.1f} m, dentro do seu nível")
    else:
        notas["tamanho"] = max(0.0, 25.0-(h-teto)*25)
        motivos.append(f"{h:.1f} m, acima do recomendado para {nivel}")

    if per >= 12: notas["periodo"] = 15.0; motivos.append(f"período de {per:.0f} s, onda formada")
    elif per >= 9: notas["periodo"] = 11.0; motivos.append(f"período de {per:.0f} s, razoável")
    elif per >= 6: notas["periodo"] = 6.0; motivos.append(f"período de {per:.0f} s, mar curto")
    else: notas["periodo"] = 2.0; motivos.append(f"período de {per:.0f} s, mar picado")

    total = sum(notas.values()); alerta = None
    if ORDEM[praia["nivel_min"]] > ORDEM.get(nivel, 0):
        total *= 0.4
        alerta = f"indicada para nível {praia['nivel_min']} ou acima"
    return {"praia": praia["nome"], "nota": round(total, 1), "motivos": motivos,
            "alerta": alerta, "altura": h, "periodo": per, "dir_swell": dsw,
            "vento": vv, "dir_vento": dv, "orientacao": praia["orientacao"],
            "temp_agua": prev.get("sea_surface_temperature"),
            "temp_ar": prev.get("temperature_2m"), "quando": prev.get("_quando"),
            "fonte": prev.get("_fonte")}


# ----------------------------------------------------------------------------
# 4. A ROSA DOS VENTOS
# ----------------------------------------------------------------------------
def rosa_dos_ventos(orientacao, dir_swell, dir_vento, tam=190):
    """Desenha em SVG a orientacao da praia, a direcao do swell e a do vento.

    E a informacao que de fato decide se a praia funciona, e que em numero isolado
    nao comunica: tres angulos em um circulo tornam visivel o alinhamento.
    """
    c = tam / 2
    r_ext, r_praia, r_swell, r_vento = tam*0.42, tam*0.30, tam*0.37, tam*0.33

    def ponto(ang, raio):
        rad = math.radians(ang - 90)
        return c + raio*math.cos(rad), c + raio*math.sin(rad)

    # setor de onde a praia "olha" (face da praia, +-45 graus)
    a1, a2 = orientacao - 45, orientacao + 45
    x1, y1 = ponto(a1, r_praia); x2, y2 = ponto(a2, r_praia)
    setor = (f'<path d="M {c} {c} L {x1:.1f} {y1:.1f} '
             f'A {r_praia:.1f} {r_praia:.1f} 0 0 1 {x2:.1f} {y2:.1f} Z" '
             f'fill="{CORES["azul_claro"]}" opacity=".55"/>')

    # seta do swell: aponta PARA o centro (de onde a ondulacao vem)
    xs, ys = ponto(dir_swell, r_swell)
    xsi, ysi = ponto(dir_swell, r_praia*0.52)
    seta_swell = (f'<line x1="{xs:.1f}" y1="{ys:.1f}" x2="{xsi:.1f}" y2="{ysi:.1f}" '
                  f'stroke="{CORES["azul_fundo"]}" stroke-width="4" stroke-linecap="round"/>'
                  f'<circle cx="{xs:.1f}" cy="{ys:.1f}" r="5" fill="{CORES["azul_fundo"]}"/>')

    # seta do vento
    xv, yv = ponto(dir_vento, r_vento)
    xvi, yvi = ponto(dir_vento, r_praia*0.52)
    seta_vento = (f'<line x1="{xv:.1f}" y1="{yv:.1f}" x2="{xvi:.1f}" y2="{yvi:.1f}" '
                  f'stroke="{CORES["amarelo"]}" stroke-width="3" stroke-linecap="round" '
                  f'stroke-dasharray="5 3"/>'
                  f'<circle cx="{xv:.1f}" cy="{yv:.1f}" r="4" fill="{CORES["amarelo"]}"/>')

    cardeais = "".join(
        f'<text x="{ponto(a, r_ext+11)[0]:.1f}" y="{ponto(a, r_ext+11)[1]+4:.1f}" '
        f'text-anchor="middle" font-size="11" font-family="DM Sans" '
        f'fill="{CORES["chumbo_sutil"]}">{n}</text>'
        for a, n in [(0,"N"),(90,"L"),(180,"S"),(270,"O")])

    return f"""<svg width="{tam}" height="{tam}" viewBox="0 0 {tam} {tam}">
  <circle cx="{c}" cy="{c}" r="{r_ext}" fill="{CORES['creme_claro']}"
          stroke="{CORES['azul_claro']}" stroke-width="1.5"/>
  {setor}
  <circle cx="{c}" cy="{c}" r="3" fill="{CORES['chumbo']}"/>
  {seta_swell}{seta_vento}{cardeais}
</svg>"""


# ----------------------------------------------------------------------------
# 5. O AGENTE
# ----------------------------------------------------------------------------
def ler_chave(nome):
    v = os.environ.get(nome)
    if not v:
        try: v = st.secrets.get(nome)
        except Exception: v = None
    return v.strip() if isinstance(v, str) else v

GROQ_API_KEY = ler_chave("GROQ_API_KEY")
OPENAI_API_KEY = ler_chave("OPENAI_API_KEY")

# Provedor: usa a OpenAI se houver chave, senao cai no Groq.
# Os dois falam o mesmo protocolo, entao o restante do codigo nao muda.
USAR_OPENAI = (OPENAI_API_KEY or "").startswith("sk-")
MODO_DEMO = not (USAR_OPENAI or (GROQ_API_KEY or "").startswith("gsk_"))

def _garantir_dependencias():
    """Instala as bibliotecas do agente se faltarem, usando o mesmo interpretador
    deste processo. Necessario porque o Streamlit roda como processo separado e
    pode nao enxergar instalacoes feitas em outro ambiente."""
    import importlib, subprocess, sys
    pacotes = {"langchain": "langchain", "langchain_openai": "langchain-openai",
               "langgraph": "langgraph"}
    faltando = [p for m, p in pacotes.items()
                if not _tem_modulo(m)]
    if faltando:
        with st.spinner("Instalando " + ", ".join(faltando) + "..."):
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", *faltando],
                           check=True)
        importlib.invalidate_caches()
    return faltando


def _tem_modulo(nome):
    import importlib
    try:
        importlib.import_module(nome); return True
    except ImportError:
        return False


@st.cache_resource(show_spinner="Preparando o agente...")
def montar_agente(_chave_groq, _chave_openai):
    _garantir_dependencias()
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import tool
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import MemorySaver

    if _chave_openai and _chave_openai.startswith("sk-"):
        modelo = "gpt-4o-mini"
        llm = ChatOpenAI(model=modelo, api_key=_chave_openai,
                         temperature=0.2, timeout=60, max_retries=2)
    else:
        modelos = requests.get("https://api.groq.com/openai/v1/models",
                               headers={"Authorization": f"Bearer {_chave_groq}"}, timeout=20)
        ids = [m["id"] for m in modelos.json().get("data", [])]
        modelo = next((m for m in ["openai/gpt-oss-20b", "openai/gpt-oss-120b",
                                   "qwen/qwen3.6-27b"] if m in ids), ids[0])
        llm = ChatOpenAI(model=modelo, base_url="https://api.groq.com/openai/v1",
                         api_key=_chave_groq, temperature=0.2, timeout=60, max_retries=2)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.executescript("""
      CREATE TABLE praias(nome TEXT PRIMARY KEY, regiao TEXT, orientacao INTEGER,
        fundo TEXT, nivel_min TEXT, mare_ideal TEXT, observacao TEXT);
      CREATE TABLE servicos(id INTEGER PRIMARY KEY, praia TEXT, tipo TEXT, nome TEXT,
        preco_brl REAL, horario TEXT, observacao TEXT);
      CREATE TABLE acessos(praia TEXT PRIMARY KEY, estacionamento TEXT,
        transporte_publico TEXT, minutos_da_tijuca INTEGER);""")
    for p in PRAIAS:
        cur.execute("INSERT INTO praias VALUES (?,?,?,?,?,?,?)",
                    (p["nome"], p["regiao"], p["orientacao"], p["fundo"],
                     p["nivel_min"], p["mare_ideal"], p["obs"]))
    cur.executemany("INSERT INTO servicos (praia,tipo,nome,preco_brl,horario,observacao) "
                    "VALUES (?,?,?,?,?,?)", SERVICOS)
    cur.executemany("INSERT INTO acessos VALUES (?,?,?,?)", ACESSOS)
    conn.commit()

    def _achar(nome):
        n = (nome or "").lower()
        for p in PRAIAS:
            if p["nome"].lower() == n or p["nome"].lower() in n or n in p["nome"].lower():
                return p
        if "barra" in n: return next(p for p in PRAIAS if p["nome"] == "Barra da Tijuca")
        if "itacoa" in n: return next(p for p in PRAIAS if p["nome"] == "Itacoatiara")
        return None

    def _off(dia):
        d = (dia or "hoje").lower()
        if d in ("hoje","agora"): return 0
        if "amanh" in d: return 1
        sem = {"segunda":0,"terca":1,"terça":1,"quarta":2,"quinta":3,
               "sexta":4,"sabado":5,"sábado":5,"domingo":6}
        for k, i in sem.items():
            if k in d:
                delta = (i - date.today().weekday()) % 7
                return delta or 7
        return 0

    def _hora(p):
        return {"manha":8,"manhã":8,"tarde":15,"noite":19}.get((p or "manha").lower(), 8)

    @tool
    def consultar_condicao_praia(praia: str, dia: str = "hoje", periodo: str = "manha") -> str:
        """Consulta a condicao do mar em UMA praia do Rio. Retorna altura, periodo,
        direcao do swell, vento e temperaturas.

        Args:
            praia: Arpoador, Leblon, Barra da Tijuca, Recreio, Macumba, Prainha,
                   Grumari ou Itacoatiara.
            dia: hoje, amanha ou dia da semana.
            periodo: manha, tarde ou noite.
        """
        p = _achar(praia)
        if not p: return f"Praia nao encontrada. Disponiveis: {', '.join(NOMES_PRAIAS)}"
        prev = buscar_previsao(p["lat"], p["lon"], _off(dia), _hora(periodo), MODO_DEMO)
        r = pontuar(p, prev, st.session_state.get("nivel", "iniciante"))
        st.session_state["ultimo_ranking"] = [r]
        return json.dumps(r, ensure_ascii=False, default=str)

    @tool
    def comparar_praias(dia: str = "hoje", periodo: str = "manha",
                        nivel: str = "iniciante", regiao: str = "") -> str:
        """Compara TODAS as praias e devolve ranking de onde surfar. Use quando
        perguntarem onde surfar, sem nomear praia.

        Args:
            dia: hoje, amanha ou dia da semana.
            periodo: manha, tarde ou noite.
            nivel: iniciante, intermediario ou avancado.
            regiao: opcional, Zona Sul, Zona Oeste ou Niteroi.
        """
        cands = [p for p in PRAIAS if not regiao or p["regiao"].lower() == regiao.lower()]
        res = [pontuar(p, buscar_previsao(p["lat"], p["lon"], _off(dia), _hora(periodo),
                                          MODO_DEMO), nivel) for p in cands]
        res.sort(key=lambda x: -x["nota"])
        st.session_state["ultimo_ranking"] = res
        return json.dumps({"ranking": res[:5]}, ensure_ascii=False, default=str)

    @tool
    def consultar_banco_surf(pergunta: str) -> str:
        """Consulta o banco com servicos (aluguel de prancha, escola, comida, precos,
        horarios) e acessos (estacionamento, transporte, minutos da Tijuca).

        Args:
            pergunta: a pergunta em linguagem natural.
        """
        esquema = ("praias(nome,regiao,orientacao,fundo,nivel_min,mare_ideal,observacao) | "
                   "servicos(id,praia,tipo,nome,preco_brl,horario,observacao) "
                   "tipo em aluguel_prancha/escola/comida | "
                   "acessos(praia,estacionamento,transporte_publico,minutos_da_tijuca)")
        sql = llm.invoke(
            f"Traduza para SQL do SQLite. Apenas SELECT, LIMIT 10, sem explicacao "
            f"e sem marcacao de codigo.\nESQUEMA: {esquema}\nPERGUNTA: {pergunta}"
        ).content.strip()
        sql = re.sub(r"^```(?:sql)?|```$", "", sql, flags=re.MULTILINE).strip()
        if not sql.lower().startswith("select") or any(
                k in sql.lower() for k in ("insert","update","delete","drop","alter")):
            return "Consulta bloqueada: apenas leitura."
        try:
            c = conn.cursor(); linhas = c.execute(sql).fetchall()
            cols = [d[0] for d in c.description]
        except Exception as e:
            return f"Consulta falhou: {e}"
        return json.dumps({"sql": sql,
                           "resultados": [dict(zip(cols, l)) for l in linhas]},
                          ensure_ascii=False)

    @tool
    def calcular_prancha(peso_kg: float, altura_cm: float, nivel: str = "iniciante",
                         idade: int = 30, condicionamento: str = "medio") -> str:
        """Calcula volume em litros e comprimento de prancha. Funcao deterministica.

        Args:
            peso_kg: peso em quilos.
            altura_cm: altura em centimetros.
            nivel: iniciante, intermediario ou avancado.
            idade: idade em anos.
            condicionamento: baixo, medio ou alto.
        """
        COEF = {"iniciante": (0.90, 1.20), "intermediario": (0.60, 0.80),
                "avancado": (0.40, 0.55)}
        nivel = (nivel or "iniciante").lower()
        if nivel not in COEF: return "Nivel invalido."
        cmin, cmax = COEF[nivel]; aj = 0.0
        if idade >= 45: aj += 0.05
        if (condicionamento or "").lower() == "baixo": aj += 0.05
        elif (condicionamento or "").lower() == "alto": aj -= 0.03
        acr = {"iniciante": (30, 50), "intermediario": (5, 25), "avancado": (-15, 5)}[nivel]
        def pes(cm):
            pol = cm/2.54; return f"{int(pol//12)}'{int(round(pol%12))}\""
        return json.dumps({
            "volume_litros": {"minimo": round(peso_kg*(cmin+aj),1),
                              "maximo": round(peso_kg*(cmax+aj),1)},
            "comprimento": {"minimo": pes(altura_cm+acr[0]), "maximo": pes(altura_cm+acr[1])},
            "tipo": "softboard ou funboard" if nivel=="iniciante" else
                    "funboard" if nivel=="intermediario" else "shortboard"},
            ensure_ascii=False)

    @tool
    def converter_unidade(valor: float, de: str, para: str) -> str:
        """Converte unidades de surf: m, pe, kmh, no, c, f.

        Args:
            valor: numero a converter.
            de: unidade de origem.
            para: unidade de destino.
        """
        t = {("m","pe"): 3.28084, ("pe","m"): 1/3.28084,
             ("kmh","no"): 1/1.852, ("no","kmh"): 1.852}
        k = (de.lower(), para.lower())
        if k in t: return f"{valor} {de} = {valor*t[k]:.2f} {para}"
        if k == ("c","f"): return f"{valor} C = {valor*9/5+32:.1f} F"
        if k == ("f","c"): return f"{valor} F = {(valor-32)*5/9:.1f} C"
        return "Conversao nao suportada."

    PROMPT = f"""## PERSONA
Voce e o Mare Boa, assistente de surf do Rio de Janeiro. Fala como surfista local:
direto, honesto quando a condicao esta ruim. Nunca minimiza risco para agradar.

## TAREFA
Ajudar a decidir onde e quando surfar. SEMPRE consulte as ferramentas para qualquer
afirmacao sobre condicao do mar. Nunca invente numero de previsao.

## CONTEXTO
Praias: {", ".join(NOMES_PRAIAS)}
- Vento terral (da terra para o mar) alisa a onda. Maral deixa o mar mexido.
- Periodo acima de 12 s e onda formada. Abaixo de 8 s e mar picado.
- O swell precisa estar alinhado com a orientacao da praia para entrar.
- Para iniciante, acima de 1,2 m ja e desafiador. Prainha e Itacoatiara nao sao
  indicadas para iniciantes em nenhuma condicao.
- Vento abaixo de 5 km/h e calmo, de 5 a 20 e moderado, acima de 20 e forte.
  Nunca chame vento acima de 20 km/h de calmo.

## REGRA DE ESCOPO
Responda APENAS sobre surf, praias e mar no Rio. Para qualquer outro assunto, diga
que nao e a sua area e ofereca ajuda sobre surf. Nao responda perguntas gerais de
conhecimento, mesmo que saiba a resposta.

## FORMATO
Resposta direta em uma frase, depois os numeros que a sustentam, depois alerta de
seguranca se houver. Ate 6 linhas. Portugues do Brasil. Nunca exiba JSON."""

    ferramentas = [consultar_condicao_praia, comparar_praias, consultar_banco_surf,
                   calcular_prancha, converter_unidade]
    agente = create_agent(llm, tools=ferramentas, system_prompt=PROMPT,
                          checkpointer=MemorySaver())
    return agente, modelo, [f.name for f in ferramentas]


# ----------------------------------------------------------------------------
# 6. BARRA LATERAL
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Seu perfil")
    nivel = st.select_slider("Nível", ["iniciante", "intermediario", "avancado"],
                             value="iniciante")
    st.session_state["nivel"] = nivel
    col1, col2 = st.columns(2)
    peso = col1.number_input("Peso (kg)", 30, 200, 62)
    altura = col2.number_input("Altura (cm)", 120, 230, 168)

    st.markdown("---")
    st.markdown("### Condições agora")
    dia = st.selectbox("Dia", ["hoje", "amanha", "sabado", "domingo"])
    periodo = st.selectbox("Período", ["manha", "tarde"])
    buscar = st.button("Atualizar ranking", use_container_width=True)

    st.markdown("---")
    estado = "simulado" if MODO_DEMO else "ao vivo"
    st.markdown(f'<p class="legenda">Previsão: Open-Meteo ({estado})<br>'
                f'Dados do mar atualizados a cada 30 min.</p>', unsafe_allow_html=True)
    if MODO_DEMO:
        st.warning("Sem GROQ_API_KEY: o chat fica indisponível e a previsão é simulada. "
                   "O ranking e a rosa dos ventos continuam demonstráveis.", icon="⚠️")


# ----------------------------------------------------------------------------
# 7. CORPO: RANKING E CHAT
# ----------------------------------------------------------------------------
esq, dir_ = st.columns([1.05, 1], gap="large")

with esq:
    st.markdown("### Onde surfar")
    st.markdown('<p class="legenda">A <b>nota de 0 a 100</b> cruza quatro fatores: '
                'alinhamento do swell com a orientação da praia (30), qualidade do vento (30), '
                'tamanho adequado ao seu nível (25) e período do swell (15). '
                'Praia acima do seu nível tem a nota reduzida por segurança.</p>',
                unsafe_allow_html=True)
    if buscar or "ranking" not in st.session_state:
        off = {"hoje":0, "amanha":1}.get(dia)
        if off is None:
            sem = {"sabado":5, "domingo":6}[dia]
            off = (sem - date.today().weekday()) % 7 or 7
        hora = 8 if periodo == "manha" else 15
        with st.spinner("Consultando o mar..."):
            st.session_state["ranking"] = sorted(
                [pontuar(p, buscar_previsao(p["lat"], p["lon"], off, hora, MODO_DEMO), nivel)
                 for p in PRAIAS], key=lambda r: -r["nota"])

    for i, r in enumerate(st.session_state.get("ranking", [])[:5]):
        classe = "card topo" if i == 0 else "card"
        pilulas = (f'<span class="pilula">{r["altura"]:.1f} m</span>'
                   f'<span class="pilula">{r["periodo"]:.0f} s</span>'
                   f'<span class="pilula">swell {r["dir_swell"]:.0f}°</span>'
                   f'<span class="pilula">vento {r["vento"]:.0f} km/h</span>')
        if r.get("temp_agua"):
            pilulas += f'<span class="pilula">água {r["temp_agua"]:.0f}°C</span>'
        if r["alerta"]:
            pilulas += f'<span class="pilula alerta">{r["alerta"]}</span>'
        elif i == 0:
            pilulas += '<span class="pilula bom">melhor opção</span>'
        html = (f'<div class="{classe}">'
                f'<div class="card-cabeca">'
                f'<span class="card-nome">{r["praia"]}</span>'
                f'<span class="card-nota"><b>{r["nota"]:.0f}</b><small>nota</small></span>'
                f'</div>'
                f'<div class="card-dados">{pilulas}</div>'
                f'<div class="card-motivos">{" · ".join(r["motivos"][:3])}</div>'
                f'</div>')
        st.markdown(html, unsafe_allow_html=True)

    if st.session_state.get("ranking"):
        topo = st.session_state["ranking"][0]
        st.markdown("### Alinhamento em " + topo["praia"])
        c1, c2 = st.columns([1, 1.15])
        with c1:
            st.markdown(rosa_dos_ventos(topo["orientacao"], topo["dir_swell"],
                                        topo["dir_vento"]), unsafe_allow_html=True)
        with c2:
            st.markdown(
                '<div style="padding-top:.5rem">'
                '<p class="legenda">'
                f'<span style="display:inline-block;width:12px;height:12px;border-radius:3px;'
                f'background:{CORES["azul_claro"]};margin-right:7px"></span>'
                f'para onde a praia olha ({topo["orientacao"]}°)<br>'
                f'<span style="display:inline-block;width:12px;height:3px;'
                f'background:{CORES["azul_fundo"]};margin-right:7px;vertical-align:middle"></span>'
                f'de onde vem o swell ({topo["dir_swell"]:.0f}°)<br>'
                f'<span style="display:inline-block;width:12px;height:3px;'
                f'background:{CORES["amarelo"]};margin-right:7px;vertical-align:middle"></span>'
                f'de onde vem o vento ({topo["dir_vento"]:.0f}°)'
                '</p>'
                '<p class="legenda">Quando a seta azul escura cai dentro do setor claro, '
                'o swell entra na praia. Vento vindo do lado oposto ao setor é terral, '
                'e alisa a onda.</p></div>', unsafe_allow_html=True)

with dir_:
    st.markdown("### Converse com o agente")
    if MODO_DEMO:
        st.info("Configure GROQ_API_KEY ou OPENAI_API_KEY para ativar o chat.", icon="🔑")
    else:
        try:
            agente, modelo, nomes_ferr = montar_agente(GROQ_API_KEY, OPENAI_API_KEY)
            st.markdown(f'<p class="legenda">Modelo: {modelo} · '
                        f'{len(nomes_ferr)} ferramentas</p>', unsafe_allow_html=True)

            if "mensagens" not in st.session_state:
                st.session_state.mensagens = [{
                    "role": "assistant",
                    "content": "Oi! Posso ver a condição de qualquer praia do Rio, comparar "
                               "onde está melhor para o seu nível, calcular que prancha "
                               "alugar e achar onde comer depois. O que você quer saber?"}]

            for m in st.session_state.mensagens:
                with st.chat_message(m["role"], avatar="🌊" if m["role"]=="assistant" else "🏄‍♀️"):
                    st.markdown(m["content"])
                    for p in m.get("passos", []):
                        st.caption(f"usou: {p}")

            if entrada := st.chat_input("ex: onde eu surfo amanhã de manhã?"):
                st.session_state.mensagens.append({"role": "user", "content": entrada})
                with st.chat_message("user", avatar="🏄‍♀️"):
                    st.markdown(entrada)
                with st.chat_message("assistant", avatar="🌊"):
                    with st.spinner("consultando..."):
                        try:
                            res = agente.invoke(
                                {"messages": [("user", entrada)]},
                                config={"configurable": {"thread_id": "streamlit"}})
                            msgs = res["messages"]
                            corte = max((i for i, m in enumerate(msgs)
                                        if m.__class__.__name__ == "HumanMessage"), default=0)
                            passos = [f'{tc["name"]}({tc["args"]})' for m in msgs[corte:]
                                      for tc in (getattr(m, "tool_calls", None) or [])]
                            resposta = msgs[-1].content
                        except Exception as e:
                            resposta = f"Não consegui responder agora: {type(e).__name__}"
                            passos = []
                    st.markdown(resposta)
                    for p in passos:
                        st.caption(f"usou: {p}")
                st.session_state.mensagens.append(
                    {"role": "assistant", "content": resposta, "passos": passos})
                st.rerun()
        except ModuleNotFoundError as e:
            st.error(f"Falta instalar uma biblioteca: {e.name}", icon="📦")
            st.code("!pip install -q langchain langchain-openai langgraph", language="bash")
            st.caption("Rode isso no notebook, reinicie o Streamlit e recarregue a página.")
        except Exception as e:
            st.error(f"Não consegui iniciar o agente: {type(e).__name__}: {e}")

st.markdown("---")
st.markdown('<p class="legenda">Maré Boa · Agentes Cognitivos com LangChain · '
            'Instituto Infnet · Maria Glatthardt Grisolia · 2026<br>'
            'Previsão: Open-Meteo. A decisão de entrar no mar é sempre sua.</p>',
            unsafe_allow_html=True)
