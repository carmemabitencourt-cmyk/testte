"""Scraper síncrono encapsulado para SerpAPI com fallback opcional."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor

import requests

from src.models import Lead


@dataclass
class SerpApiScraper:
    """Scraper para SerpAPI executado em ThreadPoolExecutor."""

    api_key: str
    executor: ThreadPoolExecutor | None = None

    def __post_init__(self) -> None:
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=5)

    async def search(self, nicho: str, cidade: str) -> List[Lead]:
        """Busca leads na SerpAPI."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._sync_search, nicho, cidade
        )

    def _sync_search(self, nicho: str, cidade: str) -> List[Lead]:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "q": f"{nicho} em {cidade}",
            "hl": "pt",
            "api_key": self.api_key,
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logging.warning("Falha na SerpAPI: %s", exc)
            return []

        results = data.get("local_results", [])
        leads: List[Lead] = []
        for item in results:
            telefone = self._format_phone(item.get("phone"))
            lead = Lead(
                nome=item.get("title", ""),
                nicho=nicho,
                cidade=cidade,
                endereco=item.get("address"),
                telefone=telefone,
                email=None,
                site=item.get("website"),
                instagram=None,
                facebook=None,
                rating=item.get("rating"),
                total_reviews=item.get("reviews"),
                score=0,
                fonte="serpapi",
                place_id=item.get("place_id"),
                latitude=item.get("gps_coordinates", {}).get("latitude"),
                longitude=item.get("gps_coordinates", {}).get("longitude"),
            )
            leads.append(lead)
        logging.info(
            "SerpAPI retornou %s resultados para %s/%s.",
            len(leads),
            nicho,
            cidade,
        )
        return leads

    @staticmethod
    def _format_phone(phone: str | None) -> str | None:
        if not phone:
            return None
        digits = "".join(char for char in phone if char.isdigit())
        if digits.startswith("55"):
            digits = digits[2:]
        if len(digits) >= 10:
            return f"+55{digits}"
        return None
