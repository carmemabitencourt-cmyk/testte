"""Cliente para integração com Google Sheets."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import List, Set

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from src.models import Lead


@dataclass
class GoogleSheetsClient:
    """Cliente responsável por ler e escrever leads no Google Sheets."""

    credentials_path: str
    sheet_id: str

    def __post_init__(self) -> None:
        self._client = self._authorize()
        self._sheet = self._client.open_by_key(self.sheet_id).sheet1

    def _authorize(self) -> gspread.Client:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_path, scope
        )
        return gspread.authorize(credentials)

    def get_existing_phones(self) -> Set[str]:
        """Obtém os telefones existentes para deduplicação."""
        try:
            values = self._sheet.col_values(5)
        except gspread.exceptions.GSpreadException as exc:
            logging.warning("Falha ao ler telefones existentes: %s", exc)
            return set()

        if not values:
            return set()
        return {value for value in values[1:] if value}

    def append_leads(self, leads: List[Lead]) -> None:
        """Envia leads para o Google Sheets em batch."""
        if not leads:
            logging.info("Nenhum lead para enviar ao Google Sheets.")
            return

        header = [
            "nome",
            "nicho",
            "cidade",
            "endereco",
            "telefone",
            "email",
            "site",
            "instagram",
            "facebook",
            "rating",
            "total_reviews",
            "score",
            "fonte",
            "data_coleta",
            "place_id",
            "latitude",
            "longitude",
        ]

        try:
            existing_header = self._sheet.row_values(1)
            if not existing_header:
                self._sheet.append_row(header)
        except gspread.exceptions.GSpreadException as exc:
            logging.warning("Falha ao validar header: %s", exc)

        rows = [lead.to_list() for lead in leads]
        try:
            self._sheet.append_rows(rows, value_input_option="USER_ENTERED")
            logging.info("%s leads enviados ao Google Sheets.", len(leads))
        except gspread.exceptions.GSpreadException as exc:
            logging.warning("Falha ao enviar leads: %s", exc)
