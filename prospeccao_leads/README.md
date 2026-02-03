# Sistema de Prospecção de Leads

Sistema assíncrono para coletar leads de múltiplas fontes, calcular scoring de
presença digital e armazenar resultados no Google Sheets.

## Requisitos

- Python 3.10+
- Credenciais de Service Account do Google Sheets (`credentials.json`)

## Configuração

1. Crie um arquivo `.env` baseado em `.env.example`.
2. Adicione o arquivo `credentials.json` com acesso à planilha.
3. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Execução

```bash
python src/main.py
```

## Estrutura

```
prospeccao_leads/
├── src/
│   ├── config.py
│   ├── models.py
│   ├── main.py
│   ├── scrapers/
│   ├── processors/
│   └── sheets/
├── .env.example
├── requirements.txt
└── README.md
```

## Notas

- O scraper da SerpAPI só é ativado se `SERPAPI_KEY` estiver configurada.
- O rate limit é controlado por `RATE_LIMIT_PER_SECOND`.
