// @ts-nocheck, legacy RADIX screen ported as-is; typed against the original lax tsconfig.
import{useCallback,useEffect,useState}from'react';
import{ElevatedCard}from'@cred/neopop-web/lib/components';
import {AlertTriangle,CheckCircle2,ChevronDown,Clock3,Landmark,LoaderCircle,Radar,RefreshCw,ShieldCheck,ArrowRight,XCircle} from 'lucide-react';
import{api}from'../services/api';
import type{IntelBundle,IntelDiag,IntelStatus,IntelSkill,IntelMatrix,IntelHiring,IntelRole,IntelBrief}from'../types';

const BLOOM_META:Record<string,{label:string;color:string}>={
 CU:{label:'Conceptual',color:'#86CFEA'},
 AP:{label:'Application',color:'#4FD6A2'},
 AS:{label:'Analysis & Synthesis',color:'#F2C14E'},
 EV:{label:'Evaluation',color:'#F28B6E'},
 CR:{label:'Creation',color:'#A07CF7'},
};
const TIER_COLORS=["#A07CF7","#86CFEA","#4FD6A2","#F2C14E","#F28B6E","#7CD4F0"];

export function CompanyIntel(){
 const[status,setStatus]=useState<IntelStatus|null>(null);
 const[company,setCompany]=useState('');
 const[result,setResult]=useState<IntelBundle|null>(null);
 const[loading,setLoading]=useState(false);
 const[error,setError]=useState('');
 const[openSkill,setOpenSkill]=useState('');
 const[openDiags,setOpenDiags]=useState(false);
 const[openRounds,setOpenRounds]=useState<Record<string,boolean>>({});

 const loadStatus=useCallback(async()=>{try{setStatus(await api.intelStatus())}catch(e:any){setError(e.message)}},[]);
 useEffect(()=>{loadStatus()},[loadStatus]);

 const research=async()=>{
  if(!company.trim())return;
  setLoading(true);setError('');setResult(null);setOpenSkill('');
  try{setResult(await api.intelResearch(company.trim()))}
  catch(e:any){setError(e.message)}
  finally{setLoading(false);loadStatus()}
 };
 const loadExisting=async(name:string)=>{
  setLoading(true);setError('');setResult(null);
  try{setResult(await api.intelCompany(name))}
  catch(e:any){setError(e.message)}
  finally{setLoading(false)}
 };

 const known=(status?.verified_companies||[]).map(v=>v.company);
 const knownFromDemo=known.length?known:(status?.bundled||[]).length?['Google','Microsoft','Oracle']:[];
 const rawMatrix = result?.artifacts?.skill_matrix;
 const rawExp = (result?.artifacts as any)?.expectation_matrix;
 const matrix = rawMatrix || (rawExp?.tokens ? {
  company_name: result?.company || '',
  skills: Object.entries(rawExp.tokens as Record<string, any>).map(([col, t]) => ({
   skill_set_code: (t.code || col.slice(0, 4)).toUpperCase(),
   skill_name: col.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
   required_level: t.level || 5,
   bloom_code: t.bloom_code || 'AP',
   confidence: t.generic ? 'low' : 'high',
   source_agreement: result?.providers_used?.length ? `${result.providers_used.length} sources` : 'offline heuristics',
   level_spread: 0,
   rationale: `Expectation benchmark for ${result?.company || 'company'} engineering roles.`,
   typical_topics: []
  })),
  consensus_sources: result?.providers_used?.length || 0,
  conflicts: []
 } : null);

 const rawHiring = result?.artifacts?.hiring_rounds;
 const rawRoles = rawHiring?.job_roles || (rawHiring as any)?.job_role_details?.map((d: any) => ({
  role_title: d.role_title || 'Software Engineer',
  role_category: d.role_category || 'SDE',
  opportunity_type: d.opportunity_type || 'Employment',
  job_summary: d.job_description || d.job_summary || '',
  hiring_rounds: (d.hiring_rounds || []).map((r: any) => ({
   round_number: r.round_number || 1,
   round_name: r.round_name || 'Interview',
   round_category: r.round_category || 'Interview',
   evaluation_type: r.evaluation_type || 'Technical',
   assessment_mode: r.assessment_mode || 'Online',
   duration_minutes: r.duration_minutes || 60,
   skills_tested: r.skills_tested || (r.skill_sets || []).map((s: any) => s.skill_set_code),
   typical_questions: Array.isArray(r.typical_questions) ? r.typical_questions : (r.typical_questions ? [r.typical_questions] : (r.skill_sets || []).map((s: any) => s.typical_questions).filter(Boolean))
  }))
 }));

 const hiring: IntelHiring | null = rawHiring ? {
  company_name: rawHiring.company_name || result?.company || '',
  job_roles: (rawRoles || []) as IntelRole[]
 } : null;

 const brief: IntelBrief = result?.artifacts?.company_brief || {
  company_name: result?.company || '',
  about: (result?.artifacts as any)?.golden_record?.['Company Description'] || (result?.artifacts as any)?.golden_record?.['Overview'] || (result?.mode === 'llm-research' ? `Multi-agent consensus intelligence profile for ${result?.company}.` : `Offline snapshot profile for ${result?.company}.`),
  campus_program: (result?.artifacts as any)?.golden_record?.['Campus Hiring Program'] || 'Standard Graduate Campus Hiring',
  interview_style: 'Multi-round algorithmic problem solving and domain depth',
  prep_focus: ['DSA and Core CS', 'System Design fundamentals', 'Hands-on practical implementation']
 };
 const bestSkill=matrix?.skills?.length?matrix.skills.reduce((a,b)=>(a.required_level>=b.required_level?a:b)):{required_level:0} as IntelSkill;
 const avgLevel=matrix?.skills?.length?Math.round(matrix.skills.reduce((s,b)=>s+b.required_level,0)/matrix.skills.length):0;

 return <div className="intel-root-plain">
  <header className="page-head"><div><div className="eyebrow page-eyebrow">Lab · Company intel</div><h1>Company intel</h1><p>How a company actually hires: the skills it tests, how deep, and in which rounds. Every dossier is checked before it feeds your readiness score.</p></div></header>
  <div className="intel-providers">
   {!(status?.providers||[]).length&&<span className="intel-provider-chip off">Loading providers…</span>}
   {(status?.providers||[]).map(p=><span key={p.provider} className={`intel-provider-chip ${p.available?'on':'off'}`}><i/>{p.provider}<small>{p.available?'connected':'offline'}</small></span>)}
   
  </div>

  <div className="intel-search-card">
   <ElevatedCard backgroundColor="#141417" edgeColors={{right:'#2A2A31',bottom:'#7A5E1E55'}} fullWidth style={{width:'100%'}}>
    <div style={{padding:14}}>
   <div className="intel-search-row">
    <Radar size={18} className="intel-search-icon"/>
    <input className="intel-input" placeholder="Search a company, e.g. Zomato" value={company}
      onChange={e=>setCompany(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')research()}}/>
    <button className="intel-cta" onClick={research} disabled={loading||company.trim().length<2}>
     {loading?<LoaderCircle size={15} className="spin"/>:<ArrowRight size={15}/>}{loading?'Researching…':'Research'}
    </button>
   </div>
   {knownFromDemo.length>0&&<div className="intel-chips-row">
    <small>Ready to open</small>
    {knownFromDemo.map(c=><button key={c} className="intel-chip" onClick={()=>loadExisting(c)}>{c}</button>)}
   </div>}
    </div>
   </ElevatedCard>
  </div>

  {error&&<div className="intel-alert error"><XCircle size={15}/><span>{error}</span></div>}
  {result?.notice&&<div className="intel-alert warn"><AlertTriangle size={15}/><span>{result.notice}</span></div>}
  {loading&&!result&&<div className="intel-pipeline skeleton-track">{['research fan-out','consensus','quality gate','hiring rounds','brief'].map(s=><div key={s} className="intel-stage skeleton"><LoaderCircle size={14} className="spin"/><span>{s}</span></div>)}</div>}

  {result&&!loading&&<div className="intel-result">
   {/* verdict header */}
   <div className="intel-verdict-card">
    <div className="intel-verdict-top">
     <div className="intel-verdict-name"><Landmark size={22}/><div><b>{result.company}</b><small>{result.mode==='llm-research'?`Multi-agent consensus · ${(result.providers_used||[]).join(' + ')}`:'Offline illustrative snapshot'}</small></div></div>
     <div className={`intel-verdict-pill ${result.verified?'pass':'unverified'}`}>{result.verified?<><CheckCircle2 size={14}/>Quality gate passed</>:<><AlertTriangle size={14}/>{result.mode==='llm-research'?'Gate flagged issues':'Unverified snapshot'}</>}</div>
    </div>
    <div className="intel-verdict-stats">
     <div><b>{avgLevel||', '}</b><span>avg required level</span></div>
     <div><b>{matrix?.skills?.length||0}</b><span>skill areas rated</span></div>
     <div><b>{result.mode==='llm-research'?String(matrix?.consensus_sources||0):'0'}</b><span>sources agreed</span></div>
     <div><b>{bestSkill?.required_level?bestSkill.skill_name:', '}</b><span>highest bar ({bestSkill?.required_level||', '}/10)</span></div>
    </div>
    {brief?.about&&<p className="intel-brief">{brief.about}</p>}
   </div>

   {/* pipeline trace */}
   <div className="intel-pipeline">
    {result.stages.map((s,i)=><div key={i} className={`intel-stage ${s.status}`}>
     <span className="stage-dot">{s.status==='ok'?'✓':'×'}</span>
     <span className="stage-name">{s.stage}</span>
     <span className="stage-time">{(s.duration_ms/1000).toFixed(1)}s</span>
    </div>)}
    {result.stages.length===0&&<div className="intel-stage ok"><span className="stage-dot">✓</span><span className="stage-name">loaded from store</span><span className="stage-time">cache</span></div>}
   </div>

   {/* skill matrix */}
   {matrix?.skills?.length?<div className="intel-matrix-card">
    <div className="intel-card-head"><h3>Skill expectation matrix</h3><span>What {result.company} actually tests, level 1-10 × Bloom depth</span></div>
    <div className="intel-matrix">
     {matrix.skills.map((s,i)=>{
      const open=openSkill===s.skill_set_code;
      const bloom=BLOOM_META[s.bloom_code]||BLOOM_META.AP;
      return <div key={s.skill_set_code} className={`intel-skill-row ${open?'open':''}`}>
       <button className="intel-skill-summary" onClick={()=>setOpenSkill(open?'':s.skill_set_code)}>
        <span className="intel-skill-code" style={{color:TIER_COLORS[i%TIER_COLORS.length],borderColor:TIER_COLORS[i%TIER_COLORS.length]+'55'}}>{s.skill_set_code}</span>
        <span className="intel-skill-name">{s.skill_name}</span>
        <span className="intel-skill-track"><i style={{width:`${s.required_level*10}%`,background:TIER_COLORS[i%TIER_COLORS.length]}}/></span>
        <b className="intel-skill-level">{s.required_level}/10</b>
        <span className="intel-bloom" style={{color:bloom.color,background:bloom.color+'1c'}}>{s.bloom_code} · {bloom.label}</span>
        <span className={`intel-confidence ${s.confidence}`}>{s.confidence}</span>
        <ChevronDown size={14} className="intel-chevron"/>
       </button>
       {open&&<div className="intel-skill-detail">
        {s.rationale&&<p>{s.rationale}</p>}
        {s.typical_topics?.length&&<div className="intel-topic-chips">{s.typical_topics.map(t=><span key={t}>{t}</span>)}</div>}
        <small>Agreement {s.source_agreement||'n/a'} · level spread {s.level_spread ?? 0} · consensus {matrix.consensus_sources} source(s)</small>
       </div>}
      </div>;
     })}
    </div>
    {matrix.conflicts?.length>0&&<div className="intel-conflicts">
     <h4><AlertTriangle size={13}/> Where the Where sources disagreed</h4>
     {matrix.conflicts.map(c=><p key={c.skill_set_code}><b>{c.skill_set_code}</b>, {c.detail}</p>)}
    </div>}
   </div>:<div className="intel-empty-card">No skill matrix in this bundle.</div>}

   {/* hiring rounds */}
   {hiring?.job_roles?.length?<div className="intel-hiring-card">
    <div className="intel-card-head"><h3>How {result.company} actually hires</h3><span>{hiring.job_roles.length} role(s) · every round, mapped to skills</span></div>
    {hiring.job_roles.map((role,ri)=><div key={ri} className="intel-role">
     <div className="intel-role-head"><b>{role.role_title}</b><span className="intel-role-tags"><i>{role.role_category}</i><i>{role.opportunity_type}</i></span></div>
     <p className="intel-role-sub">{role.job_summary}</p>
     <div className="intel-timeline">
      {(role.hiring_rounds||[]).map(r=>{
       const open=!!openRounds[`${ri}-${r.round_number}`];
       return <div key={r.round_number} className={`intel-round ${open?'open':''}`}>
        <button className="intel-round-summary" onClick={()=>setOpenRounds(o=>({...o,[`${ri}-${r.round_number}`]:!o[`${ri}-${r.round_number}`]}))}>
         <span className="round-num">{String(r.round_number).padStart(2,'0')}</span>
         <span className="round-name">{r.round_name}</span>
         <span className="round-meta">{r.round_category} · {r.evaluation_type} · {r.assessment_mode}</span>
         <span className="round-skill-chips">{(r.skills_tested||[]).map(c=><i key={c}>{c}</i>)}</span>
         <Clock3 size={12} className="round-clock"/>{r.duration_minutes?`${r.duration_minutes}m`:''}
         <ChevronDown size={13} className="intel-chevron"/>
        </button>
        {open&&<div className="intel-round-detail">
         {(r.typical_questions||[]).map((q,qi)=><p key={qi}>“{q}”</p>)}
        </div>}
       </div>;
      })}
     </div>
    </div>)}
   </div>:<div className="intel-empty-card">No hiring-round data in this bundle.</div>}

   {/* quality gate report */}
   <div className="intel-quality-card">
    <div className="intel-card-head">
     <div><h3>Data quality gate</h3><span>Offline Level-3-style rules, expanded automatically over every artifact</span></div>
     <div className={`intel-verdict-pill ${result.quality.passed?'pass':'fail'}`}>{result.quality.passed?<><CheckCircle2 size={13}/>PASS</>:<><XCircle size={13}/>FAIL</>} · {result.quality.errors}e / {result.quality.warnings}w</div>
    </div>
    {result.quality.diagnostics?.length?<>
     <button className="intel-diag-toggle" onClick={()=>setOpenDiags(!openDiags)}>{openDiags?'Hide':'Show'} all {result.quality.diagnostics.length} diagnostics</button>
     {openDiags&&<div className="intel-diags">{result.quality.diagnostics.map((d:IntelDiag,i)=><div key={i} className={`intel-diag ${d.severity}`}>
      <span>{d.severity==='error'?'ERROR':'WARN'}</span><b>{d.artifact}/{d.path}</b><p>{d.message}</p><small>rule: {d.rule}</small>
     </div>)}</div>}
    </>:<p className="intel-clean">Every rule reported clean. This record reached Talent Check unblocked.</p>}
   </div>
  </div>}

  {!result&&!loading&&!error&&<div className="intel-empty-card big">Open a dossier above, or search for another company.</div>}
  <button className="intel-refresh" onClick={loadStatus}><RefreshCw size={13}/> Refresh provider status</button>
 </div>;
}
