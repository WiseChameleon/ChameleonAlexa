from AlexaSmartHomeAPI_Chameleon.service import get_stats_from_adafruit


def test_get_stats():
    assert get_stats_from_adafruit('test')
