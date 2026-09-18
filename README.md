# 🔎 Monitor de Notícias — Polícia Preditiva / Muralha Paulista

Aplicação que busca automaticamente notícias sobre **polícia preditiva**, **muralha paulista** e temas relacionados nos principais veículos de imprensa brasileiros, e envia um compilado por e-mail.

---

## 📋 O que ele faz?

- Busca notícias usando o **RSS do Google Notícias** — que cobre **TODOS os veículos brasileiros** de uma vez (Folha, Estadão, G1, UOL, CNN, Metrópoles, etc.)
- É a mesma tecnologia por trás do **Google Alertas**: estável, rápido e sem paywall no feed
- Filtra por palavras-chave e pelos **últimos 7 dias** direto na origem
- Remove notícias repetidas
- Monta um e-mail formatado com título, veículo, data e link de cada notícia
- Envia para o seu e-mail automaticamente
- Pode rodar **toda semana de forma automática** via GitHub (de graça!)

> **Por que Google Notícias em vez de feeds RSS individuais?** Muitos veículos (Folha, Estadão, R7...) mudam a URL do feed, escondem atrás de paywall ou removem o RSS. O Google Notícias resolve tudo isso: uma busca só já traz notícias de todos os jornais.

---

## 🚀 Como usar — Passo a Passo

### PARTE 1 — Preparar o Gmail para envio

O Gmail exige uma **"Senha de App"** para permitir envios via script. É diferente da sua senha normal e mais segura.

1. Acesse: https://myaccount.google.com/security
2. Certifique-se de que a **Verificação em 2 etapas** está **ativada** (obrigatório)
3. Acesse: https://myaccount.google.com/apppasswords
4. Em "Nome do app", escreva: `monitor noticias`
5. Clique em **Criar**
6. O Google vai gerar uma senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)
7. **Copie essa senha** — você vai precisar dela logo

---

### PARTE 2 — Rodar no seu computador

#### 1. Instale o Python (uma vez só)
- Acesse: https://www.python.org/downloads/
- Baixe e instale a versão mais recente
- Durante a instalação, marque a opção **"Add Python to PATH"**

#### 2. Baixe os arquivos do projeto
- Baixe todos os arquivos desta pasta para o seu computador
- Coloque numa pasta fácil de achar, ex: `C:\monitor_noticias`

#### 3. Configure o seu e-mail
- Dentro da pasta, crie um arquivo chamado `.env` (sem extensão)
- Abra o arquivo `.env.example` como modelo e preencha:

```
EMAIL_REMETENTE=seu_email@gmail.com
SENHA_APP=abcd efgh ijkl mnop
EMAIL_DESTINO=limacase9@gmail.com
```

#### 4. Instale as dependências
- Abra o **Prompt de Comando** (tecla Windows + R, digite `cmd`, Enter)
- Navegue até a pasta: `cd C:\monitor_noticias`
- Execute: `pip install -r requirements.txt`

#### 5. Rode!
```
python monitor.py
```

Pronto! Em alguns segundos você receberá o e-mail.

---

### PARTE 3 — Rodar automaticamente toda semana no GitHub (de graça!)

#### 1. Crie uma conta no GitHub
- Acesse: https://github.com e crie uma conta gratuita

#### 2. Crie um repositório privado
- Clique em **"New repository"**
- Nome: `monitor-noticias`
- Marque como **Private** (seus dados ficam seguros)
- Clique em **"Create repository"**

#### 3. Suba os arquivos
- Siga as instruções do GitHub para fazer upload dos arquivos do projeto
- **Não suba o arquivo `.env`** — ele contém sua senha!

#### 4. Configure os Secrets (suas senhas ficam seguras aqui)
- No repositório, vá em **Settings → Secrets and variables → Actions**
- Clique em **"New repository secret"** e adicione 3 secrets:

| Nome | Valor |
|------|-------|
| `EMAIL_REMETENTE` | seu_email@gmail.com |
| `SENHA_APP` | sua senha de app do Gmail |
| `EMAIL_DESTINO` | limacase9@gmail.com |

#### 5. Ative o GitHub Actions
- Vá na aba **"Actions"** do repositório
- Clique em **"I understand my workflows, go ahead and enable them"**

#### 6. Pronto! 🎉
- Toda **segunda-feira às 8h** (horário de Brasília) o GitHub vai rodar o monitor automaticamente e te mandar o e-mail
- Você pode também rodar **a qualquer hora** manualmente: vá em Actions → "Monitor de Notícias Semanal" → "Run workflow"

---

## 📰 Veículos monitorados

**Todos os veículos brasileiros indexados pelo Google Notícias.**

Como o monitor usa a busca do Google Notícias, ele automaticamente cobre Folha, Estadão, G1, UOL, O Globo, CNN Brasil, Metrópoles, Agência Pública, Ponte Jornalismo, Nexo, JOTA e centenas de outros — sem precisar cadastrar o feed de cada um. Se o Google indexa, o monitor encontra.

---

## 🔑 Termos monitorados

Cada termo é uma busca no Google Notícias (aspas = expressão exata):

- `"muralha paulista"`
- `"smart sampa"` e `"smartsampa"`
- `"polícia preditiva"`
- `"policiamento preditivo"`
- `"vigilância preditiva"`
- `"monitoramento preditivo"`
- `"reconhecimento facial"` combinado com São Paulo / polícia / segurança
- `"câmeras inteligentes"` combinado com São Paulo / polícia / segurança

> Para adicionar ou remover termos, edite a lista `TERMOS_BUSCA` no arquivo `monitor.py`. Dica: use aspas para expressões exatas e parênteses com `OR` para combinar contextos, ex: `'"reconhecimento facial" (São Paulo OR polícia)'`.

---

## ⚙️ Como o monitor funciona

- Para **cada termo**, monta uma busca no RSS do Google Notícias já filtrada pelos **últimos 7 dias** (operador `when:7d`)
- Junta os resultados de todos os termos e **remove repetições** (por link e por título)
- Ordena da notícia **mais recente para a mais antiga**
- Cada item mostra o **veículo**, a **data** e **qual termo** fez a notícia aparecer

**Período de busca:** controlado por `DIAS_PARA_TRAS` no topo do `monitor.py` (padrão: `7`).

---

## ❓ Dúvidas comuns

**O script rodou mas não recebi e-mail?**
→ Verifique se a Verificação em 2 etapas está ativa no Gmail e se a Senha de App foi gerada corretamente.

**Quero receber mais vezes por semana?**
→ No arquivo `.github/workflows/monitor_semanal.yml`, altere a linha `cron`. Ex: `0 11 * * 1,4` roda às segundas e quintas.

**Como adicionar mais veículos?**
→ Procure pelo RSS do veículo desejado e adicione na lista `FEEDS` no arquivo `monitor.py`.
