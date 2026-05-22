<p align="center">
  <img src="frontend/assets/logo.png" alt="MetroPorTi" width="220" />
</p>

<h1 align="center">MetroPorTi</h1>

<p align="center">
  Horários do Metro do Porto, traduzidos de GTFS para uma API REST rápida e legível.<br/>
  Paragens, linhas, próximas chegadas e tarifas! Tudo num sítio, pronto para a tua app.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/GTFS-Metro_do_Porto-00B5E2?style=flat-square" alt="GTFS" />
</p>

---

## O que é isto

O **MetroPorTi** é uma API que lê dados oficiais GTFS do Metro do Porto, guarda-os em PostgreSQL (Neon) e expõe endpoints simples para consultar paragens, linhas, horários e tarifas. Foi pensada para quem quer construir uma app ou site sem ter de descodificar ficheiros `.txt` gigantes.

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| API | FastAPI + Uvicorn |
| Base de dados | PostgreSQL (Neon) |
| Driver async | asyncpg |
| Dados | GTFS (Metro do Porto) |
| Deploy | Railway |

---

## Endpoints

Base URL local: `http://localhost:8000`  
Em produção: `https://o-teu-dominio.up.railway.app`

Substitui `API_KEY` pela tua chave. Podes usar `?api_key=API_KEY` no browser ou o header `X-API-Key`.

### Sistema e paragens

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Estado da API (sem chave) |
| `GET` | `/docs` | Swagger (sem chave) |
| `GET` | `/stops` | Lista paragens (`?page=1&limit=20`) |
| `GET` | `/stops/{stop_id}` | Detalhe de uma paragem |
| `GET` | `/search/stops?q=` | Pesquisa por nome |
| `GET` | `/stops/nearby` | Paragens perto de ti (`?lat=&lon=&radius_m=800`) |

### Linhas e horários

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/routes` | Linhas A, B, C… |
| `GET` | `/lines/{route_id}/stops` | Paragens da linha por ordem (`?direction_id=0`) |
| `GET` | `/stops/{stop_id}/schedule` | Horário completo na paragem |
| `GET` | `/stops/{stop_id}/next` | Próximas chegadas (`?limit=5&route_id=C`) |
| `GET` | `/stops/{stop_id}/arrivals` | Chegadas por destino (`?destination=&route_id=`) |
| `GET` | `/stops/{stop_id}/board` | Painel estilo estação (várias linhas) |
| `GET` | `/journey` | Viagem directa origem→destino (`?from_stop_id=&to_stop_id=`) |

### Extra

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/vehicle/position` | Posição simulada (`?route_id=A`) |
| `GET` | `/fare` | Tarifa entre zonas (`?from_zone=PRT1&to_zone=MAI2`) |

---

## Exemplos reais (perguntas do dia a dia)

Fluxo habitual: **pesquisar paragem** -> usar o `stop_id` nos endpoints de horários.

**«Quando passa o próximo metro?»** (Trindade, hub com várias linhas):

```text
/search/stops?q=Trindade&api_key=API_KEY
/stops/5726/next?limit=10&api_key=API_KEY
```

**«Só a linha B»** na mesma paragem:

```text
/stops/5726/next?limit=8&route_id=B&api_key=API_KEY
```

**Filtrar por destino** — o texto tem de aparecer no sentido (`trip_headsign`) **nessa paragem**. No Fórum Maia costuma funcionar `Campanhã`; para `Póvoa` experimenta na Trindade. Lista vazia `[]` = não há próximos comboios para esse destino **ali**, não é erro da API:

```text
/stops/5760/arrivals?destination=Campanhã&limit=8&api_key=API_KEY
/stops/5726/arrivals?destination=Póvoa&limit=8&api_key=API_KEY
```

**Paragens de uma linha no mapa:**

```text
/lines/B/stops?direction_id=0&api_key=API_KEY
```

**Paragens perto (GPS):**

```text
/stops/nearby?lat=41.1523&lon=-8.6093&radius_m=1000&api_key=API_KEY
```

---

## Começar em 5 minutos

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copia `.env.example` para `.env` e preenche `DATABASE_URL` (Neon, com `?sslmode=require`).

