# 🔎 Monitor de Notícias — Polícia Preditiva / Muralha Paulista

Aplicação que busca automaticamente notícias sobre **polícia preditiva**, **muralha paulista** e temas relacionados nos principais veículos de imprensa brasileiros, e envia um compilado por e-mail.

---

## 📋 O que ele faz?

- Varre os feeds RSS de **14 veículos brasileiros** (G1, Folha, Estadão, Agência Pública, The Intercept, Brasil de Fato, Metrópoles, Carta Capital e outros)
- Filtra notícias que contenham os termos monitorados
- Monta um e-mail bonito e formatado com título, veículo, data e link de cada notícia
- Envia para o seu e-mail automaticamente
- Pode rodar **toda semana de forma automática** via GitHub (de graça!)

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

## 📰 Veículos monitorados (30 fontes)

**Grandes veículos nacionais:**
G1 / Globo · G1 São Paulo · O Globo · O Globo Brasil · UOL Notícias · Folha de S.Paulo · Folha Cotidiano · Estadão · Valor Econômico · R7 · CNN Brasil · BBC News Brasil · Veja · Metrópoles · Correio Braziliense · Agência Brasil

**Análise e política:**
Poder360 · Nexo Jornal · Carta Capital · Piauí

**Investigativo / direitos humanos / segurança:**
Agência Pública · The Intercept Brasil · Brasil de Fato · Ponte Jornalismo · Marco Zero

**Jurídico / regulação / tecnologia:**
JOTA · Migalhas · TecMundo · Tilt (UOL)

**Universitário / regional:**
Jornal da USP · Marília Notícia

> ⚠️ **Importante:** feeds RSS às vezes mudam de endereço. Ao rodar, o script mostra no final quais fontes não responderam. Se alguma aparecer sempre com problema, o link do feed dela pode ter mudado — me avise que atualizo.

> 💡 **Não há limite prático** de fontes. Para adicionar mais, é só incluir uma linha na lista `FEEDS` no arquivo `monitor.py` no formato `"Nome do veículo": "url-do-rss"`.

---

## 🔑 Termos monitorados

**Termos principais:**
- polícia preditiva / policiamento preditivo
- muralha paulista
- smart sampa / smartsampa / smart-sampa *(pega todas as grafias)*

**Termos relacionados (ampliam a cobertura):**
- vigilância preditiva
- reconhecimento facial
- câmeras inteligentes
- monitoramento preditivo
- tecnologia policial
- videomonitoramento

> Para adicionar ou remover termos, edite a lista `PALAVRAS_CHAVE` no arquivo `monitor.py`

---

## ⚙️ Como o monitor funciona (importante!)

**Onde ele busca as palavras:**
1. Primeiro no **título** e no **resumo** da notícia (rápido)
2. Se não achar, **abre a matéria e lê o texto completo** (pega muito mais!)

> Isso é controlado pela opção `LER_TEXTO_COMPLETO = True` no topo do `monitor.py`. Deixe `True` para busca completa, ou `False` para busca rápida (só título/resumo).

**Período de busca:**
- Por padrão, busca notícias dos **últimos 7 dias** (`DIAS_PARA_TRAS = 7`)
- Para pegar tudo o que estiver no feed (sem filtro de data), coloque `DIAS_PARA_TRAS = 0`

**Sem repetição:** o monitor evita mostrar a mesma notícia duas vezes na mesma varredura.

---

## ❓ Dúvidas comuns

**O script rodou mas não recebi e-mail?**
→ Verifique se a Verificação em 2 etapas está ativa no Gmail e se a Senha de App foi gerada corretamente.

**Quero receber mais vezes por semana?**
→ No arquivo `.github/workflows/monitor_semanal.yml`, altere a linha `cron`. Ex: `0 11 * * 1,4` roda às segundas e quintas.

**Como adicionar mais veículos?**
→ Procure pelo RSS do veículo desejado e adicione na lista `FEEDS` no arquivo `monitor.py`.
