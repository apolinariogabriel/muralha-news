"""
Monitor de Notícias - Polícia Preditiva / Muralha Paulista
Busca notícias em feeds RSS dos principais veículos brasileiros
e envia um compilado por e-mail.
"""

import feedparser
import smtplib
import os
import requests
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# Cabeçalho para os sites não bloquearem nossa leitura
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

# ─────────────────────────────────────────────
# CONFIGURAÇÕES — preencha com seus dados
# (ou use variáveis de ambiente no GitHub Actions)
# ─────────────────────────────────────────────

EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE", "SEU_EMAIL@gmail.com")
SENHA_APP       = os.environ.get("SENHA_APP",       "SUA_SENHA_DE_APP")
EMAIL_DESTINO   = os.environ.get("EMAIL_DESTINO",   "limacase9@gmail.com")

# ─────────────────────────────────────────────
# PALAVRAS-CHAVE para filtrar notícias
# ─────────────────────────────────────────────

PALAVRAS_CHAVE = [
    # Termos principais
    "polícia preditiva",
    "policia preditiva",
    "policiamento preditivo",
    "muralha paulista",
    # Smart Sampa — várias grafias possíveis (tudo junto, com espaço, etc.)
    "smart sampa",
    "smartsampa",
    "smart-sampa",
    # Termos relacionados (ampliam a cobertura)
    "vigilância preditiva",
    "reconhecimento facial",
    "câmeras inteligentes",
    "monitoramento preditivo",
    "tecnologia policial",
    "videomonitoramento",
]

# ─────────────────────────────────────────────
# QUANTOS DIAS PARA TRÁS buscar (filtro de data)
# Ex: 7 = só notícias dos últimos 7 dias.
# Use 0 para NÃO filtrar por data (pega tudo que estiver no feed).
# ─────────────────────────────────────────────
DIAS_PARA_TRAS = 7

# Ler o texto completo de cada matéria (mais lento, mas pega muito mais)?
# True  = abre cada notícia e lê o corpo inteiro
# False = busca só no título e no resumo do RSS (rápido)
LER_TEXTO_COMPLETO = True

# ─────────────────────────────────────────────
# FEEDS RSS dos principais veículos brasileiros
# ─────────────────────────────────────────────

FEEDS = {
    # ── Grandes veículos nacionais ──────────────────────────────
    "G1 / Globo":             "https://g1.globo.com/rss/g1/",
    "G1 - São Paulo":         "https://g1.globo.com/rss/g1/sao-paulo/",
    "O Globo":                "https://oglobo.globo.com/rss/oglobo/",
    "O Globo - Brasil":       "https://oglobo.globo.com/rss/oglobo/brasil/",
    "UOL Notícias":           "https://rss.uol.com.br/feed/noticias.xml",
    "Folha de S.Paulo":       "https://feeds.folha.uol.com.br/folha/br/rss091.xml",
    "Folha - Cotidiano":      "https://feeds.folha.uol.com.br/cotidiano/rss091.xml",
    "Estadão":                "https://feeds.estadao.com.br/rss20/estadao-conteudo.xml",
    "Valor Econômico":        "https://valor.globo.com/rss/valor/",
    "R7":                     "https://noticias.r7.com/feed.xml",
    "CNN Brasil":             "https://www.cnnbrasil.com.br/feed/",
    "BBC News Brasil":        "https://feeds.bbci.co.uk/portuguese/rss.xml",
    "Veja":                   "https://veja.abril.com.br/feed/",
    "Metrópoles":             "https://www.metropoles.com/feed",
    "Correio Braziliense":    "https://www.correiobraziliense.com.br/rss_feed.xml",
    "Agência Brasil":         "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",

    # ── Análise e política ──────────────────────────────────────
    "Poder360":               "https://www.poder360.com.br/feed/",
    "Nexo Jornal":            "https://www.nexojornal.com.br/rss.xml",
    "Carta Capital":          "https://www.cartacapital.com.br/feed/",
    "Piauí":                  "https://piaui.folha.uol.com.br/feed/",

    # ── Investigativo / direitos humanos / segurança ────────────
    "Agência Pública":        "https://apublica.org/feed/",
    "The Intercept Brasil":   "https://theintercept.com/brasil/feed/?lang=pt",
    "Brasil de Fato":         "https://www.brasildefato.com.br/rss.xml",
    "Ponte Jornalismo":       "https://ponte.org/feed/",
    "Marco Zero":             "https://marcozero.org/feed/",

    # ── Jurídico / regulação / tecnologia ───────────────────────
    "JOTA":                   "https://www.jota.info/feed",
    "Migalhas":               "https://www.migalhas.com.br/rss",
    "TecMundo":               "https://rss.tecmundo.com.br/feed",
    "Tilt (UOL)":             "https://rss.uol.com.br/feed/tilt.xml",

    # ── Universitário / regional ────────────────────────────────
    "Jornal da USP":          "https://jornal.usp.br/feed/",
    "Marília Notícia":        "https://www.marilianoticia.com.br/feed/",
}

