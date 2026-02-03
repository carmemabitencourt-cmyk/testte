"""Rotinas de deduplicação de leads."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from difflib import SequenceMatcher
from typing import Iterable, List, Set

from src.models import Lead


@dataclass
class Deduplicator:
    """Deduplica leads com base em telefone e similaridade de nome."""

    existing_phones: Set[str]

    def deduplicate(self, leads: Iterable[Lead]) -> List[Lead]:
        """Remove leads duplicados."""
        deduplicated: List[Lead] = []
        removed = 0
        normalized_existing = {self._normalize_phone(p) for p in self.existing_phones}

        for lead in leads:
            normalized_phone = self._normalize_phone(lead.telefone)
            if normalized_phone and normalized_phone in normalized_existing:
                removed += 1
                continue

            if self._is_similar_name(lead, deduplicated):
                removed += 1
                continue

            deduplicated.append(lead)
            if normalized_phone:
                normalized_existing.add(normalized_phone)

        logging.info("Deduplicação removeu %s leads.", removed)
        return deduplicated

    @staticmethod
    def _normalize_phone(phone: str | None) -> str | None:
        if not phone:
            return None
        digits = "".join(char for char in phone if char.isdigit())
        if digits.startswith("55"):
            digits = digits[2:]
        return digits

    @staticmethod
    def _is_similar_name(candidate: Lead, leads: Iterable[Lead]) -> bool:
        for lead in leads:
            ratio = SequenceMatcher(
                None, candidate.nome.lower(), lead.nome.lower()
            ).ratio()
            if ratio >= 0.8 and candidate.cidade == lead.cidade:
                return True
        return False
