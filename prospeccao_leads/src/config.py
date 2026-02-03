"""Configurações centralizadas carregadas via variáveis de ambiente."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import List

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Configurações da aplicação carregadas do ambiente."""

    google_places_api_key: str
    sheet_id: str
    serpapi_key: str | None
    cidades: List[str]
    nichos: List[str]
    rate_limit_per_second: float
    google_sheets_credentials: str

    @staticmethod
    def _split_list(value: str | None) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    @classmethod
    def from_env(cls) -> "Config":
        """Carrega as configurações a partir de variáveis de ambiente."""
        load_dotenv()
        google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
        sheet_id = os.getenv("SHEET_ID", "").strip()
        serpapi_key = os.getenv("SERPAPI_KEY", "").strip() or None
        cidades = cls._split_list(os.getenv("CIDADES"))
        nichos = cls._split_list(os.getenv("NICHOS"))
        rate_limit_per_second = float(os.getenv("RATE_LIMIT_PER_SECOND", "4"))
        google_sheets_credentials = os.getenv(
            "GOOGLE_SHEETS_CREDENTIALS", "credentials.json"
        ).strip()

        missing = []
        if not google_places_api_key:
            missing.append("GOOGLE_PLACES_API_KEY")
        if not sheet_id:
            missing.append("SHEET_ID")
        if missing:
            raise ValueError(
                "Chaves obrigatórias ausentes: " + ", ".join(missing)
            )
        if not cidades or not nichos:
            raise ValueError(
                "CIDADES e NICHOS devem conter pelo menos um valor cada."
            )

        return cls(
            google_places_api_key=google_places_api_key,
            sheet_id=sheet_id,
            serpapi_key=serpapi_key,
            cidades=cidades,
            nichos=nichos,
            rate_limit_per_second=rate_limit_per_second,
            google_sheets_credentials=google_sheets_credentials,
        )
