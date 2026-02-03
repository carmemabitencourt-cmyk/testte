"""Entry point da aplicação de prospecção de leads."""
from __future__ import annotations

import asyncio
import logging
from typing import List

from src.config import Config
from src.models import Lead
from src.processors.deduplicator import Deduplicator
from src.processors.scoring import Scoring
from src.scrapers.google_places import GooglePlacesScraper
from src.scrapers.serpapi import SerpApiScraper
from src.sheets.google_sheets import GoogleSheetsClient


class ScraperApp:
    """Orquestra a coleta, deduplicação e envio dos leads."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.scoring = Scoring()

    async def run(self) -> None:
        """Executa o pipeline completo da aplicação."""
        logging.info("Iniciando aplicação de prospecção.")

        try:
            sheets_client = GoogleSheetsClient(
                credentials_path=self.config.google_sheets_credentials,
                sheet_id=self.config.sheet_id,
            )
        except Exception as exc:  # noqa: BLE001
            logging.exception("Erro ao conectar no Google Sheets: %s", exc)
            return

        existing_phones = sheets_client.get_existing_phones()
        logging.info("%s telefones carregados do Google Sheets.", len(existing_phones))

        leads: List[Lead] = []
        async with GooglePlacesScraper(
            api_key=self.config.google_places_api_key,
            rate_limit_per_second=self.config.rate_limit_per_second,
        ) as google_scraper:
            tasks = [
                google_scraper.search(nicho, cidade)
                for cidade in self.config.cidades
                for nicho in self.config.nichos
            ]

            if self.config.serpapi_key:
                serpapi_scraper = SerpApiScraper(api_key=self.config.serpapi_key)
                tasks.extend(
                    serpapi_scraper.search(nicho, cidade)
                    for cidade in self.config.cidades
                    for nicho in self.config.nichos
                )
            else:
                logging.info("SERPAPI_KEY não configurada. Ignorando SerpAPI.")

            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logging.warning("Erro durante a coleta: %s", result)
                continue
            leads.extend(result)

        logging.info("Total de leads coletados: %s", len(leads))

        deduplicator = Deduplicator(existing_phones=existing_phones)
        leads = deduplicator.deduplicate(leads)

        for lead in leads:
            lead.score = self.scoring.calculate(lead)

        leads.sort(key=lambda item: item.score, reverse=True)
        sheets_client.append_leads(leads)

        logging.info(
            "Processo concluído. Leads finais: %s. Score máximo: %s.",
            len(leads),
            max((lead.score for lead in leads), default=0),
        )


def main() -> None:
    """Ponto de entrada síncrono."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        config = Config.from_env()
    except ValueError as exc:
        logging.error("Configuração inválida: %s", exc)
        return

    asyncio.run(ScraperApp(config).run())


if __name__ == "__main__":
    main()
