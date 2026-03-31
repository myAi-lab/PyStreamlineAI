export type ApiEnvelope<T> = {
  success: true;
  data: T;
  request_id?: string;
};

export type ApiErrorEnvelope = {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  request_id?: string;
};

export type UserRole = "candidate" | "student" | "recruiter" | "admin";
export type InterviewStatus = "created" | "ready" | "active" | "paused" | "completed" | "failed";
export type InterviewMode = "behavioral" | "technical" | "mixed";
export type ResumeSourceType = "upload" | "pasted_text";
export type ResumeParseStatus = "pending" | "processing" | "completed" | "failed";

export type UserPublic = {
  id: string;
  email: string;
  role_contact_email: string | null;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_token_expires_minutes: number;
};

export type AuthPayload = {
  user: UserPublic;
  tokens: TokenPair;
};

export type CandidateProfile = {
  id: string;
  user_id: string;
  headline: string | null;
  years_experience: number | null;
  target_roles: string[];
  location: string | null;
  role_contact_email: string | null;
  role_profile: Record<string, string>;
  created_at: string;
  updated_at: string;
};

export type Resume = {
  id: string;
  user_id: string;
  source_type: ResumeSourceType;
  file_name: string | null;
  storage_key: string | null;
  parse_status: ResumeParseStatus;
  created_at: string;
  updated_at: string;
};

export type ResumeDetail = Resume & {
  raw_text: string;
};

export type ResumeAnalysis = {
  id: string;
  resume_id: string;
  extracted_skills: string[];
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  summary: string;
  model_name: string;
  analysis_version: string;
  created_at: string;
};

export type ResumeProcessResponse = {
  resume: Resume;
  job_id: string | null;
  analysis: ResumeAnalysis | null;
};

export type InterviewSession = {
  id: string;
  user_id: string;
  role_target: string;
  status: InterviewStatus;
  session_mode: InterviewMode;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InterviewTurn = {
  id: string;
  session_id: string;
  turn_index: number;
  interviewer_message: string;
  candidate_message: string | null;
  model_feedback: {
    strengths?: string[];
    weaknesses?: string[];
    feedback?: string;
    next_step_guidance?: string;
  } | null;
  score_overall: number | null;
  score_communication: number | null;
  score_technical: number | null;
  score_confidence: number | null;
  created_at: string;
};

export type InterviewSummary = {
  id: string;
  session_id: string;
  final_score: number;
  recommendation: string;
  strengths: string[];
  improvement_areas: string[];
  summary: string;
  created_at: string;
};

export type InterviewStartResponse = {
  session: InterviewSession;
  first_turn: InterviewTurn;
  is_complete: boolean;
};

export type InterviewRespondResponse = {
  session: InterviewSession;
  evaluated_turn: InterviewTurn;
  evaluation: {
    turn_id: string;
    score_overall: number;
    score_communication: number;
    score_technical: number;
    score_confidence: number;
    strengths: string[];
    weaknesses: string[];
    feedback: string;
    next_step_guidance: string;
  };
  next_turn: InterviewTurn | null;
  is_complete: boolean;
};

export type InterviewSessionDetail = {
  session: InterviewSession;
  turns: InterviewTurn[];
  summary: InterviewSummary | null;
};

export type Usage = {
  total_resumes: number;
  total_resume_analyses: number;
  total_sessions: number;
  completed_sessions: number;
};

export type ModelConfig = {
  provider: string;
  default_model: string;
  max_retries: number;
  timeout_seconds: number;
  interview_max_turns: number;
};

export type WorkspaceSession = {
  id: string;
  user_id: string;
  title: string;
  message_count: number;
  last_message_preview: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkspaceMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  message_type: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type WorkspaceSessionDetail = {
  session: WorkspaceSession;
  messages: WorkspaceMessage[];
};

export type WorkspaceMessageSendResponse = {
  session: WorkspaceSession;
  user_message: WorkspaceMessage;
  assistant_message: WorkspaceMessage;
};

export type RecentScoreItem = {
  kind: "resume_analysis" | "interview_summary";
  entity_id: string;
  title: string;
  score: number;
  summary: string;
  created_at: string;
};

export type LiveInterviewLaunchResponse = {
  launch_url: string;
  expires_at: string;
};

export type CareersMatchFilters = {
  role_query: string;
  preferred_location: string;
  visa_status: string;
  sponsorship_required: boolean;
  selected_position_types: string[];
  posted_within_days: number;
  max_results: number;
};

export type CareersTopCompanyLink = {
  name: string;
  url: string;
};

export type CareersMatchResult = {
  external_id: string | null;
  title: string;
  company: string;
  location: string;
  posted_at: string | null;
  overall_score: number;
  resume_match_score: number;
  role_relevance: number;
  sponsorship_status: string;
  sponsorship_confidence: number;
  reason: string;
  missing_points: string[];
  apply_url: string | null;
  position_tags: string[];
  source_provider: string;
};

export type CareersMatchResponse = {
  filters: CareersMatchFilters;
  results: CareersMatchResult[];
  trace: string[];
  info_message: string | null;
  top_company_links: CareersTopCompanyLink[];
};

export type CodingRoomStage = {
  stage_index: number;
  title: string;
  skill_focus: string;
  challenge: string;
  difficulty: string;
  time_limit_min: number;
  requirements: string[];
  hint_starters: string[];
};

export type CodingRoomStagesResponse = {
  role_target: string;
  interview_mode: InterviewMode;
  stages: CodingRoomStage[];
};

export type CodingStarterCodeResponse = {
  stage_index: number;
  language: string;
  code: string;
};

export type CodingHiddenCheckResponse = {
  ran: boolean;
  total: number;
  passed: number;
  failed_cases: string[];
  summary: string;
  ready_for_evaluation: boolean;
};

export type CodingEvaluationResponse = {
  score: number;
  verdict: string;
  strengths: string[];
  improvements: string[];
  next_step: string;
};

export type ImmigrationUpdateItem = {
  id: string;
  title: string;
  summary: string;
  source: string;
  source_url: string | null;
  link: string;
  visa_category: string;
  published_date: string | null;
  tags: string[];
};

export type ImmigrationSearchResponse = {
  updates: ImmigrationUpdateItem[];
  categories: string[];
  live_note: string;
  last_refreshed_at: string | null;
};

export type ImmigrationRefreshResponse = {
  refreshed: boolean;
  fetched_count: number;
  message: string;
  last_refreshed_at: string | null;
};

export type ImmigrationBriefResponse = {
  brief: string;
  generated_at: string;
};
