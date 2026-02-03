"""Cálculo de score baseado em presença digital."""
from __future__ import annotations

from dataclasses import dataclass

from src.models import Lead


@dataclass
class Scoring:
    """Calcula o score de um lead."""

    priority_nichos: tuple[str, ...] = (
        "dentista",
        "clínica estética",
        "clinica estetica",
    )

    def calculate(self, lead: Lead) -> int:
        """Calcula o score do lead (0-100)."""
        score = 0

        if not lead.site:
            score += 25
            if lead.instagram or lead.facebook:
                score += 20
        else:
            if "wix" in lead.site.lower() or "wordpress" in lead.site.lower():
                score += 15

        if lead.telefone:
            score += 10
        if lead.email:
            score += 15

        if lead.rating is not None and lead.rating < 4.0:
            score += 10
        if lead.total_reviews is not None and lead.total_reviews < 10:
            score += 10

        if lead.nicho.lower() in self.priority_nichos:
            score += 10

        return min(score, 100)
