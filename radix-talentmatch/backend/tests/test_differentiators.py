from fastapi.testclient import TestClient
from app.main import app
from app.repositories.profile_repository import get_profile

client = TestClient(app)

def test_hiring_committee_deliberation():
    response = client.post("/api/committee/deliberate", json={
        "candidate_id": "ananya-rao",
        "company": "Google",
        "role_title": "Software Engineer"
    })
    assert response.status_code == 200
    data = response.json()
    assert "consensus_verdict" in data
    assert "consensus_score" in data
    assert isinstance(data["consensus_score"], (int, float))
    assert len(data["personas"]) == 3
    for persona in data["personas"]:
        assert persona["name"]
        assert persona["role"]
        assert persona["vote"]
        assert persona["stance"]
        assert persona["key_concern"]
        assert persona["key_endorsement"]

    assert len(data["conditions_to_hire"]) > 0

def test_interview_arena_question_and_evaluation():
    # 1. Start question
    start_res = client.post("/api/interview/start", json={
        "candidate_id": "ananya-rao",
        "company": "Google",
        "round_name": "Round 2: Technical Interview"
    })
    assert start_res.status_code == 200
    q_data = start_res.json()
    assert "question" in q_data
    assert "interviewer_role" in q_data
    assert "target_bloom" in q_data
    assert "hints" in q_data

    # 2. Evaluate answer
    eval_res = client.post("/api/interview/evaluate", json={
        "candidate_id": "ananya-rao",
        "company": "Google",
        "round_name": "Round 2: Technical Interview",
        "question": q_data["question"],
        "answer": "I would design a partitioned event stream using consistent hashing on message keys, backed by RocksDB for local state stores and Raft consensus across 3 replicas for partition fault tolerance. Downstream consumers maintain idempotency via deduplication filters with Redis Bloom filters.",
        "apply_upgrade": True
    })
    assert eval_res.status_code == 200
    e_data = eval_res.json()
    assert "score" in e_data
    assert "verdict" in e_data
    assert "bloom_achieved" in e_data
    assert len(e_data["strengths"]) > 0
    assert "ideal_answer_takeaway" in e_data
    assert e_data.get("profile_updated") is True

    # Check candidate profile was updated in repository with the suggested skill
    profile = get_profile("ananya-rao")
    assert profile is not None
    skill_names = [s.get("skill_name", "").lower() for s in profile.get("skills", [])]
    suggested = e_data.get("suggested_skill_to_update", "").lower()
    assert any(suggested in s or s in suggested for s in skill_names)

def test_career_radar_endpoint():
    res = client.get("/api/career/radar?candidate_id=ananya-rao")
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == "ananya-rao"
    assert "overall_placement_tier" in data
    assert "tiers" in data
    assert "super_dream" in data["tiers"]
    assert "dream" in data["tiers"]
    assert "standard" in data["tiers"]
    
    super_dream = data["tiers"]["super_dream"]
    assert "readiness_score" in super_dream
    assert "status" in super_dream
    assert len(super_dream["representative_companies"]) > 0

    assert len(data["roi_skill_jumps"]) > 0
    first_jump = data["roi_skill_jumps"][0]
    assert "skill" in first_jump
    assert "estimated_ctc_boost" in first_jump
    assert "unlocked_tier" in first_jump

def test_resume_tailor_bullet_endpoint():
    res = client.post("/api/resume/tailor-bullet", json={
        "skill_name": "System Design & Architecture",
        "target_company": "Google",
        "target_bloom": "EV"
    })
    assert res.status_code == 200
    data = res.json()
    assert "ats_bullet" in data
    assert "xyz_breakdown" in data
    assert data["xyz_breakdown"]["accomplished_x"]
    assert data["xyz_breakdown"]["measured_by_y"]
    assert data["xyz_breakdown"]["done_by_z"]
    assert "micro_project_blueprint" in data
    blueprint = data["micro_project_blueprint"]
    assert "project_title" in blueprint
    assert "github_repo_slug" in blueprint
    assert len(blueprint["deliverables"]) >= 3
