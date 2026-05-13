def test_app_importable():
    import concept_analytics
    assert concept_analytics is not None

def test_app_config():
    from concept_analytics.apps import ConceptAnalyticsConfig
    assert ConceptAnalyticsConfig.name == "concept_analytics"
