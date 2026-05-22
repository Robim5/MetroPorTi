<p align="center">
  <img src="assets/logo.png" alt="MetroPorTi" width="180" />
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

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Estado da API (para Railway) |
| `GET` | `/stops` | Lista paragens (`?page=1&limit=20`) |
| `GET` | `/stops/{stop_id}` | Detalhe de uma paragem |
| `GET` | `/search/stops?q=` | Pesquisa por nome |
| `GET` | `/routes` | Linhas A, B, C… (`?page=1&limit=20`) |
| `GET` | `/stops/{stop_id}/schedule` | Horários na paragem, por linha e direção |
| `GET` | `/stops/{stop_id}/next` | Próximas chegadas (`?limit=5`) |
| `GET` | `/stops/{stop_id}/arrivals` | Chegadas filtradas por destino (`?destination=`) |
| `GET` | `/vehicle/position` | Posição simulada do comboio (`?route_id=A`) |
| `GET` | `/fare` | Tarifa entre zonas (`?from_zone=PRT1&to_zone=PRT2`) |
| `GET` | `/docs` | Documentação interativa (Swagger) |

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

Abre **http://localhost:8000/docs** para experimentar os endpoints.

Coloca os ficheiros GTFS em `gtfs_data/` (`stops.txt`, `routes.txt`, `stop_times.txt`, etc.). Mantém a extensão `.txt`.

---

## Autenticação e limites

**API Key** (opcional em local, recomendada em produção)

Se `API_KEY` estiver definida no `.env`, envia em cada pedido:

```http
X-API-Key: a_tua_chave
```

Rotas públicas sem chave: `/health` e `/docs`.

**Rate limit:** 60 pedidos por minuto por IP (`RATE_LIMIT=60/minute`). O `/health` está isento para o Railway não falhar nos health checks.

---

## Exemplos

```http
GET /stops?limit=5
GET /search/stops?q=Trindade
GET /stops/5726/next?limit=3
GET /stops/5726/arrivals?destination=Póvoa de Varzim
GET /vehicle/position?route_id=A
GET /fare?from_zone=PRT1&to_zone=PRT2
```

Com API key:

```powershell
curl -H "X-API-Key: TUA_CHAVE" "http://localhost:8000/stops?limit=3"
```

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

5. Gera um domínio em **Networking** e testa `https://teu-dominio.up.railway.app/health`.

O ficheiro `Procfile` diz ao Railway como arrancar a app (ver secção abaixo).

---

## Estrutura do projeto

```
app/           → API FastAPI (routers, modelos, cache, segurança)
scripts/       → init_db.py e import_gtfs.py
sql/           → schema PostgreSQL
gtfs_data/     → ficheiros GTFS (.txt, não versionados)
tests/         → testes básicos
Procfile       → comando de arranque no Railway
```

---

## Testes

```powershell
python -m pytest -q
```

---

<p align="center">
  <sub>Feito com dados GTFS do Metro do Porto · FastAPI · Neon · Railway</sub>
</p>
