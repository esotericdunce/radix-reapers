from pathlib import Path
import json, re
from typing import Any
from dotenv import load_dotenv

# Load backend/.env (provider keys, CORS, models) before anything reads the environment.
load_dotenv(Path(__file__).resolve().parents[1] / '.env')

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr, field_validator
from app.services.document_extractor import extract_document
from app.services.skill_extractor import extract_skills, CATEGORIES
from app.intelligence import agents as intel_agents
from app.intelligence import quality as intel_quality
from app.intelligence import store as intel_store
from app.intelligence import supabase_source as intel_supabase
from app.repositories.profile_repository import all_profiles, get_profile, save_profile, add_assessment, recent_assessments
from app.utils.scoring import readiness, match
from app.utils.skill_aliases import canonical_key

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'
def load_json(name, fallback):
    try: return json.loads((DATA/name).read_text(encoding='utf-8'))
    except Exception: return fallback
CANDIDATES=load_json('sample_candidates.json', [])
JOBS=load_json('sample_job_descriptions.json', [])
COMPANY_DATA=load_json('talent_check_company_skillsets.json', {"source":"Illustrative demo expectations","companies":{}})
app=FastAPI(title='RADIX TalentMatch API',version='1.0.0',description='Local-first, rule-based candidate readiness and job matching demo.')
origins=[x.strip() for x in __import__('os').getenv('CORS_ORIGINS','http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000').split(',')]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

class Profile(BaseModel):
    id: str|None=None
    name: str=Field(min_length=1,max_length=120)
    email: str|None=None
    education: list[str]=[]
    skills: list[dict[str,Any]]=[]
    projects: list[str]=[]
    hackathons: list[str]=[]
    internships: list[str]=[]
    certifications: list[str]=[]
    preferred_roles: list[str]=[]
    cv_file: str|None=None
    @field_validator('email')
    @classmethod
    def email_ok(cls,v):
        if v and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',v): raise ValueError('Enter a valid email address')
        return v
class MatchRequest(BaseModel):
    candidate_id: str
    job_description_id: str|None=None
    job_description: str|None=None
class TalentRequest(BaseModel):
    candidate_id: str
    company: str

class ResearchRequest(BaseModel):
    company: str = Field(min_length=2, max_length=80)
    providers: list[str] | None = None

def ensure_seed():
    existing={p['id'] for p in all_profiles()}
    for candidate in CANDIDATES:
        if candidate['id'] not in existing: save_profile(candidate)
ensure_seed()

def find_candidate(pid):
    profile=get_profile(pid)
    if not profile: raise HTTPException(404,'Candidate profile not found.')
    return profile

def infer_title(text):
    for line in text.splitlines()[:8]:
        if re.search(r'\b(engineer|analyst|scientist|developer|associate|manager|intern|designer)\b',line,re.I): return line.strip()[:120]
    return 'Not detected'

@app.get('/api/health')
def health(): return {'status':'ok','version':'1.0.0'}
@app.get('/api/candidates')
def candidates(): return all_profiles()
@app.get('/api/jobs')
def jobs(): return JOBS
@app.get('/api/companies')
def companies():
    base = list(COMPANY_DATA.get('companies', {}).keys())
    researched = [c['company'] for c in intel_store.verified_list()]
    sb_list = [c['name'] for c in intel_supabase.list_companies(limit=200)]
    all_c = sorted(list({c: True for c in (base + researched + sb_list)}.keys()), key=lambda x: x.lower())
    source_msg = f"Supabase verified dataset ({len(sb_list)} companies) + live AI research" if sb_list else COMPANY_DATA.get('source', 'Illustrative fallback data')
    return {'companies': all_c, 'source': source_msg, 'total_count': len(all_c), 'supabase_count': len(sb_list)}

@app.get('/api/assessments')
def assessments(limit: int=50): return recent_assessments(limit)