```powershell
python scripts/init_db.py
python scripts/import_gtfs.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Abre **http://localhost:8000/docs** para a documentação Swagger.

Coloca os ficheiros GTFS em `gtfs_data/` (`stops.txt`, `routes.txt`, `stop_times.txt`, etc.). Mantém a extensão `.txt`.

---

## Painel web para testar a API

O projeto inclui um frontend em `frontend/` servido pela própria API. Serve para ver se cada endpoint funciona, com separadores e resposta JSON em tempo real.

**Importante:** não abras `frontend/index.html` com duplo clique no Explorer. O browser usa `file://` e bloqueia os pedidos, ou seja, aparece «Não foi possível aceder ao seu ficheiro». Usa sempre o URL com a API a correr.

### Arrancar (local)

Com o mesmo comando da API:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Abre no browser:

```text
http://localhost:8000/testar/
```

1. Em **URL da API** deixa `http://localhost:8000` (preenche automaticamente se estiveres no mesmo servidor).
2. Em **API Key** cola a chave do `.env` se tiveres `API_KEY` definida; em local podes deixar vazio.
3. Clica **Guardar**, escolhe um separador (Paragens, Horários, Linhas…) e **Testar** em cada exemplo.

### Railway

Depois do deploy:

```text
https://O-TEU-DOMINIO.up.railway.app/testar/
```

Cola o mesmo domínio em «URL da API» e a `API_KEY` das Variables do Railway.

### Estrutura do frontend

```text
frontend/
├── index.html
├── css/main.css
├── js/
│   ├── config.js          # URL + API key (localStorage)
│   ├── api-client.js      # pedidos fetch
│   ├── tests-catalog.js   # lista de testes por tab
│   └── app.js             # interface
└── assets/logo.png
```

---

## Autenticação e limites

**API Key** (opcional em local, recomendada em produção)

Se `API_KEY` estiver definida, envia a chave de uma destas formas:

**Header** (Postman, código):
```http
X-API-Key: a_tua_chave
```

**No URL** (testar no browser):
```text
https://BASE/stops?page=1&limit=5&api_key=a_tua_chave
```

Rotas públicas sem chave: `/health` e `/docs`.

**Rate limit:** 60 pedidos por minuto por IP (`RATE_LIMIT=60/minute`). O `/health` está isento para o Railway não falhar nos health checks.

---

## Deploy no Railway

1. Faz push do repositório para o GitHub (sem `.env`, sem `gtfs_data/*.txt`).
2. No [Railway](https://railway.app): **New Project** → liga o repo.
3. Em **Variables**, define:

| Variável | Valor |
|----------|--------|
| `DATABASE_URL` | Connection string Neon com `?sslmode=require` |
| `API_KEY` | Chave forte (gera com `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `APP_ENV` | `production` |
| `ALLOWED_ORIGINS` | URL do teu frontend |
| `RATE_LIMIT` | `60/minute` |

4. **Antes** do primeiro uso em produção, corre na tua máquina (com a mesma `DATABASE_URL`):

```powershell
python scripts/init_db.py
python scripts/import_gtfs.py
```

5. Gera um domínio em **Networking** e testa `https://teu-dominio.up.railway.app/health` e o painel `https://teu-dominio.up.railway.app/testar/`.

O ficheiro `Procfile` diz ao Railway como arrancar a app.

---

## Estrutura do projeto

```
app/           → API FastAPI (routers, modelos, cache, segurança)
frontend/      → painel de testes (servido em /testar/)
scripts/       → init_db.py e import_gtfs.py
sql/           → schema PostgreSQL
gtfs_data/     → ficheiros GTFS (.txt, não versionados)
tests/         → testes automáticos (pytest)
Procfile       → comando de arranque no Railway
```

---

## Testes

```powershell
python -m pytest -q
```

---

## Licença

Este projeto está licenciado sob a **[MIT License](LICENSE)**.

---

<p align="center">
  <sub>
    Dados GTFS do Metro do Porto (feed de 7 de abril de 2026) · FastAPI · Neon · Railway<br/>
    Última atualização: 21 de maio de 2026
  </sub>
</p>
