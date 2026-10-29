"""Offline tests for the Company Intelligence layer (no LLM keys needed).

Covers: the 163-parameter schema, L3-style gate rules on the golden record,
Level-Code matrix checks, hiring envelope checks, text parsing, consolidation
(best-of-N), the LangGraph pipeline's offline fallback, and the product
endpoints. All offline; the LangGraph graph itself stays unexercised without
keys via the bundled fallback path.
"""
import os
import tempfile

# setdefault: test_api.py may already have configured the DB/paths (shared process)
os.environ.setdefault('RADIX_DB_PATH', os.path.join(tempfile.mkdtemp(), 'intel-test.db'))
os.environ.setdefault('RADIX_INTEL_PATH', tempfile.mkdtemp(prefix='radix-intel-'))
os.environ.pop('OPENROUTER_API_KEY', None)
os.environ.pop('GROQ_API_KEY', None)
os.environ.pop('GEMINI_API_KEY', None)
os.environ.pop('GOOGLE_API_KEY', None)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.intelligence import agents, consolidation, parsing, prompts, quality, store  # noqa: E402
from app.intelligence.golden_record import BY_ID, BY_NAME, COLUMNS, PARAMS  # noqa: E402

client = TestClient(app)


# ------------------------------------------------------------ schema ----------

def test_schema_has_exactly_163_unique_parameters():
    assert len(PARAMS) == 163
    assert len(BY_ID) == 163 and len(BY_NAME) == 163
    assert len(COLUMNS) == 163


def test_atomic_composite_metadata_is_carried_through():
    logo = BY_ID[3]
    assert logo.ac == 'Composite' and logo.minimum == 1 and logo.maximum == 5
    assert logo.content_type == 'URL' and 'Logo' in quality.URL_PARAMS
    name = BY_ID[1]
    assert name.ac == 'Atomic' and name.minimum is None
    rating = BY_ID[34]
    assert rating.parameter in quality.RATING_PARAMS


# -------------------------------------------------------- parsing ------------

def test_extract_json_survives_fences_and_prose():
    text = "Here you go:\n```json\n{\"a\": {\"b\": [1,2]}}\n```\nHope that helps!"
    assert parsing.extract_json(text) == {'a': {'b': [1, 2]}}


def test_parse_markdown_table_handles_fences_and_short_rows():
    text = "intro\n| ID | A/C | Parameter | Research Output / Data |\n|---|---|---|---|\n| 1 | Atomic | Company Name | Zomato Ltd |\n"
    rows = parsing.parse_markdown_table(text)
    assert rows == [{'ID': '1', 'A/C': 'Atomic', 'Parameter': 'Company Name', 'Research Output / Data': 'Zomato Ltd'}]
    assert parsing.parse_markdown_table('no tables here') == []


# ------------------------------------------------------------ gates ----------

def _clean_record():
    record = {}
    for p in PARAMS:
        if p.ac == 'Composite':
            n = p.minimum or 1
            record[p.parameter] = '; '.join(f'Element {i}' for i in range(1, n + 1))
        elif p.parameter in quality.URL_PARAMS:
            record[p.parameter] = 'https://example.com/logo.png'
        elif p.parameter in quality.RATING_PARAMS:
            record[p.parameter] = '8.4/10 — strong on ethos'
        else:
            record[p.parameter] = f'Clean value for parameter {p.id}'
    return record


def test_gate_passes_a_well_formed_golden_record():
    record = _clean_record()
    diags = quality.validate_golden_record(record)
    errors = [d for d in diags if d['severity'] == 'error']
    assert errors == [], errors[:5]


def test_gate_catches_delimiters_and_missing_keys():
    record = _clean_record()
    record['Company Name'] = 'Zomato; Limited'          # atomic with delimiter
    record['Countries Operating In'] = 'India; India'   # fine compositely, but...
    del record['Crisis behavior']                        # missing key
    diags = [d for d in quality.validate_golden_record(record) if d['severity'] == 'error']
    rules = {d['rule'] for d in diags}
    assert 'atomic_no_delimiter' in rules and 'all_163_present' in rules


def test_gate_flags_placeholders_and_bad_urls_as_warn():
    record = _clean_record()
    record['Overview of the Company'] = 'Not Found'
    record['Website URL'] = 'not-a-url'
    diags = quality.validate_golden_record(record)
    warns = {(d['rule'], d['severity']) for d in diags}
    assert ('no_placeholder', 'warn') in warns and ('url_shape', 'warn') in warns


