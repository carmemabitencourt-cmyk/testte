"""Rotinas de deduplicação de leads."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from difflib import SequenceMatcher
from typing import Iterable

from src.models import Lead


@dataclass
class Deduplicator:
    """Deduplica leads com base em telefone e similaridade de nome."""

    existing_phones: set[str]

    def deduplicate(self, leads: Iterable[Lead]) -> list[Lead]:
        """Remove leads duplicados."""
        deduplicated: list[Lead] = []
        # Agrupa leads por cidade para otimizar a comparação de similaridade de nome
        # Cada entrada contém (nome_lowercased, lead)
        by_city: dict[str, list[tuple[str, Lead]]] = {}
        removed = 0
        normalized_existing = {self._normalize_phone(p) for p in self.existing_phones}

        for lead in leads:
            normalized_phone = self._normalize_phone(lead.telefone)
            if normalized_phone and normalized_phone in normalized_existing:
                removed += 1
                continue

            # Otimização: Só compara similaridade com leads da mesma cidade
            # e evita chamadas repetidas a .lower()
            name_lower = lead.nome.lower()
            city_leads = by_city.get(lead.cidade, [])
            if self._is_similar_name(name_lower, city_leads):
                removed += 1
                continue

            deduplicated.append(lead)
            by_city.setdefault(lead.cidade, []).append((name_lower, lead))

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
    def _is_similar_name(candidate_name_lower: str, city_leads: list[tuple[str, Lead]]) -> bool:
        """Verifica se existe algum lead na lista com nome similar."""
        for lead_name_lower, _ in city_leads:
            # SequenceMatcher é O(n), então reduzir o número de chamadas é crítico
            ratio = SequenceMatcher(
                None, candidate_name_lower, lead_name_lower
            ).ratio()
            if ratio >= 0.8:
                return True
        return False
