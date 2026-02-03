"""Modelos de dados usados no sistema de prospecção."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class Lead:
    """Representa um lead coletado das fontes disponíveis."""

    nome: str
    nicho: str
    cidade: str
    endereco: str | None
    telefone: str | None
    email: str | None
    site: str | None
    instagram: str | None
    facebook: str | None
    rating: float | None
    total_reviews: int | None
    score: int
    fonte: str
    data_coleta: str = field(
        default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds")
    )
    place_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte o lead em dicionário para persistência."""
        return {
            "nome": self.nome,
            "nicho": self.nicho,
            "cidade": self.cidade,
            "endereco": self.endereco,
            "telefone": self.telefone,
            "email": self.email,
            "site": self.site,
            "instagram": self.instagram,
            "facebook": self.facebook,
            "rating": self.rating,
            "total_reviews": self.total_reviews,
            "score": self.score,
            "fonte": self.fonte,
            "data_coleta": self.data_coleta,
            "place_id": self.place_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    def to_list(self) -> List[Any]:
        """Converte o lead em lista na ordem esperada pelo Google Sheets."""
        return [
            self.nome,
            self.nicho,
            self.cidade,
            self.endereco,
            self.telefone,
            self.email,
            self.site,
            self.instagram,
            self.facebook,
            self.rating,
            self.total_reviews,
            self.score,
            self.fonte,
            self.data_coleta,
            self.place_id,
            self.latitude,
            self.longitude,
        ]
