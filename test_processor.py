from processor import NewsProcessor



def test_duplicate_article():
    processor_A = NewsProcessor()
    processor_B = NewsProcessor() 
    processor_A.add_news("BTC_001")
    assert processor_A.has_seen("BTC_001") is True
    assert processor_B.has_seen("BTC_001") is False
    