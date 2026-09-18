"""
Monitor de Notícias - Polícia Preditiva / Muralha Paulista / Smart Sampa
=========================================================================
Estratégia: usa o RSS de busca do GOOGLE NOTÍCIAS, que já cobre TODOS os
veículos brasileiros de uma vez (Folha, Estadão, G1, UOL, etc.) e já filtra
por palavra-chave e por data na origem. É a mesma tecnologia por trás do
Google Alertas — estável, rápido e sem paywall no feed.

Depois envia um compilado por e-mail.
"""

import feedparser
import smtplib
import os
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURAÇÕES — preencha com seus dados
# (ou use variáveis de ambiente / Secrets no GitHub)
# ─────────────────────────────────────────────

EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE", "SEU_EMAIL@gmail.com")
SENHA_APP       = os.environ.get("SENHA_APP",       "SUA_SENHA_DE_APP")
EMAIL_DESTINO   = os.environ.get("EMAIL_DESTINO",   "limacase9@gmail.com")

# ─────────────────────────────────────────────
# TERMOS DE BUSCA
# Cada item é buscado no Google Notícias. Use aspas para expressões exatas.
# ─────────────────────────────────────────────

TERMOS_BUSCA = [
    # Termos fortes: quase nunca dão ruído
    '"muralha paulista"',
    '"smart sampa"',
    '"smartsampa"',
    '"polícia preditiva"',
    '"policiamento preditivo"',
    '"vigilância preditiva"',
    '"monitoramento preditivo"',
    # Termos amplos: restringidos ao contexto de SP/polícia/segurança
    '"reconhecimento facial" (São Paulo OR polícia OR segurança pública OR prefeitura)',
    '"câmeras inteligentes" (São Paulo OR polícia OR segurança pública OR prefeitura)',
]

# ─────────────────────────────────────────────
# PALAVRAS PARA EXCLUIR (reduz ruído)
# Notícias que contiverem esses contextos são descartadas da busca.
# Ex: futebol/estádio, shows, etc. — onde "reconhecimento facial" aparece
# mas não tem relação com vigilância urbana / polícia preditiva.
# ─────────────────────────────────────────────
EXCLUIR = [
    "estádio", "estadio", "torcedor", "torcida", "MorumBIS", "Morumbi",
    "Allianz", "Maracanã", "ingresso", "show", "festival", "aeroporto",
    "embarque", "Copa", "Libertadores", "Brasileirão", "jogo",
]

# ─────────────────────────────────────────────
# QUANTOS DIAS PARA TRÁS buscar
# Ex: 7 = últimos 7 dias · 15 = últimos 15 dias · 30 = último mês
# Como o envio é semanal, 7 é o ideal: pega tudo da semana sem repetir.
# ─────────────────────────────────────────────
DIAS_PARA_TRAS = 7

# Idioma/região da busca (Brasil, português)
GNEWS_PARAMS = "hl=pt-BR&gl=BR&ceid=BR:pt-419"


# ─────────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────────

def montar_url_google_news(termo: str) -> str:
    """Monta a URL do RSS de busca do Google Notícias para um termo.

    O operador 'when:7d' faz o próprio Google já filtrar pelos últimos 7 dias.
    """
    query = termo
    if DIAS_PARA_TRAS > 0:
        query = f"{termo} when:{DIAS_PARA_TRAS}d"
    query_codificada = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={query_codificada}&{GNEWS_PARAMS}"


def extrair_veiculo(entry) -> str:
    """Tenta descobrir o nome do veículo (fonte) da notícia."""
    # O Google News costuma preencher entry.source.title
    fonte = getattr(entry, "source", None)
    if fonte and getattr(fonte, "title", None):
        return fonte.title
    # Alternativa: o título vem como "Notícia - Veículo"
    titulo = entry.get("title", "")
    if " - " in titulo:
        return titulo.rsplit(" - ", 1)[-1].strip()
    return "Fonte desconhecida"


def limpar_titulo(titulo: str, veiculo: str) -> str:
    """Remove o ' - Veículo' que o Google acrescenta no fim do título."""
    sufixo = f" - {veiculo}"
    if titulo.endswith(sufixo):
        return titulo[: -len(sufixo)].strip()
    return titulo


