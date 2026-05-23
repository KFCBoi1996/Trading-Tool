from __future__ import annotations

from app.data.mock_provider import DeterministicMockMarketProvider


def test_mock_provider_is_deterministic_for_repeated_calls() -> None:
    provider = DeterministicMockMarketProvider()
    a = provider.get_latest_candles("EUR_USD", "H1", 10)
    b = provider.get_latest_candles("EUR_USD", "H1", 10)
    assert [c.timestamp for c in a] == [c.timestamp for c in b]
    assert [c.open for c in a] == [c.open for c in b]
    assert [c.high for c in a] == [c.high for c in b]
    assert [c.low for c in a] == [c.low for c in b]


def test_mock_provider_labels_outputs_as_mock() -> None:
    provider = DeterministicMockMarketProvider()
    candles = provider.get_latest_candles("USD_JPY", "M15", 3)
    quote = provider.get_latest_quote("USD_JPY")
    assert all(c.data_status == "MOCK" and c.is_mock for c in candles)
    assert quote.data_status == "MOCK" and quote.is_mock
    assert quote.spread_pips > 0


def test_mock_provider_rejects_unsupported_inputs() -> None:
    provider = DeterministicMockMarketProvider()
    try:
        provider.get_latest_candles("XXX_YYY", "M15", 1)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for unsupported instrument")
    try:
        provider.get_latest_candles("EUR_USD", "D1", 1)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for unsupported timeframe")


def test_mock_provider_anchor_for_h4_is_block_aligned() -> None:
    provider = DeterministicMockMarketProvider()
    candles = provider.get_latest_candles("GBP_USD", "H4", 4)
    hours = {c.timestamp.hour for c in candles}
    assert all(hour % 4 == 0 for hour in hours)
