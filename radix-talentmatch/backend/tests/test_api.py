import os, tempfile
os.environ['RADIX_DB_PATH']=os.path.join(tempfile.mkdtemp(),'test.db')
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health(): assert client.get('/api/health').json()['status']=='ok'
def test_jd_analysis_text():
 r=client.post('/api/jd/analyze',data={'text':'Google Software Engineer\nPython, SQL and Data Structures and Algorithms required'})
 assert r.status_code==200 and r.json()['company']=='Google' and len(r.json()['required_skills'])>=3
def test_unsupported_document(): assert client.post('/api/jd/analyze',files={'file':('bad.exe',b'x')}).status_code==415
def test_empty_input(): assert client.post('/api/jd/analyze',data={'text':' '}).status_code==422
def test_resume_parse():
 r=client.post('/api/resume/parse',data={'text':'Ananya Rao\nEmail: ananya@example.com\nSkills: Python, SQL\nProjects: Demo app'})
 assert r.status_code==200 and r.json()['email']=='ananya@example.com' and r.json()['skills']
def test_profile_create_read_update():
 payload={'id':'test-person','name':'Test Person','email':'test@example.com','skills':[]}
 assert client.post('/api/profile',json=payload).status_code==200
 assert client.get('/api/profile',params={'candidate_id':'test-person'}).json()['name']=='Test Person'
 payload['projects']=['Edited']; assert client.put('/api/profile',json=payload).json()['projects']==['Edited']
def test_talent_score_valid():
 r=client.post('/api/talent-check',json={'candidate_id':'ananya-rao','company':'Google'})
 assert r.status_code==200 and 0<=r.json()['readiness_score']<=100 and r.json()['skillset_gap']
def test_match_candidate_and_jd_differ():
 a=client.post('/api/skill-match',json={'candidate_id':'ananya-rao','job_description_id':'google-ds'}).json()
 b=client.post('/api/skill-match',json={'candidate_id':'karthik-subramaniam','job_description_id':'google-ds'}).json()
 c=client.post('/api/skill-match',json={'candidate_id':'ananya-rao','job_description_id':'oracle-support'}).json()
 assert 0<=a['match_score']<=100 and a['match_score']!=b['match_score'] and a['match_score']!=c['match_score']
 assert a['missing_skills']
def test_unknown_job(): assert client.post('/api/skill-match',json={'candidate_id':'ananya-rao','job_description_id':'nope'}).status_code==404


def test_skill_aliases_match_but_related_skills_stay_distinct():
 from app.services.skill_extractor import extract_skills
 from app.utils.scoring import match
 aliases=extract_skills('DSA, OOP, JS, and ML')
 assert {s['skill_name'] for s in aliases}=={'Data Structures and Algorithms','Object-Oriented Programming','JavaScript','Machine Learning'}
 profile={'skills':[{'skill_name':'DSA','level':7,'evidence':'Practiced graph problems'},{'skill_name':'OOP','level':6,'evidence':'Built a small app'}]}
 required=[{'skill_name':'Data Structures and Algorithms','category_code':'DSA','evidence':'DSA required'},{'skill_name':'Object-Oriented Programming','category_code':'OOD','evidence':'OOP required'}]
 score,matched,missing,_=match(profile,required)
 assert score==100 and len(matched)==2 and not missing
 unrelated={'skills':[{'skill_name':'Java','level':8,'evidence':'Java project'},{'skill_name':'React','level':8,'evidence':'React interface'}]}
 score,matched,missing,_=match(unrelated,[{'skill_name':'JavaScript','category_code':'COD','evidence':'JS required'},{'skill_name':'Machine Learning','category_code':'AI','evidence':'ML required'}])
 assert score==0 and not matched and len(missing)==2

def test_assessment_history_logs_real_results():
 result=client.post('/api/skill-match',json={'candidate_id':'ananya-rao','job_description_id':'google-ds'}).json()
 history=client.get('/api/assessments').json()
 assert history and history[0]['type']=='match'
 assert history[0]['candidate_id']=='ananya-rao' and history[0]['target']==result['job_title']
 assert history[0]['score']==result['match_score'] and history[0]['timestamp']
 assert client.get('/api/assessments',params={'limit':0}).status_code==200


def test_detected_skill_without_rating_is_unassessed():
 from app.utils.scoring import match, readiness
 profile={'skills':[{'skill_name':'Python','category_code':'COD','evidence':'Found in resume text'}]}
 requirement={'skill_name':'Python','category_code':'COD','evidence':'Required Python'}
 score,matched,missing,_=match(profile,[requirement])
 assert score==0 and not matched and len(missing)==1
 readiness_score,gaps=readiness(profile,[{'skill_name':'Python','category_code':'COD','required_level':5}])
 assert readiness_score==0 and gaps[0]['status']=='Missing'