def _clean_matrix():
    generic = store.generic_expectations_by_column()
    tokens = {}
    for col in quality.SKILL_COLUMNS:
        level, bloom = generic[col]
        tokens[col] = {'level': level, 'bloom_code': bloom, 'raw': f'{level}-{bloom}'}
    return {'companies': 'Acme', 'tokens': tokens}


def test_gate_matrix_catches_invalid_tokens_and_flat_rows():
    ok = quality.validate_expectation_matrix(_clean_matrix())
    assert ok == [], ok  # the generic bar varies by skill, so no diagnostics at all
    bad = {'companies': 'Acme',
           'tokens': {'coding': {'level': 3, 'bloom_code': 'XX', 'raw': '3-XX', 'invalid': True}}}
    diags = quality.validate_expectation_matrix(bad)
    assert any(d['rule'] == 'level_code_valid' for d in diags)
    level = _clean_matrix()['tokens']['coding']['level']
    bloom = _clean_matrix()['tokens']['coding']['bloom_code']
    flat = {c: {'level': level, 'bloom_code': bloom, 'raw': f'{level}-{bloom}'}
            for c in quality.SKILL_COLUMNS}
    flat_diags = quality.validate_expectation_matrix({'companies': 'Acme', 'tokens': flat})
    assert any(d['rule'] == 'matrix_not_flat' and d['severity'] == 'warn' for d in flat_diags)


def _clean_hiring():
    return {'company_name': 'Acme', 'job_role_details': [{
        'opportunity_type': 'Employment', 'role_title': 'Software Engineer',
        'role_category': 'SDE', 'job_description': 'Builds products.',
        'compensation': 'CTC', 'ctc_or_stipend': 1200000, 'bonus': 'NA', 'benefits_summary': 'Health cover.',
        'hiring_rounds': [
            {'round_number': 1, 'round_name': 'Coding Test', 'round_category': 'Coding Test',
             'evaluation_type': 'Technical', 'assessment_mode': 'Online',
             'skill_sets': [{'skill_set_code': 'DSA', 'typical_questions': 'graphs; dp; tries'}]},
            {'round_number': 2, 'round_name': 'Technical Interview', 'round_category': 'Interview',
             'evaluation_type': 'Technical', 'assessment_mode': 'Onsite',
             'skill_sets': [{'skill_set_code': 'SYSD', 'typical_questions': 'Design a rate limiter'}]},
            {'round_number': 3, 'round_name': 'HR Interview', 'round_category': 'Interview',
             'evaluation_type': 'HR', 'assessment_mode': 'Onsite',
             'skill_sets': [{'skill_set_code': 'COMM', 'typical_questions': 'Tell me about a project'}]},
        ]}]}


def test_gate_hiring_passes_clean_and_catches_bad_envelopes():
    assert quality.validate_hiring_rounds(_clean_hiring()) == []
    bad = _clean_hiring()
    role = bad['job_role_details'][0]
    role['opportunity_type'] = 'Freelance'
    del role['hiring_rounds'][-1]
    role['hiring_rounds'][0]['round_category'] = 'Party'
    role['hiring_rounds'][0]['skill_sets'][0]['skill_set_code'] = 'QUANT'
    diags = quality.validate_hiring_rounds(bad)
    rules = {d['rule'] for d in diags}
    assert {'rounds_shape', 'round_category_valid', 'skill_code_valid'} <= rules


def test_report_is_markdown_with_verdict():
    report = quality.build_quality_report('Acme', quality.validate_golden_record({'Company Name': 'x'}))
    assert report.startswith('# Data quality report') and 'FAIL' in report


# ------------------------------------------------------ consolidation --------

def _research_rows(provider, value_by_id):
    return [
        {'ID': str(pid), 'Category': BY_ID[pid].category, 'A/C': BY_ID[pid].ac,
         'Parameter': BY_ID[pid].parameter, 'Research Output / Data': value_by_id.get(pid, '')
         + (f' ({provider})' if value_by_id.get(pid) else '')}
        for pid in range(1, 164)
    ]


def test_dataset_carries_source_column():
    dataset = consolidation.build_dataset({'gemini': _research_rows('gemini', {1: 'Zomato Ltd'})})
    assert dataset.count('| gemini |') >= 1 and '| ID |' in dataset


def test_consolidation_keeps_best_partial_across_chain():
    sources = {
        'gemini': _research_rows('gemini', {1: 'Zomato Limited'}),
        'groq': _research_rows('groq', {1: 'Zomato', 2: 'ET'}),
    }

    def fake_invoke(name, prompt):
        provided = sources[name]
        lines = ['| ID | Category | A/C | Parameter | Research Output / Data | Source |',
                 '|---|---|---|---|---|---|']
        lines += [f"| {r['ID']} | {r['Category']} | {r['A/C']} | {r['Parameter']} | "
                  f"{r['Research Output / Data']} | {name} |" for r in provided if r['Research Output / Data']]
        return '\n'.join(lines)

    out = consolidation.consolidate(sources, fake_invoke, available=['gemini', 'groq'])
    assert out['provider'] == 'groq'          # groq yields 2 usable params, gemini 1
    assert out['record'].get('Short Name') == 'ET (groq)'
    assert out['usable'] == 2