@app.post('/api/jd/analyze')
async def analyze_jd(file: UploadFile|None=File(default=None), text: str|None=Form(default=None)):
    if file:
        raw=await file.read(); content=extract_document(file.filename or '',raw); filename=file.filename
    elif text and text.strip(): content=text.strip(); filename='pasted-text'
    else: raise HTTPException(422,'Upload a PDF, DOCX, or TXT file, or provide job-description text.')
    from app.services.skill_extractor import extract_skills_semantic
    skills, method = extract_skills_semantic(content)
    known_c = list(COMPANY_DATA.get('companies', {}).keys()) + [c['company'] for c in intel_store.verified_list()] + ['Google', 'Microsoft', 'Oracle', 'Amazon', 'Meta', 'Apple', 'Netflix', 'Uber', 'Atlassian', 'Zomato', 'Swiggy', 'Flipkart', 'Blinkit', 'Juspay', 'Infosys', 'TCS', 'Wipro', 'Adobe', 'Cisco', 'Salesforce']
    company = next((c for c in dict.fromkeys(known_c) if re.search(rf'\b{re.escape(c)}\b', content, re.I)), 'Not detected')
    return {'title':infer_title(content),'company':company,'source_file':filename,'text':content,'required_skills':skills,'skill_categories':CATEGORIES,'method':method}

def extract_resume_sections(content: str) -> dict[str, list[str]]:
    """Robust multi-line section extraction for resumes (supports inline and block formats)."""
    headers = [
        ('education', r'(?:education|academic\s+background|qualifications)'),
        ('skills', r'(?:technical\s+skills|core\s+skills|skills|technologies)'),
        ('projects', r'(?:personal\s+projects|academic\s+projects|technical\s+projects|projects)'),
        ('internships', r'(?:work\s+experience|professional\s+experience|internships|experience|employment)'),
        ('hackathons', r'(?:hackathons|competitions|coding\s+contests)'),
        ('certifications', r'(?:licenses\s+and\s+certifications|certifications|certificates|courses)'),
        ('preferred_roles', r'(?:preferred\s+roles|target\s+roles|objective|career\s+objective)'),
    ]
    results = {k: [] for k, _ in headers}

    for key, pattern in headers:
        m = re.search(rf'{pattern}\s*:\s*([^\n]+)', content, re.I)
        if m:
            results[key] = [x.strip() for x in re.split(r'[,;|]', m.group(1)) if x.strip()]

    lines = content.splitlines()
    current_key = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        matched_header = None
        for key, pattern in headers:
            if re.match(rf'^(?:#+|\*+)?\s*{pattern}\s*:?$', stripped, re.I):
                matched_header = key
                break
        if matched_header:
            current_key = matched_header
            continue
        if current_key and not results[current_key]:
            clean_item = re.sub(r'^[•\-\*–\d\.\)]\s*', '', stripped).strip()
            if clean_item and len(clean_item) > 2 and not any(re.match(rf'^(?:#+|\*+)?\s*{p}\s*:?$', clean_item, re.I) for _, p in headers):
                results[current_key].append(clean_item)
                if len(results[current_key]) >= 8:
                    current_key = None

    return results

