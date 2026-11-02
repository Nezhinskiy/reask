"""Thin client for ledger-api (ONB-9: one request per statement row)."""

import os

import requests

LEDGER_URL = os.environ["LEDGER_API_URL"]
TIMEOUT_S = 3


def post_entry(school_id, entry):
    r = requests.post(f"{LEDGER_URL}/schools/{school_id}/entries", json=entry, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()["id"]


def rollback(entry_ids):
    for entry_id in entry_ids:
        requests.delete(f"{LEDGER_URL}/entries/{entry_id}", timeout=TIMEOUT_S)