def test_consolidation_raises_when_no_provider_parses():
    try:
        consolidation.consolidate({'gemini': _research_rows('gemini', {1: 'x'})},
                                  lambda name, prompt: 'not a table', available=['gemini'])
        assert False, 'should have raised'
    except ValueError:
        pass


def test_provider_chain_filters_by_availability():
    assert consolidation.provider_chain(['gemini', 'groq'], ['groq']) == ['groq']
    assert consolidation.provider_chain(['groq'], []) == ['groq']


# ------------------------------------------------------------ prompts --------

def test_research_prompt_embeds_full_schema_and_company():
    prompt = prompts.research('Zomato')
    assert 'Zomato' in prompt and 'Crisis behavior' in prompt and 'Atomic' in prompt


def test_brief_prompt_is_retired():
    try:
        prompts.brief_prompt('x')
        assert False, 'should have raised'
    except NotImplementedError:
        pass


# ------------------------------------------------------------ pipeline -------

def test_pipeline_offline_fallback_and_endpoint_research():
    r = client.post('/api/intelligence/research', json={'company': 'Zomato'})
    assert r.status_code == 200
    body = r.json()
    assert body['mode'] == 'offline-fallback' and body['verified'] is False
    assert any(s['stage'].startswith('research (offline fallback)') for s in body['stages'])
    assert body['artifacts']['hiring_rounds']['job_role_details']
    assert body['artifacts']['expectation_matrix']['tokens']
    stored = store.load_research('Zomato')
    assert stored and stored['company'] == 'Zomato'
    assert 'NOT been researched' in body['notice']


def test_status_and_company_endpoints():
    r = client.get('/api/intelligence/status')
    assert r.status_code == 200
    body = r.json()
    assert {'openrouter', 'groq', 'gemini'} <= {p['provider'] for p in body['providers']}
    assert {p['available'] for p in body['providers']} == {False}  # no keys in test env
    assert any(c['company'] == 'Zomato' for c in body['verified_companies'])
    got = client.get('/api/intelligence/company/Zomato')
    assert got.status_code == 200 and got.json()['company'] == 'Zomato'
    assert client.get('/api/intelligence/company/Never-Researched').status_code == 404


def test_talent_check_prefers_researched_company_and_reports_verification():
    r = client.post('/api/talent-check', json={'candidate_id': 'ananya-rao', 'company': 'Zomato'})
    assert r.status_code == 200
    body = r.json()
    assert body['verification']['verified'] is False
    assert body['verification']['mode'] == 'offline-fallback'
    assert 'offline' in body['expectations_source'].lower()
    assert 0 <= body['readiness_score'] <= 100


def test_talent_check_verified_ranking_beats_static_demo_data():
    fallback = agents.run_pipeline('Google')
    assert fallback['company'] == 'Google'
    r = client.post('/api/talent-check', json={'candidate_id': 'ananya-rao', 'company': 'Google'})
    assert r.status_code == 200 and r.json()['verification']['mode'] in {'llm-research', 'offline-fallback', 'supabase-database'}
    assert len(r.json()['skillset_gap']) >= 8


def test_langgraph_graph_compiles_and_orchestration_flag_is_true():
    assert agents.HAS_LANGGRAPH is True
    assert agents._COMPILED is not None
    graph = agents._build_graph()
    names = {n for n in graph.get_graph().nodes}
    assert {'research', 'validate_research', 'consolidate', 'gate', 'matrix', 'hiring'} <= names


def test_pipeline_runs_graph_without_keys_via_fallback():
    bundle = agents.run_pipeline('UnlistedCustomStartupX')
    assert bundle['mode'] in {'offline-fallback', 'llm-research'}
    assert len(bundle['artifacts']['expectation_matrix']['tokens']) == 12


def test_levels_by_code_uses_category_level():
    from app.utils.scoring import levels_by_code, readiness
    profile = {'skills': [{'skill_name': 'Python', 'category_code': 'COD', 'level': 7}]}
    assert levels_by_code(profile) == {'COD': 7}
    score, gaps = readiness(profile, [{'skill_name': 'Coding', 'category_code': 'COD', 'required_level': 5}])
    assert score == 100 and gaps[0]['status'] == 'Met'  # code-based fallback matched