@app.post('/api/resume/parse')
async def parse_resume(file: UploadFile|None=File(default=None), text: str|None=Form(default=None)):
    if file: content=extract_document(file.filename or '',await file.read()); filename=file.filename
    elif text and text.strip(): content=text.strip(); filename='pasted-text'
    else: raise HTTPException(422,'Upload a PDF, DOCX, or TXT file, or provide resume text.')
    name=next((line.strip() for line in content.splitlines()[:6] if line.strip() and '@' not in line and not re.search(r'^(resume|curriculum vitae)',line.strip(),re.I)),'Not detected')
    emails=re.findall(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',content,re.I)
    sections = extract_resume_sections(content)
    from app.services.skill_extractor import extract_skills_semantic
    skills, method = extract_skills_semantic(content)
    return {'name':name,'email':emails[0] if emails else None,'education':sections['education'],'skills':[dict(s,level=5) for s in skills],'projects':sections['projects'],'hackathons':sections['hackathons'],'internships':sections['internships'],'certifications':sections['certifications'],'preferred_roles':sections['preferred_roles'],'cv_file':filename,'evidence':content[:500],'method':method}

@app.get('/api/profile')
def profile_get(candidate_id: str|None=None):
    items=all_profiles()
    if candidate_id: return find_candidate(candidate_id)
    return items[0] if items else None
@app.get('/api/profiles')
def profiles_get(): return all_profiles()
@app.post('/api/profile')
def profile_create(body: Profile):
    data=body.model_dump(); data['id']=data.get('id') or re.sub(r'[^a-z0-9]+','-',data['name'].lower()).strip('-')
    if get_profile(data['id']): raise HTTPException(409,'Profile ID already exists; use PUT to update it.')
    save_profile(data); return data
@app.put('/api/profile')
def profile_update(body: Profile, candidate_id: str|None=None):
    data=body.model_dump(); data['id']=candidate_id or data.get('id')
    if not data['id']: raise HTTPException(422,'Profile id or candidate_id is required for update.')
    if not get_profile(data['id']): raise HTTPException(404,'Profile not found; use POST to create it.')
    save_profile(data); return data

@app.post('/api/talent-check')
def talent_check(body: TalentRequest):
    profile=find_candidate(body.candidate_id)
    requirements=COMPANY_DATA.get('companies',{}).get(body.company)
    source_note=COMPANY_DATA.get('source')
    bundle=None
    candidates=[c for c in intel_store.verified_list() if c['company'].lower()==body.company.lower()]
    if candidates:
        bundle=intel_store.load_research(candidates[0]['company'])
        matrix=(bundle or {}).get('artifacts',{}).get('expectation_matrix') or {}
        tokens = matrix.get('tokens') or {}
        if tokens:
            requirements=[]
            for col,t in tokens.items():
                code={'coding':'COD','data_structures_and_algorithms':'DSA','object_oriented_programming_and_design':'OOD','aptitude_and_problem_solving':'APTI','communication_skills':'COMM','ai_native_engineering':'AI','devops_and_cloud':'CLOUD','sql_and_design':'SQL','software_engineering':'SWE','system_design_and_architecture':'SYSD','computer_networking':'NETW','operating_system':'OS'}.get(col,col)
                requirements.append({'skill_name':col.replace('_',' ').title(),'category_code':code,'required_level':t.get('level') or 5})
        elif (bundle or {}).get('artifacts',{}).get('skill_matrix'):
            sm = bundle['artifacts']['skill_matrix']
            requirements = [{'skill_name': s['skill_name'], 'category_code': s.get('skill_set_code', 'OTHER'), 'required_level': s.get('required_level', 5)} for s in sm.get('skills', [])]
    if not bundle:
        sb_bundle = intel_supabase.build_bundle_from_supabase(body.company)
        if sb_bundle:
            intel_store.save_artifacts(body.company, sb_bundle)
            bundle = sb_bundle
            matrix = (bundle or {}).get('artifacts', {}).get('expectation_matrix') or {}
            tokens = matrix.get('tokens') or {}
            if tokens:
                requirements = []
                for col, t in tokens.items():
                    code = {'coding':'COD','data_structures_and_algorithms':'DSA','object_oriented_programming_and_design':'OOD','aptitude_and_problem_solving':'APTI','communication_skills':'COMM','ai_native_engineering':'AI','devops_and_cloud':'CLOUD','sql_and_design':'SQL','software_engineering':'SWE','system_design_and_architecture':'SYSD','computer_networking':'NETW','operating_system':'OS'}.get(col, col)
                    requirements.append({'skill_name': col.replace('_', ' ').title(), 'category_code': code, 'required_level': t.get('level') or 5})
                source_note = f"Verified hiring bar from team's Supabase dataset ({bundle.get('company')})."

    if requirements is None:
        fallback_m = intel_store.fallback_expectation_matrix(body.company, COMPANY_DATA)
        requirements = []
        for col, t in (fallback_m.get('tokens') or {}).items():
            code = {'coding':'COD','data_structures_and_algorithms':'DSA','object_oriented_programming_and_design':'OOD','aptitude_and_problem_solving':'APTI','communication_skills':'COMM','ai_native_engineering':'AI','devops_and_cloud':'CLOUD','sql_and_design':'SQL','software_engineering':'SWE','system_design_and_architecture':'SYSD','computer_networking':'NETW','operating_system':'OS'}.get(col,col)
            requirements.append({'skill_name': col.replace('_',' ').title(), 'category_code': code, 'required_level': t.get('level') or 5})
        source_note = f'Heuristic baseline for {body.company}; research with LLM agents for verified criteria.'

    score,gaps=readiness(profile,requirements)
    response={'candidate_id':body.candidate_id,'company':body.company,'expectations_source':source_note,'readiness_score':score,'skillset_gap':gaps,'recommendations':[f"Improve {g['skill_name']} by {g['gap']} level(s)." for g in sorted(gaps,key=lambda x:x['gap'],reverse=True) if g['gap']>0][:5]}
    if bundle:
        q=bundle.get('quality',{})
        response['verification']={'verified':bool(bundle.get('verified')),'mode':bundle.get('mode'),'researched_at':bundle.get('researched_at'),'quality_errors':q.get('errors',0),'quality_warnings':q.get('warnings',0),'consensus_sources':len(bundle.get('providers_used') or []),'conflicts':[],'langgraph':bundle.get('langgraph',False)}
        if bundle.get('mode') == 'supabase-database':
            response['expectations_source'] = f"Verified enterprise benchmark from team's Supabase dataset ({bundle.get('company')})"
        elif bundle.get('mode') == 'llm-research':
            response['expectations_source'] = 'LLM agent research · consensus across sources'
        else:
            response['expectations_source'] = 'Bundled offline snapshot · not researched'
    add_assessment('readiness',body.candidate_id,profile['name'],body.company,score)
    return response

@app.post('/api/skill-match')
def skill_match(body: MatchRequest):
    profile=find_candidate(body.candidate_id)
    if body.job_description_id:
        jd=next((j for j in JOBS if j['id']==body.job_description_id),None)
        if jd is None: raise HTTPException(404,'Job description not found.')
        text=jd['text']; source=jd['id']; title=jd['title']
    elif body.job_description and body.job_description.strip(): text=body.job_description.strip(); source='supplied-text'; title=infer_title(text)
    else: raise HTTPException(422,'Provide job_description_id or job_description text.')
    skills=extract_skills(text)
    score,matched,missing,recommendations=match(profile,skills)
    add_assessment('match',body.candidate_id,profile['name'],title,score)
    matched_keys={canonical_key(s['skill_name']) for s in matched}
    categories={}
    for code,label in CATEGORIES.items():
        subset=[s for s in skills if s['category_code']==code]
        if subset: categories[code]={'label':label,'required':len(subset),'matched':sum(1 for s in subset if canonical_key(s['skill_name']) in matched_keys)}
    return {'candidate_id':body.candidate_id,'jd_source_file':source,'job_title':title,'match_score':score,'matched_skills':matched,'missing_skills':missing,'category_breakdown':categories,'recommendations':recommendations,'method':'Matched required skill phrases / total extracted required skill phrases × 100.'}

# ---------------------------------------------------------------- intelligence

@app.get('/api/intelligence/status')
def intelligence_status():
    """Provider availability + researchable/snapshot state, for the UI banner."""
    return {'providers':intel_agents.providers.provider_status(),'verified_companies':intel_store.verified_list(),'bundled':list(intel_store.snapshot_files().keys()),'supabase_configured':intel_supabase.supabase_configured()}

@app.get('/api/intelligence/supabase/companies')
def intelligence_supabase_companies(limit: int = 100):
    """Read-only snapshot of company_json from the team's Supabase project
    (set SUPABASE_URL + SUPABASE_ANON_KEY env). Empty list when unconfigured."""
    return {'configured':intel_supabase.supabase_configured(),'companies':intel_supabase.list_companies(limit)}

@app.get('/api/intelligence/companies')
def intelligence_companies():
    local = intel_store.verified_list()
    sb_comps = intel_supabase.list_companies(limit=200)
    all_names = sorted(list({c['company']: True for c in local} | {c['name']: True for c in sb_comps}.keys()), key=lambda x: x.lower())
    return {'companies': all_names, 'detail': local, 'supabase_count': len(sb_comps)}

@app.post('/api/intelligence/research')
def intelligence_research(body: ResearchRequest):
    """Run the Supabase-first research pipeline (instant DB golden load or multi-agent LLM consensus)."""
    return intel_agents.run_pipeline(body.company, body.providers)

@app.get('/api/intelligence/company/{company_name}')
def intelligence_company(company_name: str):
    bundle=intel_store.load_research(company_name)
    if not bundle:
        sb_bundle = intel_supabase.build_bundle_from_supabase(company_name)
        if sb_bundle:
            intel_store.save_artifacts(company_name, sb_bundle)
            return sb_bundle
        raise HTTPException(404,'No research bundle for this company yet. Run /api/intelligence/research first.')
    return bundle


# --------------------------------------------------- differentiators: committee & interview

class CommitteeRequest(BaseModel):
    candidate_id: str
    company: str
    role_title: str = "Software Engineer"
    job_description: str | None = None

class InterviewStartRequest(BaseModel):
    candidate_id: str
    company: str
    round_name: str = "Round 2: Technical Interview"

class InterviewEvalRequest(BaseModel):
    candidate_id: str
    company: str
    round_name: str
    question: str
    answer: str
    apply_upgrade: bool = False

class TailorRequest(BaseModel):
    skill_name: str
    target_company: str = "Google"
    target_bloom: str = "EV"

@app.post('/api/committee/deliberate')
def committee_deliberate(body: CommitteeRequest):
    candidate = find_candidate(body.candidate_id)
    from app.intelligence.committee_agent import deliberate_candidate
    result = deliberate_candidate(candidate, body.company, body.role_title, body.job_description)
    add_assessment('committee', body.candidate_id, candidate['name'], f"{body.company} (HC)", result.get('consensus_score', 75))
    return result

@app.post('/api/interview/start')
def interview_start(body: InterviewStartRequest):
    candidate = find_candidate(body.candidate_id)
    from app.intelligence.interview_agent import generate_interview_question
    return generate_interview_question(body.company, body.round_name, candidate)

@app.post('/api/interview/evaluate')
def interview_evaluate(body: InterviewEvalRequest):
    candidate = find_candidate(body.candidate_id)
    from app.intelligence.interview_agent import evaluate_interview_answer
    result = evaluate_interview_answer(body.company, body.round_name, body.question, body.answer, candidate)
    
    if body.apply_upgrade and result.get('recommended_profile_level'):
        skill_to_up = result.get('suggested_skill_to_update', 'System Design & Architecture')
        new_lvl = result['recommended_profile_level']
        updated_skills = []
        found = False
        for s in candidate.get('skills', []):
            if s.get('skill_name', '').lower() == skill_to_up.lower():
                s['level'] = max(int(s.get('level', 0)), new_lvl)
                s['evidence'] = f"Verified in AI Mock Interview ({body.company} {body.round_name}) with Bloom {result.get('bloom_achieved', 'EV')} depth."
                found = True
            updated_skills.append(s)
        if not found:
            updated_skills.append({
                'skill_name': skill_to_up,
                'category_code': 'SYSD',
                'level': new_lvl,
                'evidence': f"Assessed in AI Mock Interview ({body.company})."
            })
        candidate['skills'] = updated_skills
        save_profile(candidate)
        result['profile_updated'] = True
    
    add_assessment('interview', body.candidate_id, candidate['name'], f"{body.company} ({body.round_name})", int(result.get('score', 7)) * 10)
    return result

@app.get('/api/career/radar')
def career_radar(candidate_id: str):
    candidate = find_candidate(candidate_id)
    from app.intelligence.career_radar import compute_career_radar
    return compute_career_radar(candidate)

@app.post('/api/resume/tailor-bullet')
def tailor_bullet(body: TailorRequest):
    from app.intelligence.career_radar import tailor_resume_bullet
    return tailor_resume_bullet(body.skill_name, body.target_company, body.target_bloom)


# -------------------------------------------------------------- static spa mount

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST_DIR = ROOT / 'frontend' / 'dist'
if DIST_DIR.exists():
    app.mount('/assets', StaticFiles(directory=str(DIST_DIR / 'assets')), name='assets')

    @app.api_route('/{full_path:path}', methods=['GET', 'HEAD'])
    async def serve_spa(full_path: str):
        if full_path.startswith('api'):
            raise HTTPException(404, 'API endpoint not found')
        target = DIST_DIR / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(DIST_DIR / 'index.html')