# ─────────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────────

def texto_contem_palavra_chave(texto: str) -> str | None:
    """Retorna a primeira palavra-chave encontrada no texto, ou None se nenhuma bater."""
    texto_lower = texto.lower()
    for palavra in PALAVRAS_CHAVE:
        if palavra.lower() in texto_lower:
            return palavra
    return None


def ler_texto_completo(link: str) -> str:
    """Abre a página da notícia e devolve o texto do corpo (limpo de HTML)."""
    try:
        resp = requests.get(link, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        sopa = BeautifulSoup(resp.content, "html.parser")

        # Remove trechos que não são conteúdo (scripts, menus, rodapés)
        for tag in sopa(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Prioriza o texto dentro de <article>, se existir
        artigo = sopa.find("article")
        alvo = artigo if artigo else sopa

        return alvo.get_text(separator=" ", strip=True)
    except Exception:
        # Se não conseguir abrir a matéria, devolve vazio (usa só o resumo)
        return ""


def dentro_do_periodo(data) -> bool:
    """Verifica se a data está dentro da janela de DIAS_PARA_TRAS. Sem data = inclui."""
    if DIAS_PARA_TRAS <= 0 or data is None:
        return True
    limite = datetime.now(timezone.utc) - timedelta(days=DIAS_PARA_TRAS)
    # Normaliza para comparação com fuso
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    return data >= limite


def buscar_noticias() -> tuple[list[dict], list[str]]:
    """Percorre todos os feeds e retorna (notícias encontradas, feeds com problema)."""
    resultados = []
    feeds_com_problema = []
    links_vistos = set()  # evita a mesma notícia duas vezes

    for veiculo, url in FEEDS.items():
        print(f"🔍 Buscando em: {veiculo}...")
        try:
            feed = feedparser.parse(url)

            if not feed.entries:
                print(f"  ⚠️  Nenhuma entrada em {veiculo} (feed pode estar fora do ar)")
                feeds_com_problema.append(veiculo)
                continue

            for entry in feed.entries:
                titulo   = entry.get("title", "")
                resumo   = entry.get("summary", "")
                link     = entry.get("link", "")
                data_raw = entry.get("published", entry.get("updated", ""))

                # Evita duplicatas
                if link in links_vistos:
                    continue

                # Converte a data
                try:
                    data = dateparser.parse(data_raw)
                    data_str = data.strftime("%d/%m/%Y %H:%M") if data else "Data desconhecida"
                except Exception:
                    data = None
                    data_str = data_raw or "Data desconhecida"

                # Filtro de data: pula se for antiga demais
                if not dentro_do_periodo(data):
                    continue

                # 1º) tenta achar no título ou resumo (rápido)
                achou = texto_contem_palavra_chave(titulo) or texto_contem_palavra_chave(resumo)

                # 2º) se não achou e a opção está ligada, lê o texto completo da matéria
                if not achou and LER_TEXTO_COMPLETO and link:
                    corpo = ler_texto_completo(link)
                    if corpo:
                        achou = texto_contem_palavra_chave(corpo)

                if achou:
                    links_vistos.add(link)
                    resultados.append({
                        "veiculo":  veiculo,
                        "titulo":   titulo,
                        "resumo":   (resumo[:300] + "...") if len(resumo) > 300 else resumo,
                        "link":     link,
                        "data":     data_str,
                        "termo":    achou,  # qual palavra-chave bateu
                    })
                    print(f"  ✅ Encontrada: {titulo[:70]}... (termo: {achou})")

        except Exception as e:
            print(f"  ⚠️  Erro ao acessar {veiculo}: {e}")
            feeds_com_problema.append(veiculo)

    resultados.sort(key=lambda x: x["veiculo"])
    return resultados, feeds_com_problema


def montar_email_html(noticias: list[dict]) -> str:
    """Monta o corpo do e-mail em HTML formatado."""
    hoje = datetime.now().strftime("%d/%m/%Y")

    if not noticias:
        corpo = """
        <p>Nenhuma notícia encontrada com os termos monitorados nesta varredura.</p>
        <p>Os termos buscados foram:</p>
        <ul>
        """ + "".join(f"<li>{p}</li>" for p in PALAVRAS_CHAVE) + "</ul>"
    else:
        itens = ""
        for n in noticias:
            termo = n.get("termo", "")
            itens += f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:16px; margin-bottom:16px; background:#fff;">
              <p style="color:#888; font-size:12px; margin:0 0 4px 0;">
                📰 <strong>{n['veiculo']}</strong> &nbsp;·&nbsp; 🗓️ {n['data']}
                &nbsp;·&nbsp; 🔑 <span style="color:#c0392b;">{termo}</span>
              </p>
              <h3 style="margin:4px 0 8px 0;">
                <a href="{n['link']}" style="color:#1a0dab; text-decoration:none;">{n['titulo']}</a>
              </h3>
              <p style="color:#444; font-size:14px; margin:0 0 8px 0;">{n['resumo']}</p>
              <a href="{n['link']}" style="font-size:13px; color:#1a73e8;">🔗 Ler notícia completa</a>
            </div>
            """

        periodo = f"nos últimos {DIAS_PARA_TRAS} dias" if DIAS_PARA_TRAS > 0 else "(sem filtro de data)"
        corpo = f"<p>Foram encontradas <strong>{len(noticias)} notícia(s)</strong> com os termos monitorados {periodo}:</p>" + itens

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; background:#f5f5f5; padding:24px;">
      <div style="max-width:700px; margin:auto; background:#f9f9f9; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.1);">

        <!-- Cabeçalho -->
        <div style="background:#1a1a2e; color:white; padding:24px;">
          <h1 style="margin:0; font-size:22px;">🔎 Monitor de Notícias</h1>
          <p style="margin:4px 0 0 0; opacity:0.8; font-size:14px;">
            Polícia Preditiva · Muralha Paulista &nbsp;|&nbsp; {hoje}
          </p>
        </div>

        <!-- Corpo -->
        <div style="padding:24px;">
          {corpo}
        </div>

        <!-- Rodapé -->
        <div style="background:#eee; padding:16px; font-size:12px; color:#888; text-align:center;">
          Este e-mail foi gerado automaticamente pelo seu monitor de notícias.<br>
          Termos monitorados: {" · ".join(PALAVRAS_CHAVE)}
        </div>

      </div>
    </body>
    </html>
    """
    return html


def enviar_email(html: str, total: int):
    """Envia o e-mail com o compilado de notícias."""
    hoje = datetime.now().strftime("%d/%m/%Y")
    assunto = f"[Monitor] {total} notícia(s) encontrada(s) — {hoje}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINO

    msg.attach(MIMEText(html, "html", "utf-8"))

    print(f"\n📧 Enviando e-mail para {EMAIL_DESTINO}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_bytes())

    print("✅ E-mail enviado com sucesso!")


# ─────────────────────────────────────────────
# EXECUÇÃO PRINCIPAL
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  MONITOR DE NOTÍCIAS — iniciando varredura")
    print("=" * 50)

    noticias, feeds_com_problema = buscar_noticias()

    print(f"\n📋 Total encontrado: {len(noticias)} notícia(s)")
    print(f"📡 Total de fontes: {len(FEEDS)}")
    if feeds_com_problema:
        print(f"⚠️  Fontes que não responderam ({len(feeds_com_problema)}): {', '.join(feeds_com_problema)}")
    print()

    html = montar_email_html(noticias)
    enviar_email(html, len(noticias))

    print("\n✅ Concluído!")