def buscar_noticias() -> tuple[list[dict], list[str]]:
    """Busca cada termo no Google Notícias e junta os resultados sem repetir."""
    resultados = []
    termos_com_problema = []
    links_vistos = set()
    titulos_vistos = set()

    for termo in TERMOS_BUSCA:
        url = montar_url_google_news(termo)
        print(f"🔍 Buscando: {termo}")
        try:
            feed = feedparser.parse(url)

            if not feed.entries:
                print("  · nenhum resultado")
                continue

            for entry in feed.entries:
                link  = entry.get("link", "")
                data_raw = entry.get("published", entry.get("updated", ""))

                # Data
                try:
                    data = dateparser.parse(data_raw)
                    data_str = data.strftime("%d/%m/%Y %H:%M") if data else "Data desconhecida"
                except Exception:
                    data = None
                    data_str = data_raw or "Data desconhecida"

                veiculo = extrair_veiculo(entry)
                titulo  = limpar_titulo(entry.get("title", ""), veiculo)
                resumo  = entry.get("summary", "")

                # Filtro de exclusão: descarta ruído (futebol, shows, aeroporto...)
                texto_para_checar = f"{titulo} {resumo}".lower()
                if any(palavra.lower() in texto_para_checar for palavra in EXCLUIR):
                    print(f"  🚫 Ignorada (ruído): {titulo[:55]}")
                    continue

                # Evita duplicatas (mesmo link OU mesmo título)
                chave_titulo = titulo.lower().strip()
                if link in links_vistos or chave_titulo in titulos_vistos:
                    continue
                links_vistos.add(link)
                titulos_vistos.add(chave_titulo)

                resultados.append({
                    "veiculo": veiculo,
                    "titulo":  titulo,
                    "resumo":  "",   # o resumo do Google é só HTML de link; omitimos
                    "link":    link,
                    "data":    data_str,
                    "data_obj": data,
                    "termo":   termo.replace('"', ''),
                })
                print(f"  ✅ {titulo[:65]}  [{veiculo}]")

        except Exception as e:
            print(f"  ⚠️  Erro ao buscar '{termo}': {e}")
            termos_com_problema.append(termo)

    # Ordena da mais recente para a mais antiga
    resultados.sort(
        key=lambda x: x["data_obj"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return resultados, termos_com_problema


def montar_email_html(noticias: list[dict]) -> str:
    """Monta o corpo do e-mail em HTML formatado."""
    hoje = datetime.now().strftime("%d/%m/%Y")
    periodo = f"nos últimos {DIAS_PARA_TRAS} dias" if DIAS_PARA_TRAS > 0 else "(sem filtro de data)"

    if not noticias:
        corpo = f"""
        <p>Nenhuma notícia encontrada com os termos monitorados {periodo}.</p>
        <p>Termos buscados:</p>
        <ul>
        """ + "".join(f"<li>{t.replace(chr(34), '')}</li>" for t in TERMOS_BUSCA) + "</ul>"
    else:
        itens = ""
        for n in noticias:
            itens += f"""
            <div style="border:1px solid #ddd; border-radius:8px; padding:16px; margin-bottom:16px; background:#fff;">
              <p style="color:#888; font-size:12px; margin:0 0 4px 0;">
                📰 <strong>{n['veiculo']}</strong> &nbsp;·&nbsp; 🗓️ {n['data']}
                &nbsp;·&nbsp; 🔑 <span style="color:#c0392b;">{n['termo']}</span>
              </p>
              <h3 style="margin:4px 0 8px 0;">
                <a href="{n['link']}" style="color:#1a0dab; text-decoration:none;">{n['titulo']}</a>
              </h3>
              <a href="{n['link']}" style="font-size:13px; color:#1a73e8;">🔗 Ler notícia completa</a>
            </div>
            """
        # Resumo de quantas notícias por veículo (ajuda a conferir a cobertura)
        contagem = {}
        for n in noticias:
            contagem[n["veiculo"]] = contagem.get(n["veiculo"], 0) + 1
        linhas_veiculos = "".join(
            f"<li>{v}: <strong>{qtd}</strong></li>"
            for v, qtd in sorted(contagem.items(), key=lambda x: x[1], reverse=True)
        )
        resumo_veiculos = f"""
        <details style="margin-bottom:16px;">
          <summary style="cursor:pointer; color:#555; font-size:14px;">
            📊 Cobertura: {len(contagem)} veículo(s) diferente(s) (clique para ver)
          </summary>
          <ul style="font-size:13px; color:#555; columns:2;">{linhas_veiculos}</ul>
        </details>
        """

        corpo = f"<p>Foram encontradas <strong>{len(noticias)} notícia(s)</strong> {periodo}:</p>" + resumo_veiculos + itens

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; background:#f5f5f5; padding:24px;">
      <div style="max-width:700px; margin:auto; background:#f9f9f9; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <div style="background:#1a1a2e; color:white; padding:24px;">
          <h1 style="margin:0; font-size:22px;">🔎 Monitor de Notícias</h1>
          <p style="margin:4px 0 0 0; opacity:0.8; font-size:14px;">
            Polícia Preditiva · Muralha Paulista · Smart Sampa &nbsp;|&nbsp; {hoje}
          </p>
        </div>
        <div style="padding:24px;">
          {corpo}
        </div>
        <div style="background:#eee; padding:16px; font-size:12px; color:#888; text-align:center;">
          Gerado automaticamente via Google Notícias.<br>
          Cobre todos os veículos brasileiros indexados pelo Google.
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
    print("=" * 55)
    print("  MONITOR DE NOTÍCIAS (via Google Notícias)")
    print("=" * 55)

    noticias, termos_com_problema = buscar_noticias()

    print(f"\n📋 Total encontrado: {len(noticias)} notícia(s)")
    print(f"🔎 Termos buscados: {len(TERMOS_BUSCA)}")
    if termos_com_problema:
        print(f"⚠️  Termos com erro: {', '.join(termos_com_problema)}")
    print()

    html = montar_email_html(noticias)
    enviar_email(html, len(noticias))

    print("\n✅ Concluído!")
