"""Tests for Supabase-First Company Intelligence and Zero-Token Database Loading."""
from fastapi.testclient import TestClient
from app.main import app
from app.intelligence import supabase_source, agents

client = TestClient(app)


def test_supabase_configured_and_has_118_companies():
    assert supabase_source.supabase_configured() is True
    comps = supabase_source.list_companies(limit=200)
    assert len(comps) >= 110, f"Expected ~118 companies in Supabase, got {len(comps)}"
    names = {c['name'].lower() for c in comps}
    assert any('google' in n for n in names)
    assert any('apple' in n for n in names)
    assert any('uber' in n for n in names)
    assert any('amazon' in n for n in names)
    assert any('swiggy' in n for n in names)


def test_api_companies_returns_all_supabase_companies():
    res = client.get('/api/companies')
    assert res.status_code == 200
    data = res.json()
    assert data.get('total_count', 0) >= 118
    assert data.get('supabase_count', 0) >= 110
    assert 'Supabase verified dataset' in data.get('source', '')


def test_company_bundle_from_supabase_zero_tokens():
    # Uber is company #51 in Supabase
    bundle = supabase_source.build_bundle_from_supabase('Uber')
    assert bundle is not None
    assert bundle['mode'] == 'supabase-database'
    assert bundle['verified'] is True
    assert 'Zero LLM tokens consumed' in bundle['notice']
    
    # 12 skills must be present
    skills = bundle['artifacts']['skill_matrix']['skills']
    assert len(skills) == 12
    for s in skills:
        assert s['required_level'] >= 1
        assert s['bloom_code'] in {'CU', 'AP', 'AS', 'EV', 'CR'}
        assert s['skill_set_code'] in {'COD', 'DSA', 'OOD', 'APTI', 'COMM', 'AI', 'CLOUD', 'SQL', 'SWE', 'SYSD', 'NETW', 'OS'}

    # 4 hiring rounds must be structured
    rounds = bundle['artifacts']['hiring_rounds']['job_roles'][0]['hiring_rounds']
    assert len(rounds) == 4


def test_talent_check_against_supabase_company():
    # Test candidate against Swiggy (from Supabase)
    res = client.post('/api/talent-check', json={
        'candidate_id': 'ananya-rao',
        'company': 'Swiggy'
    })
    assert res.status_code == 200
    data = res.json()
    assert 0 <= data['readiness_score'] <= 100
    assert len(data['skillset_gap']) == 12
    assert data['verification']['verified'] is True
    assert data['verification']['mode'] == 'supabase-database'


def test_ai_interviewer_grounded_in_company_context():
    # Interview question generation for Uber
    res = client.post('/api/interview/start', json={
        'candidate_id': 'ananya-rao',
        'company': 'Uber',
        'round_name': 'Round 3: System Design & Architecture'
    })
    assert res.status_code == 200
    data = res.json()
    assert data['company'] in {'Uber', 'Uber Technologies, Inc.'}
    assert 'question' in data
    assert 'constraints' in data
    assert len(data['constraints']) >= 2
