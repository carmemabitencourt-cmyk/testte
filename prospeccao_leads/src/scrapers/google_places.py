"""Scraper assíncrono para Google Places API."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt
from tenacity import wait_exponential

from src.models import Lead


@dataclass
class GooglePlacesScraper:
    """Scraper para a API Google Places com suporte assíncrono."""

    api_key: str
    rate_limit_per_second: float
    max_workers: int = 5

    def __post_init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._semaphore = asyncio.Semaphore(self.max_workers)
        self._rate_lock = asyncio.Lock()
        self._last_call: float | None = None

    async def __aenter__(self) -> "GooglePlacesScraper":
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session:
            await self._session.close()

    async def _rate_limit(self) -> None:
        async with self._rate_lock:
            if self._last_call is None:
                self._last_call = asyncio.get_event_loop().time()
                return
            elapsed = asyncio.get_event_loop().time() - self._last_call
            wait_time = max(0, (1 / self.rate_limit_per_second) - elapsed)
            if wait_time:
                await asyncio.sleep(wait_time)
            self._last_call = asyncio.get_event_loop().time()

    async def _request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self._session:
            raise RuntimeError("Sessão HTTP não inicializada.")

        await self._rate_limit()
        async with self._session.get(url, params=params, timeout=30) as response:
            response.raise_for_status()
            return await response.json()

    async def _request_with_retry(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(min=1, max=10),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(aiohttp.ClientError),
            reraise=True,
        ):
            with attempt:
                return await self._request(url, params)
        raise RuntimeError("Falha inesperada na requisição.")

    async def _get_place_details(self, place_id: str) -> Dict[str, Any]:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,formatted_phone_number,website,"
            "formatted_address,geometry,rating,user_ratings_total,"
            "business_status",
            "key": self.api_key,
        }
        return await self._request_with_retry(url, params)

    async def search(self, nicho: str, cidade: str) -> List[Lead]:
        """Busca leads na Google Places API."""
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{nicho} em {cidade}",
            "language": "pt-BR",
            "key": self.api_key,
        }
        leads: List[Lead] = []
        next_page_token: Optional[str] = None
        while True:
            if next_page_token:
                params["pagetoken"] = next_page_token
                await asyncio.sleep(2)

            data = await self._request_with_retry(url, params)
            results = data.get("results", [])
            logging.info(
                "Google Places retornou %s resultados para %s/%s.",
                len(results),
                nicho,
                cidade,
            )
            for item in results:
                if item.get("business_status") != "OPERATIONAL":
                    continue
                place_id = item.get("place_id")
                if not place_id:
                    continue

                async with self._semaphore:
                    details = await self._get_place_details(place_id)

                result = details.get("result", {})
                if result.get("business_status") != "OPERATIONAL":
                    continue

                telefone = self._format_phone(result.get("formatted_phone_number"))
                lead = Lead(
                    nome=result.get("name") or item.get("name", ""),
                    nicho=nicho,
                    cidade=cidade,
                    endereco=result.get("formatted_address")
                    or item.get("formatted_address"),
                    telefone=telefone,
                    email=None,
                    site=result.get("website"),
                    instagram=None,
                    facebook=None,
                    rating=result.get("rating"),
                    total_reviews=result.get("user_ratings_total"),
                    score=0,
                    fonte="google_places",
                    place_id=place_id,
                    latitude=item.get("geometry", {})
                    .get("location", {})
                    .get("lat"),
                    longitude=item.get("geometry", {})
                    .get("location", {})
                    .get("lng"),
                )
                leads.append(lead)
                if len(leads) >= 60:
                    return leads

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break
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
