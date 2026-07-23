from ai_eval.metrics.extraction import ExtractionEvaluator

def test_extraction_is_empty():
    evaluator = ExtractionEvaluator()
    assert evaluator._is_empty(None) is True
    assert evaluator._is_empty("") is True
    assert evaluator._is_empty("   ") is True
    assert evaluator._is_empty("None") is True
    assert evaluator._is_empty("N/A") is True
    assert evaluator._is_empty([]) is True
    assert evaluator._is_empty({}) is True
    assert evaluator._is_empty("Project Apex") is False

def test_extraction_simple_accuracy():
    evaluator = ExtractionEvaluator()
    
    extracted = {
        "Project Name": "Project Apex",
        "Client": "Acme Corp",
        "Start Year": "2024",
        "Revenue/Billing": "$250,000"
      }
      
    expected = {
        "Project Name": "Project Apex",
        "Client": "Acme Corporation",
        "Start Year": "2024",
        "Revenue/Billing": "250000"
      }
      
    # Client: substring match
    # Start Year: exact match
    # Revenue: numeric equivalent match
    # Project Name: exact match
    
    metrics = evaluator.evaluate(
        extracted_fields=extracted,
        expected_fields=expected,
        source_text="Contract for Project Apex in 2024 with Acme Corporation for 250000.",
        field_citations={
            "Project Name": "Project Apex",
            "Start Year": "2024"
        }
    )
    
    assert metrics.accuracy == 100.0
    assert metrics.completeness == 100.0
    # Two citations checked and both present in source text
    assert metrics.citation_coverage == 50.0  # 2 citations / 4 non-empty fields = 50%
    assert metrics.missing_field_detection == 100.0
