import llmtg.cards as cards


def test_cards_public_api_exports_bulk_helpers() -> None:
    assert cards.BulkScryfallProvider is not None
    assert callable(cards.ensure_default_bulk_data)
    assert callable(cards.ensure_oracle_bulk_data)
