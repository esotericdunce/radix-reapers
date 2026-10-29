export type Skill = {skill_name:string;category_code:string;evidence:string;confidence:string;level?:number;candidate_evidence?:string;candidate_level?:number};
export type Profile = {id:string;name:string;email:string|null;education:string[];skills:Skill[];projects:string[];hackathons:string[];internships:string[];certifications:string[];preferred_roles:string[];cv_file:string|null};
export type Job = {id:string;title:string;company:string;text:string};
export type Analysis = {title:string;company:string;source_file:string;text:string;required_skills:Skill[];method:string};
export type MatchResult = {candidate_id:string;jd_source_file:string;job_title:string;match_score:number;matched_skills:Skill[];missing_skills:Skill[];category_breakdown:Record<string,{label:string;required:number;matched:number}>;recommendations:string[];method:string};

export type Assessment = {type:'match'|'readiness';candidate_id:string;candidate_name:string;target:string;score:number;timestamp:string};

export type ProviderStatus={provider:string;model:string;available:boolean};
export type VerifiedCompany={company:string;mode:string;verified:boolean;errors:number;warnings:number;researched_at:string};
export type IntelStatus={providers:ProviderStatus[];verified_companies:VerifiedCompany[];bundled:string[]};
export type IntelSkill={skill_set_code:string;skill_name:string;required_level:number;bloom_code:string;rationale?:string;typical_topics?:string[];confidence:string;source_agreement?:string;level_spread?:number};
export type IntelMatrix={company_name:string;skills:IntelSkill[];consensus_sources:number;conflicts:{skill_set_code:string;detail:string;votes:Record<string,number>}[]};
export type IntelRound={round_number:number;round_name:string;round_category:string;evaluation_type:string;assessment_mode:string;duration_minutes?:number;skills_tested?:string[];typical_questions?:string[]};
export type IntelRole={role_title:string;role_category:string;opportunity_type:string;job_summary:string;hiring_rounds:IntelRound[]};
export type IntelHiring={company_name:string;job_roles:IntelRole[]};
export type IntelBrief={company_name:string;about?:string;campus_program?:string;interview_style?:string;prep_focus?:string[]};
export type IntelDiag={rule:string;severity:'error'|'warn';artifact:string;path:string;message:string;scope:string;category:string};
export type IntelStage={stage:string;status:'ok'|'error';duration_ms:number;detail?:string};
export type IntelBundle={company:string;researched_at:string;mode:string;verified:boolean;notice?:string;providers_used?:string[];stages:IntelStage[];artifacts:{skill_matrix:IntelMatrix;hiring_rounds:IntelHiring|null;company_brief:IntelBrief};quality:{passed:boolean;errors:number;warnings:number;diagnostics:IntelDiag[]};quality_report_md?:string};
export type TalentVerification={verified:boolean;mode:string;researched_at:string;quality_errors:number;quality_warnings:number;consensus_sources:number;conflicts:IntelMatrix['conflicts']};

export type CommitteePersona = {name:string;role:string;vote:string;stance:string;key_concern:string;key_endorsement:string};
export type CommitteeResult = {mode:string;provider:string;company:string;candidate_id:string;consensus_verdict:string;consensus_score:number;summary_statement:string;personas:CommitteePersona[];conditions_to_hire:string[];key_differentiator:string};

export type InterviewQuestion = {question_id:string;company:string;round_name:string;interviewer_role:string;question:string;scenario_context:string;target_bloom:string;primary_skill:string;constraints?:string[];hints:string[];evaluation_criteria:string[];mode:string;provider:string};
export type InterviewEvaluation = {score:number;bloom_achieved:string;bloom_label:string;verdict:string;summary_feedback:string;strengths:string[];blindspots_and_gaps:string[];follow_up_challenge?:string;ideal_answer_takeaway:string;production_code_snippet?:string;dimension_scores?:Record<string,number>;recommended_profile_level:number;suggested_skill_to_update:string;profile_updated?:boolean;mode:string;provider:string};

export type TierInfo = {label:string;ctc_range:string;readiness_score:number;status:string;representative_companies:string[]};
export type RoiJump = {skill:string;current_level:number;target_level:number;unlocked_tier:string;estimated_ctc_boost:string;reasoning:string};
export type CareerRadarData = {candidate_id:string;candidate_name:string;overall_placement_tier:string;tiers:Record<string,TierInfo>;roi_skill_jumps:RoiJump[]};

export type TailoredBulletResult = {skill_name:string;target_company:string;ats_bullet:string;xyz_breakdown:{accomplished_x:string;measured_by_y:string;done_by_z:string};micro_project_blueprint:{project_title:string;github_repo_slug:string;architecture_summary:string;deliverables:string[]};mode:string};
