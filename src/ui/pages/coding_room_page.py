from __future__ import annotations

# Transitional extraction: page rendering moved out of app_runtime.
from src.app_runtime import *  # noqa: F401,F403

def render_coding_room_view(user: dict[str, Any]) -> None:
    full_name = str(user.get("full_name", "")).strip()
    first_name = full_name.split()[0] if full_name else "Candidate"
    analysis = st.session_state.get("analysis_result") or {}
    resume_text = str(st.session_state.get("latest_resume_text", "")).strip()
    job_description = str(st.session_state.get("latest_job_description", "")).strip()
    logo_data_uri = get_logo_data_uri()
    is_mobile = is_mobile_browser()
    interviewer_chat_height = 260 if is_mobile else 320
    editor_height = 360 if is_mobile else 520
    # One-time cleanup for legacy autoscroll observers that can cause scroll jitter while typing.
    render_zoswi_autoscroll_cleanup_once()
    if st.session_state.get("coding_room_clear_input"):
        st.session_state.coding_room_user_input = ""
        st.session_state.coding_room_clear_input = False

    st.markdown(
        """
        <style>
        .coding-room-shell {
            border: 1px solid #dbeafe;
            border-radius: 18px;
            padding: 1rem 1rem 0.8rem 1rem;
            background:
                radial-gradient(800px 280px at -8% -14%, rgba(14, 165, 233, 0.16) 0%, transparent 56%),
                radial-gradient(600px 240px at 100% 0%, rgba(20, 184, 166, 0.15) 0%, transparent 60%),
                #ffffff;
            box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
        }
        .coding-room-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
            margin-bottom: 0.75rem;
        }
        .coding-room-title h2 {
            margin: 0;
            color: #0f172a;
            font-size: 1.48rem;
            line-height: 1.15;
        }
        .coding-room-title p {
            margin: 0.22rem 0 0 0;
            color: #475569;
            font-size: 0.9rem;
        }
        .coding-live-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border: 1px solid #99f6e4;
            background: #f0fdfa;
            color: #0f766e;
            border-radius: 999px;
            padding: 0.28rem 0.62rem;
            font-size: 0.76rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .coding-live-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #14b8a6;
            box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.55);
            animation: codingLivePulse 1.5s infinite;
        }
        @keyframes codingLivePulse {
            0% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.52); }
            70% { box-shadow: 0 0 0 8px rgba(20, 184, 166, 0.0); }
            100% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.0); }
        }
        .coding-video-shell {
            border: 1px solid #dbeafe;
            border-radius: 15px;
            overflow: hidden;
            background: linear-gradient(180deg, #f8fbff 0%, #eef7ff 100%);
            min-height: 468px;
        }
        .coding-video-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.65rem;
            padding: 0.58rem 0.72rem;
            border-bottom: 1px solid #e2e8f0;
            background: rgba(255, 255, 255, 0.86);
        }
        .coding-memoji {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #34d399 0%, #22d3ee 100%);
            color: #ffffff;
            font-size: 1.05rem;
            box-shadow: 0 8px 18px rgba(45, 212, 191, 0.33);
        }
        .coding-video-name {
            margin: 0;
            color: #0f172a;
            font-size: 0.9rem;
            font-weight: 700;
            line-height: 1.1;
        }
        .coding-video-sub {
            margin: 0.12rem 0 0 0;
            color: #475569;
            font-size: 0.77rem;
            line-height: 1.1;
        }
        .coding-video-body {
            padding: 0.78rem 0.82rem 0.84rem 0.82rem;
        }
        .coding-question-stage {
            margin: 0;
            color: #0369a1;
            font-size: 0.73rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }
        .coding-question-title {
            margin: 0.24rem 0 0 0;
            color: #0f172a;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.3;
        }
        .coding-question-meta {
            margin: 0.26rem 0 0 0;
            color: #334155;
            font-size: 0.8rem;
            line-height: 1.32;
        }
        .coding-question-text {
            margin: 0.36rem 0 0 0;
            color: #1e293b;
            font-size: 0.81rem;
            line-height: 1.38;
        }
        .coding-question-subhead {
            margin: 0.5rem 0 0.2rem 0;
            color: #0f172a;
            font-size: 0.8rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .coding-question-list {
            margin: 0;
            padding-left: 1.03rem;
            color: #334155;
            font-size: 0.79rem;
            line-height: 1.34;
        }
        .coding-question-list li {
            margin-bottom: 0.12rem;
        }
        .coding-stage-card {
            border: 1px solid #dbeafe;
            border-radius: 15px;
            background: linear-gradient(140deg, #ffffff 0%, #f3f8ff 100%);
            padding: 0.92rem;
            box-shadow: 0 12px 24px rgba(14, 116, 144, 0.08);
        }
        .coding-stage-title {
            margin: 0;
            color: #0f172a;
            font-size: 1.06rem;
            font-weight: 700;
            line-height: 1.25;
        }
        .coding-stage-meta {
            margin: 0.38rem 0 0.5rem 0;
            color: #334155;
            font-size: 0.82rem;
            line-height: 1.35;
        }
        .coding-room-shell ul {
            margin-top: 0.2rem;
        }
        .st-key-coding_action_ready button,
        .st-key-coding_action_hint button,
        .st-key-coding_action_nudge button {
            border-radius: 999px !important;
            border: 1px solid #bae6fd !important;
            background: #f0f9ff !important;
            color: #0c4a6e !important;
            font-weight: 700 !important;
            font-size: 0.77rem !important;
            min-height: 2rem !important;
            box-shadow: none !important;
        }
        .st-key-coding_action_ready button:hover,
        .st-key-coding_action_hint button:hover,
        .st-key-coding_action_nudge button:hover {
            border-color: #38bdf8 !important;
            background: #e0f2fe !important;
        }
        .st-key-coding_eval_btn button,
        .st-key-coding_next_stage_btn button,
        .st-key-coding_load_template_btn button,
        .st-key-coding_reset_session_btn button,
        .st-key-coding_back_home_btn button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            min-height: 2.05rem !important;
        }
        .st-key-coding_eval_btn button {
            border: 1px solid #0f766e !important;
            background: linear-gradient(130deg, #14b8a6 0%, #0ea5e9 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 10px 18px rgba(20, 184, 166, 0.26) !important;
        }
        .st-key-coding_next_stage_btn button {
            border: 1px solid #1d4ed8 !important;
            background: #dbeafe !important;
            color: #1e3a8a !important;
        }
        .st-key-coding_reset_session_btn button {
            border: 1px solid #fca5a5 !important;
            background: #fef2f2 !important;
            color: #b91c1c !important;
        }
        .st-key-coding_reset_session_btn button:hover {
            border-color: #ef4444 !important;
            background: #fee2e2 !important;
            color: #991b1b !important;
        }
        .st-key-coding_load_template_btn button {
            border: 1px solid #cbd5e1 !important;
            background: #ffffff !important;
            color: #334155 !important;
            min-height: 1.85rem !important;
            font-size: 0.74rem !important;
            margin: 0.35rem 0 0.42rem 0 !important;
        }
        .st-key-coding_stage_approach_wrap [data-testid="stTextArea"] > label {
            color: #334155 !important;
            font-size: 0.76rem !important;
            font-weight: 700 !important;
        }
        .st-key-coding_stage_approach_wrap textarea {
            min-height: 112px !important;
            border-radius: 10px !important;
            border: 1px solid #cbd5e1 !important;
            background: #ffffff !important;
            color: #0f172a !important;
            line-height: 1.4 !important;
            font-size: 0.82rem !important;
        }
        .coding-score-card {
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            background: #f8fbff;
            padding: 0.7rem 0.78rem;
            margin-top: 0.45rem;
        }
        .coding-score-card h4 {
            margin: 0;
            color: #0f172a;
            font-size: 0.91rem;
            line-height: 1.25;
        }
        .coding-score-card p {
            margin: 0.24rem 0 0 0;
            color: #334155;
            font-size: 0.79rem;
            line-height: 1.34;
        }
        .coding-workspace-wrap {
            border: 1px solid #cbd5e1;
            border-radius: 13px;
            background:
                radial-gradient(900px 300px at -12% -30%, rgba(14, 165, 233, 0.12) 0%, transparent 56%),
                radial-gradient(700px 260px at 110% -28%, rgba(16, 185, 129, 0.1) 0%, transparent 58%),
                #f8fbff;
            padding: 0.75rem 0.8rem;
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
            margin-bottom: 0.58rem;
        }
        .coding-workspace-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            margin-bottom: 0.56rem;
        }
        .coding-workspace-title {
            margin: 0;
            color: #0f172a;
            font-size: 0.94rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .coding-workspace-sub {
            margin: 0.1rem 0 0 0;
            color: #475569;
            font-size: 0.74rem;
            line-height: 1.2;
        }
        .coding-workspace-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            border: 1px solid #7dd3fc;
            background: #e0f2fe;
            color: #0c4a6e;
            border-radius: 999px;
            padding: 0.18rem 0.54rem;
            font-size: 0.68rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .coding-workspace-chips {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.43rem;
        }
        .coding-tech-chip {
            border: 1px solid #dbeafe;
            border-radius: 10px;
            background: #ffffff;
            padding: 0.34rem 0.42rem;
        }
        .coding-tech-key {
            margin: 0;
            color: #64748b;
            font-size: 0.62rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            line-height: 1.1;
        }
        .coding-tech-value {
            margin: 0.17rem 0 0 0;
            color: #0f172a;
            font-size: 0.76rem;
            font-weight: 700;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .coding-tech-value.timer-live-display {
            font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
            font-size: 0.98rem;
            letter-spacing: 0.03em;
        }
        .coding-tech-value.timer-safe {
            color: #047857;
        }
        .coding-tech-value.timer-alert {
            color: #b91c1c;
        }
        .st-key-coding_language_wrap [data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important;
            color: #0f172a !important;
            box-shadow: none !important;
        }
        .st-key-coding_language_wrap [data-baseweb="select"] span,
        .st-key-coding_language_wrap [data-baseweb="select"] div {
            color: #0f172a !important;
        }
        .st-key-coding_language_wrap label {
            color: #475569 !important;
            font-size: 0.74rem !important;
            font-weight: 700 !important;
        }
        .coding-editor-shell {
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            overflow: hidden;
            background: #f8fafc;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.11);
        }
        .coding-editor-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            padding: 0.48rem 0.62rem;
            border-bottom: 1px solid #d1d5db;
            background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
        }
        .coding-editor-tabs {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .coding-editor-tab {
            border: 1px solid #334155;
            background: #0b1220;
            color: #cbd5e1;
            border-radius: 999px;
            padding: 0.16rem 0.54rem;
            font-size: 0.7rem;
            font-weight: 700;
            line-height: 1;
        }
        .coding-editor-tab.active {
            border-color: #0ea5e9;
            color: #e0f2fe;
            background: rgba(14, 165, 233, 0.2);
        }
        .coding-editor-status {
            color: #334155;
            font-size: 0.72rem;
            font-weight: 600;
            line-height: 1;
        }
        .coding-editor-head-left {
            display: inline-flex;
            align-items: center;
            gap: 0.34rem;
        }
        .coding-editor-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }
        .coding-editor-dot.red { background: #ef4444; }
        .coding-editor-dot.yellow { background: #eab308; }
        .coding-editor-dot.green { background: #22c55e; }
        .coding-editor-file {
            color: #0f172a;
            font-size: 0.71rem;
            font-weight: 700;
            margin-left: 0.32rem;
            letter-spacing: 0.01em;
        }
        .st-key-coding_editor_shell [data-testid="stTextArea"] > label {
            color: #334155 !important;
            font-weight: 600 !important;
            font-size: 0.77rem !important;
        }
        .st-key-coding_editor_shell .zoswi-code-line-gutter {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            overflow: hidden !important;
        }
        .st-key-coding_editor_shell [data-testid="stTextArea"].zoswi-code-editor-root {
            position: static !important;
        }
        .st-key-coding_editor_shell {
            border: 1px solid #bfdbfe;
            border-top: 0;
            border-radius: 0 0 12px 12px;
            background: linear-gradient(135deg, #ffffff 0%, #eff6ff 45%, #ecfeff 100%);
            box-shadow: 0 12px 24px rgba(30, 64, 175, 0.1);
            padding: 0.32rem 0.36rem 0.36rem 0.36rem;
            margin-top: -1px;
        }
        .st-key-coding_editor_shell [data-testid="stTextArea"] {
            border: 1px solid #dbeafe;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.96);
            padding: 0.12rem;
        }
        .st-key-coding_editor_shell [data-testid="stTextArea"] textarea {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 0 0 10px 10px !important;
            font-family: "JetBrains Mono", "Consolas", "Courier New", monospace !important;
            font-size: 0.86rem !important;
            line-height: 1.45 !important;
            caret-color: #0369a1 !important;
            min-height: 250px !important;
            background-image:
                url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='340' height='140' viewBox='0 0 340 140'%3E%3Ctext x='50%25' y='54%25' dominant-baseline='middle' text-anchor='middle' font-family='Segoe UI,Arial,sans-serif' font-size='52' font-weight='700' fill='%230284c7' fill-opacity='0.11'%3EZoSwi%3C/text%3E%3C/svg%3E"),
                linear-gradient(transparent 96%, rgba(148, 163, 184, 0.06) 96%),
                linear-gradient(90deg, rgba(148, 163, 184, 0.04) 1px, transparent 1px) !important;
            background-repeat: no-repeat, repeat, repeat !important;
            background-position: center center, 0 0, 0 0 !important;
            background-size: 220px auto, 100% 1.5rem, 1.5rem 100% !important;
        }
        .st-key-coding_editor_shell [data-testid="stTextArea"] textarea:focus {
            border-color: #0284c7 !important;
            box-shadow: 0 0 0 1px rgba(2, 132, 199, 0.32) !important;
        }
        @media (max-width: 980px) {
            .coding-room-shell {
                padding: 0.75rem 0.75rem 0.68rem 0.75rem;
            }
            .coding-room-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.45rem;
            }
            .coding-room-title h2 {
                font-size: 1.2rem;
            }
            .coding-room-title p {
                font-size: 0.8rem;
            }
            .coding-video-shell {
                min-height: auto;
            }
            .coding-video-body {
                padding: 0.62rem 0.64rem 0.68rem 0.64rem;
            }
            .coding-question-title {
                font-size: 0.9rem;
            }
            .coding-question-meta,
            .coding-question-text,
            .coding-question-list {
                font-size: 0.76rem;
            }
            .coding-workspace-top {
                flex-direction: column;
                align-items: flex-start;
            }
            .coding-workspace-chips {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .st-key-coding_main_cols_wrap [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 0.6rem !important;
            }
            .st-key-coding_main_cols_wrap [data-testid="column"] {
                flex: 1 1 100% !important;
                min-width: 100% !important;
                width: 100% !important;
            }
            .st-key-coding_room_input_wrap [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 0.32rem !important;
            }
            .st-key-coding_room_input_wrap [data-testid="column"] {
                flex: 1 1 100% !important;
                min-width: 100% !important;
                width: 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if logo_data_uri:
        st.markdown(
            f"""
            <style>
            .st-key-coding_editor_shell [data-testid="stTextArea"] textarea {{
                background-image:
                    linear-gradient(rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.92)),
                    url("{logo_data_uri}"),
                    linear-gradient(transparent 96%, rgba(148, 163, 184, 0.06) 96%),
                    linear-gradient(90deg, rgba(148, 163, 184, 0.04) 1px, transparent 1px) !important;
                background-repeat: no-repeat, no-repeat, repeat, repeat !important;
                background-position: center center, center center, 0 0, 0 0 !important;
                background-size: 100% 100%, 520px auto, 100% 1.5rem, 1.5rem 100% !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="coding-room-shell">
            <div class="coding-room-header">
                <div class="coding-room-title">
                    <h2>ZoSwi Live Coding Room</h2>
                    <p>One-on-one coding interview simulation for {html.escape(first_name)} using your latest resume and JD analysis.</p>
                </div>
                <div class="coding-live-pill"><span class="coding-live-dot"></span>LIVE INTERVIEW FLOW</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not resume_text or not job_description or not isinstance(analysis, dict):
        st.warning("Run Resume-JD Analysis first, then launch the coding room.")
        with st.container(key="coding_back_home_btn"):
            if st.button("Go To Home", key="coding_go_home_from_empty", use_container_width=False):
                st.session_state.dashboard_view = "home"
                st.rerun()
        return

    source_payload = json.dumps(analysis, sort_keys=True, ensure_ascii=True)
    source_sig = hashlib.sha256(f"{resume_text}\n##\n{job_description}\n##\n{source_payload}".encode("utf-8")).hexdigest()
    if st.session_state.get("coding_room_source_sig") != source_sig:
        with st.spinner("Preparing your 3-stage coding simulation..."):
            payload = build_coding_stage_payload(resume_text, job_description, analysis)
        st.session_state.coding_room_payload = payload
        st.session_state.coding_room_source_sig = source_sig
        st.session_state.coding_room_stage_index = 0
        st.session_state.coding_room_stage_scores = {}
        st.session_state.coding_room_messages = []
        st.session_state.coding_room_session_started = False
        st.session_state.coding_room_clear_input = True
        st.session_state.coding_room_scroll_pending = False
        st.session_state.coding_room_stage_started_at = {}
        st.session_state.coding_room_hidden_tests = {}
        st.session_state.coding_room_stage_approaches = {}

    payload = st.session_state.get("coding_room_payload")
    if not isinstance(payload, dict) or not isinstance(payload.get("stages"), list) or not payload.get("stages"):
        st.error("Coding room setup failed. Please click back and run analysis again.")
        return

    stages = payload["stages"]
    total_stages = min(CODING_STAGE_COUNT, len(stages))
    stage_index = int(st.session_state.get("coding_room_stage_index") or 0)
    stage_index = max(0, min(total_stages - 1, stage_index))
    st.session_state.coding_room_stage_index = stage_index
    stage = stages[stage_index]
    stage_scores = st.session_state.get("coding_room_stage_scores", {})
    if not isinstance(stage_scores, dict):
        stage_scores = {}
    stage_key = str(stage_index)
    stage_started_at = st.session_state.get("coding_room_stage_started_at", {})
    if not isinstance(stage_started_at, dict):
        stage_started_at = {}
    if stage_key not in stage_started_at:
        stage_started_at[stage_key] = float(time.time())
        st.session_state.coding_room_stage_started_at = stage_started_at
    elapsed_seconds = max(0, int(time.time() - float(stage_started_at.get(stage_key, time.time()))))
    stage_limit_seconds = max(60, int(stage.get("time_limit_min", 20)) * 60)
    remaining_seconds = max(0, stage_limit_seconds - elapsed_seconds)
    timer_expired = remaining_seconds <= 0
    timer_instance_token = f"{stage_key}_{int(float(stage_started_at.get(stage_key, time.time())))}"
    timer_dom_id = f"coding_chip_timer_{re.sub(r'[^a-zA-Z0-9_-]', '_', timer_instance_token)}"

    hidden_tests_map = st.session_state.get("coding_room_hidden_tests", {})
    if not isinstance(hidden_tests_map, dict):
        hidden_tests_map = {}
    approaches_map = st.session_state.get("coding_room_stage_approaches", {})
    if not isinstance(approaches_map, dict):
        approaches_map = {}

    completed_stages = len([key for key in stage_scores if str(key).isdigit()])
    progress_value = min(1.0, float(completed_stages) / float(max(1, total_stages)))

    if not st.session_state.get("coding_room_session_started"):
        intro = str(payload.get("interviewer_intro", "")).strip()
        if intro:
            append_coding_room_message("assistant", intro)
        stage_opening = (
            f"Stage {stage_index + 1}/{total_stages}: {stage.get('title', '')}. "
            "When ready, summarize your approach, then complete the TODO blocks in starter code."
        )
        append_coding_room_message("assistant", stage_opening)
        st.session_state.coding_room_session_started = True

    skills = payload.get("detected_skills", [])
    if isinstance(skills, list) and skills:
        st.caption(f"Skill alignment: {', '.join(str(skill) for skill in skills[:6])}")
    st.progress(progress_value, text=f"Stage progress: {completed_stages}/{total_stages} completed")

    stage_question_text = str(stage.get("question", "") or stage.get("challenge", "")).strip()
    stage_completion_steps = stage.get("completion_steps", [])
    if not isinstance(stage_completion_steps, list) or not stage_completion_steps:
        stage_completion_steps = stage.get("requirements", [])
    question_requirements_html = "".join(
        f"<li>{html.escape(str(req))}</li>" for req in stage_completion_steps[:4]
    )
    question_hints_html = "".join(
        f"<li>{html.escape(str(hint))}</li>" for hint in stage.get("hint_starters", [])[:3]
    )
    question_sample_case = str(stage.get("sample_case", "")).strip()

    with st.container(key="coding_main_cols_wrap"):
        if is_mobile:
            left_col = st.container()
            right_col = st.container()
        else:
            left_col, right_col = st.columns([0.96, 1.34], gap="medium")
    with left_col:
        st.markdown(
            f"""
            <div class="coding-video-shell">
                <div class="coding-video-head">
                    <div style="display:flex;align-items:center;gap:0.52rem;">
                        <span class="coding-memoji">\U0001F916</span>
                        <div>
                            <p class="coding-video-name">ZoSwi Interview Bot</p>
                            <p class="coding-video-sub">Live stage {stage_index + 1} interviewer</p>
                        </div>
                    </div>
                    <div class="coding-live-pill"><span class="coding-live-dot"></span>ACTIVE</div>
                </div>
                <div class="coding-video-body">
                    <p class="coding-question-stage">Stage {stage_index + 1} Question</p>
                    <p class="coding-question-title">{html.escape(str(stage.get("title", "")))}</p>
                    <p class="coding-question-meta"><strong>Focus:</strong> {html.escape(str(stage.get("skill_focus", "")))} | <strong>Time:</strong> {int(stage.get("time_limit_min", 20))} min</p>
                    <p class="coding-question-text"><strong>Scenario:</strong> {html.escape(str(stage.get("scenario", "")))}</p>
                    <p class="coding-question-text"><strong>Question:</strong> {html.escape(stage_question_text)}</p>
                    {f'<p class="coding-question-text"><strong>Sample:</strong> {html.escape(question_sample_case)}</p>' if question_sample_case else ''}
                    <p class="coding-question-subhead">Complete These TODOs</p>
                    <ul class="coding-question-list">{question_requirements_html}</ul>
                    <p class="coding-question-subhead">Hint Starters</p>
                    <ul class="coding-question-list">{question_hints_html}</ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(height=interviewer_chat_height):
            chat_history_container = st.container()
            live_reply_container = st.container()
            with chat_history_container:
                for msg in st.session_state.get("coding_room_messages", []):
                    st.markdown(
                        format_zoswi_message_html(
                            msg.get("role", "assistant"),
                            msg.get("content", ""),
                            first_name,
                        ),
                        unsafe_allow_html=True,
                    )
            if bool(st.session_state.get("coding_room_scroll_pending", False)):
                st.markdown('<div id="zoswi-scroll-anchor"></div>', unsafe_allow_html=True)
                render_zoswi_autoscroll()
                st.session_state.coding_room_scroll_pending = False

        if is_mobile:
            with st.container(key="coding_action_ready"):
                ready_clicked = st.button("\U0001F60A I am ready", key="coding_action_ready_btn", use_container_width=True)
            with st.container(key="coding_action_hint"):
                hint_clicked = st.button("\U0001F914 Give hint", key="coding_action_hint_btn", use_container_width=True)
            with st.container(key="coding_action_nudge"):
                nudge_clicked = st.button("\u23ED Move forward", key="coding_action_nudge_btn", use_container_width=True)
        else:
            action_cols = st.columns(3, gap="small")
            with action_cols[0]:
                with st.container(key="coding_action_ready"):
                    ready_clicked = st.button("\U0001F60A I am ready", key="coding_action_ready_btn", use_container_width=True)
            with action_cols[1]:
                with st.container(key="coding_action_hint"):
                    hint_clicked = st.button("\U0001F914 Give hint", key="coding_action_hint_btn", use_container_width=True)
            with action_cols[2]:
                with st.container(key="coding_action_nudge"):
                    nudge_clicked = st.button("\u23ED Move forward", key="coding_action_nudge_btn", use_container_width=True)

        pending_action = ""
        pending_user_message = ""
        if ready_clicked:
            pending_action = "ready"
            pending_user_message = "I am ready. Please continue."
        elif hint_clicked:
            pending_action = "hint"
            pending_user_message = "I need a hint for this stage."
        elif nudge_clicked:
            pending_action = "nudge"
            pending_user_message = "Move to the next interview follow-up question."
        if pending_action:
            append_coding_room_message("user", pending_user_message)

        with st.container(key="coding_room_input_wrap"):
            if is_mobile:
                candidate_message = st.text_input(
                    "Message interviewer",
                    key="coding_room_user_input",
                    on_change=request_coding_room_submit,
                    label_visibility="collapsed",
                    placeholder="Tell your approach or ask clarifications...",
                )
                send_message = st.button("\u2191", key="coding_room_send_btn", use_container_width=True, help="Send")
            else:
                input_cols = st.columns([9, 1])
                with input_cols[0]:
                    candidate_message = st.text_input(
                        "Message interviewer",
                        key="coding_room_user_input",
                        on_change=request_coding_room_submit,
                        label_visibility="collapsed",
                        placeholder="Tell your approach or ask clarifications...",
                    )
                with input_cols[1]:
                    send_message = st.button("\u2191", key="coding_room_send_btn", use_container_width=True, help="Send")

        submit_requested = bool(send_message) or bool(st.session_state.get("coding_room_submit"))
        if submit_requested:
            st.session_state.coding_room_submit = False
            clean_message = str(candidate_message or "").strip()
            if clean_message:
                pending_action = "message"
                pending_user_message = clean_message
                append_coding_room_message("user", clean_message)
                st.session_state.coding_room_clear_input = True

        if pending_action:
            with live_reply_container:
                response_placeholder = st.empty()
                response_placeholder.markdown(
                    format_zoswi_message_html("assistant", "...", first_name),
                    unsafe_allow_html=True,
                )
                response_text = ""
                for chunk in stream_coding_interviewer_reply(
                    pending_action,
                    pending_user_message,
                    stage,
                    stage_index,
                    first_name,
                ):
                    response_text += str(chunk)
                    response_placeholder.markdown(
                        format_zoswi_message_html("assistant", response_text + " \u258c", first_name),
                        unsafe_allow_html=True,
                    )
                if not response_text.strip():
                    response_text = "I did not get that fully. Share your approach in 2-3 steps and proceed with code."
                response_placeholder.markdown(
                    format_zoswi_message_html("assistant", response_text, first_name),
                    unsafe_allow_html=True,
                )
            append_coding_room_message("assistant", response_text)
            st.rerun()

    with right_col:
        difficulty_label = "Medium" if stage_index == 0 else ("Hard" if stage_index == 1 else "Expert")
        timer_value_label = "Expired" if timer_expired else format_timer_label(remaining_seconds)
        timer_value_class = "timer-alert" if timer_expired else "timer-safe"
        st.markdown(
            f"""
            <div class="coding-workspace-wrap">
                <div class="coding-workspace-top">
                    <div>
                        <p class="coding-workspace-title">Coding Workspace</p>
                        <p class="coding-workspace-sub">Focused implementation zone with stage-linked evaluation.</p>
                    </div>
                    <span class="coding-workspace-pill">\u2699 RUN PHASE</span>
                </div>
                <div class="coding-workspace-chips">
                    <div class="coding-tech-chip">
                        <p class="coding-tech-key">Stage</p>
                        <p class="coding-tech-value">{stage_index + 1}/{total_stages}</p>
                    </div>
                    <div class="coding-tech-chip">
                        <p class="coding-tech-key">Difficulty</p>
                        <p class="coding-tech-value">{difficulty_label}</p>
                    </div>
                    <div class="coding-tech-chip">
                        <p class="coding-tech-key">Focus</p>
                        <p class="coding-tech-value">{html.escape(str(stage.get("skill_focus", "")))}</p>
                    </div>
                    <div class="coding-tech-chip">
                        <p class="coding-tech-key">Timer</p>
                        <p id="{timer_dom_id}" class="coding-tech-value timer-live-display {timer_value_class}">{timer_value_label}</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if timer_expired:
            st.warning("Stage timer expired. Click Next Stage to auto-evaluate your current submission and continue.")
        render_live_stage_timer_widget(remaining_seconds, timer_dom_id, timer_instance_token)

        language_widget_key = f"coding_room_language_stage_{stage_index}"
        if language_widget_key not in st.session_state:
            st.session_state[language_widget_key] = st.session_state.get("coding_room_language", CODING_LANGUAGES[0])
        with st.container(key="coding_language_wrap"):
            selected_language = st.selectbox(
                "Runtime / Language",
                options=CODING_LANGUAGES,
                key=language_widget_key,
            )
        st.session_state.coding_room_language = selected_language
        language_token = _normalize_language_token(selected_language)
        language_ext_map = {
            "python": "py",
            "java": "java",
            "javascript": "js",
            "typescript": "ts",
            "go": "go",
            "c": "cpp",
            "c++": "cpp",
        }
        file_ext = language_ext_map.get(language_token, "txt")
        code_key = f"coding_room_code_stage_{stage_index}_{language_token}"
        if code_key not in st.session_state:
            st.session_state[code_key] = build_stage_starter_code(stage, selected_language)
        st.markdown(
            f"""
            <div class="coding-editor-shell">
                <div class="coding-editor-head">
                    <div class="coding-editor-tabs">
                        <div class="coding-editor-head-left">
                            <span class="coding-editor-dot red"></span>
                            <span class="coding-editor-dot yellow"></span>
                            <span class="coding-editor-dot green"></span>
                            <span class="coding-editor-file">stage_{stage_index + 1}_solution.{file_ext}</span>
                        </div>
                    </div>
                    <span class="coding-editor-status">{html.escape(selected_language)} | {int(stage.get("time_limit_min", 20))}m slot</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="coding_load_template_btn"):
            load_template_clicked = st.button(
                "Reload Starter Code",
                key=f"coding_load_template_{stage_index}_{language_token}",
                use_container_width=False,
            )
        if load_template_clicked:
            st.session_state[code_key] = build_stage_starter_code(stage, selected_language)
            st.rerun()
        with st.container(key="coding_editor_shell"):
            st.text_area(
                f"Stage {stage_index + 1} Solution",
                key=code_key,
                height=editor_height,
                placeholder=f"Write your {selected_language} solution here...",
            )
        render_solution_editor_security_guard()
        st.caption("Copy/paste is disabled in the solution editor for assessment integrity.")

        stage_code_current = str(st.session_state.get(code_key, "")).strip()
        stage_code_hash = hashlib.sha256(stage_code_current.encode("utf-8")).hexdigest()
        raw_hidden_result = hidden_tests_map.get(stage_key, {})
        if not isinstance(raw_hidden_result, dict):
            raw_hidden_result = {}
        hidden_result = (
            raw_hidden_result
            if str(raw_hidden_result.get("code_hash", "")) == stage_code_hash
            else {}
        )
        hidden_ran = bool(hidden_result.get("ran", False))
        hidden_ready_for_eval = bool(hidden_result.get("ready_for_evaluation", False))

        if raw_hidden_result and not hidden_result:
            st.caption("Code changed after the last backend check. Click Evaluate Stage to run hidden tests again.")
        if hidden_result:
            total_tests = int(hidden_result.get("total", 0) or 0)
            passed_tests = int(hidden_result.get("passed", 0) or 0)
            failed_cases = hidden_result.get("failed_cases", [])
            if not isinstance(failed_cases, list):
                failed_cases = []
            status_label = "Ready for Evaluate Stage" if hidden_ready_for_eval else "Fix hidden test failures first"
            status_color = "green" if hidden_ready_for_eval else "orange"
            st.markdown(
                f"Hidden tests: **{passed_tests}/{max(1, total_tests)} passed** | :{status_color}[{status_label}]"
            )
            summary_text = str(hidden_result.get("summary", "")).strip()
            if summary_text:
                st.caption(summary_text)
            if failed_cases:
                st.caption(f"Failed cases: {', '.join(str(item) for item in failed_cases[:5])}")

        approach_key = f"coding_stage_approach_{stage_index}"
        if approach_key not in st.session_state:
            st.session_state[approach_key] = str(approaches_map.get(stage_key, "")).strip()
        with st.container(key="coding_stage_approach_wrap"):
            st.text_area(
                "Your Approach (required before Next Stage unless timer expires)",
                key=approach_key,
                height=120,
                placeholder="Explain your approach, edge cases, and complexity considerations...",
            )
        stage_approach_text = str(st.session_state.get(approach_key, "")).strip()
        approach_ok, approach_error = validate_stage_approach_text(stage_approach_text)
        if stage_approach_text and not approach_ok:
            st.warning(approach_error)
        if approach_ok:
            st.caption("Approach validation: ready")

        has_stage_score = stage_key in stage_scores
        can_go_next = timer_expired or (approach_ok and has_stage_score)
        if is_mobile:
            with st.container(key="coding_eval_btn"):
                evaluate_clicked = st.button(
                    "Evaluate Stage",
                    key=f"coding_eval_stage_btn_{stage_index}",
                    use_container_width=True,
                    disabled=timer_expired,
                )
            with st.container(key="coding_next_stage_btn"):
                next_label = "Next Stage" if stage_index < total_stages - 1 else "Finish Evaluation"
                next_clicked = st.button(
                    next_label,
                    key=f"coding_next_stage_btn_{stage_index}",
                    use_container_width=True,
                    disabled=not can_go_next,
                )
            with st.container(key="coding_reset_session_btn"):
                reset_clicked = st.button(
                    "Reset Session",
                    key=f"coding_reset_session_main_btn_{stage_index}",
                    use_container_width=True,
                )
        else:
            action_row = st.columns(3, gap="small")
            with action_row[0]:
                with st.container(key="coding_eval_btn"):
                    evaluate_clicked = st.button(
                        "Evaluate Stage",
                        key=f"coding_eval_stage_btn_{stage_index}",
                        use_container_width=True,
                        disabled=timer_expired,
                    )
            with action_row[1]:
                with st.container(key="coding_next_stage_btn"):
                    next_label = "Next Stage" if stage_index < total_stages - 1 else "Finish Evaluation"
                    next_clicked = st.button(
                        next_label,
                        key=f"coding_next_stage_btn_{stage_index}",
                        use_container_width=True,
                        disabled=not can_go_next,
                    )
            with action_row[2]:
                with st.container(key="coding_reset_session_btn"):
                    reset_clicked = st.button(
                        "Reset Session",
                        key=f"coding_reset_session_main_btn_{stage_index}",
                        use_container_width=True,
                    )
        if not timer_expired:
            st.caption("Evaluate Stage runs hidden tests automatically in the backend.")
        else:
            st.caption("Timer expired: Next Stage will auto-evaluate your current code in the backend before moving on.")

        if evaluate_clicked:
            stage_code = stage_code_current
            hidden_result_payload = run_hidden_tests_for_submission(
                stage=stage,
                code=stage_code,
                language=selected_language,
                resume_text=resume_text,
                job_description=job_description,
            )
            updated_hidden = dict(hidden_tests_map)
            hidden_result_payload["code_hash"] = stage_code_hash
            updated_hidden[stage_key] = hidden_result_payload
            st.session_state.coding_room_hidden_tests = updated_hidden
            append_coding_room_message(
                "assistant",
                (
                    f"Hidden tests auto-run for Stage {stage_index + 1}: "
                    f"{int(hidden_result_payload.get('passed', 0))}/{int(hidden_result_payload.get('total', 0))} passed."
                ),
            )
            if not bool(hidden_result_payload.get("ready_for_evaluation", False)):
                append_coding_room_message(
                    "assistant",
                    "Evaluation blocked because hidden tests are not passing yet. Update code and evaluate again.",
                )
                st.rerun()
            result = evaluate_coding_submission(
                stage=stage,
                code=stage_code,
                language=selected_language,
                resume_text=resume_text,
                job_description=job_description,
            )
            updated_scores = dict(stage_scores)
            updated_scores[str(stage_index)] = result
            st.session_state.coding_room_stage_scores = updated_scores
            append_coding_room_message(
                "assistant",
                (
                    f"Stage {stage_index + 1} evaluation complete: {result.get('score', 0)}% ({result.get('verdict', '')}). "
                    f"Next step: {result.get('next_step', '')}"
                ),
            )
            st.rerun()

        current_stage_result = stage_scores.get(str(stage_index), {})
        if isinstance(current_stage_result, dict) and current_stage_result:
            score = int(current_stage_result.get("score", 0))
            st.markdown(
                f"""
                <div class="coding-score-card">
                    <h4>Stage {stage_index + 1} Score: {score}% ({html.escape(str(current_stage_result.get("verdict", "")))})</h4>
                    <p><strong>Strengths:</strong> {html.escape('; '.join(current_stage_result.get("strengths", [])))}</p>
                    <p><strong>Improvements:</strong> {html.escape('; '.join(current_stage_result.get("improvements", [])))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if next_clicked:
            if not timer_expired and not approach_ok:
                st.error(approach_error)
            else:
                updated_approaches = dict(approaches_map)
                if stage_approach_text:
                    updated_approaches[stage_key] = stage_approach_text
                st.session_state.coding_room_stage_approaches = updated_approaches

                updated_scores = dict(stage_scores)
                if stage_key not in updated_scores:
                    if timer_expired:
                        stage_code = stage_code_current
                        hidden_result_payload = run_hidden_tests_for_submission(
                            stage=stage,
                            code=stage_code,
                            language=selected_language,
                            resume_text=resume_text,
                            job_description=job_description,
                        )
                        latest_hidden_tests = st.session_state.get("coding_room_hidden_tests", {})
                        if not isinstance(latest_hidden_tests, dict):
                            latest_hidden_tests = {}
                        updated_hidden = dict(latest_hidden_tests)
                        hidden_result_payload["code_hash"] = stage_code_hash
                        updated_hidden[stage_key] = hidden_result_payload
                        st.session_state.coding_room_hidden_tests = updated_hidden
                        append_coding_room_message(
                            "assistant",
                            (
                                f"Timer expiry auto-check for Stage {stage_index + 1}: "
                                f"{int(hidden_result_payload.get('passed', 0))}/{int(hidden_result_payload.get('total', 0))} hidden tests passed."
                            ),
                        )

                        result = evaluate_coding_submission(
                            stage=stage,
                            code=stage_code,
                            language=selected_language,
                            resume_text=resume_text,
                            job_description=job_description,
                        )
                        if not bool(hidden_result_payload.get("ready_for_evaluation", False)):
                            existing_improvements = result.get("improvements", [])
                            if not isinstance(existing_improvements, list):
                                existing_improvements = [str(existing_improvements)]
                            result["improvements"] = [
                                "Timer-expiry auto-evaluation used the available code even though hidden tests were not fully passing.",
                                *[str(item) for item in existing_improvements if str(item).strip()],
                            ][:5]
                        result["next_step"] = "Stage timed out. Result captured from current submission and moved to next stage."
                        updated_scores[stage_key] = result
                        st.session_state.coding_room_stage_scores = updated_scores
                        append_coding_room_message(
                            "assistant",
                            (
                                f"Stage {stage_index + 1} auto-evaluated at timeout: "
                                f"{result.get('score', 0)}% ({result.get('verdict', '')})."
                            ),
                        )
                    else:
                        st.error("Run Evaluate Stage first (or wait for timer expiry) before moving ahead.")
                        updated_scores = {}

                if updated_scores:
                    if stage_index < total_stages - 1:
                        st.session_state.coding_room_stage_index = stage_index + 1
                        next_stage = stages[stage_index + 1]
                        append_coding_room_message(
                            "assistant",
                            (
                                f"Great. Moving to Stage {stage_index + 2}/{total_stages}: {next_stage.get('title', '')}. "
                                "Share approach first, then complete the starter code."
                            ),
                        )
                        st.rerun()
                    overall_scores = []
                    final_scores = st.session_state.get("coding_room_stage_scores", {})
                    if not isinstance(final_scores, dict):
                        final_scores = {}
                    for idx in range(total_stages):
                        result = final_scores.get(str(idx))
                        if isinstance(result, dict):
                            overall_scores.append(int(result.get("score", 0)))
                    overall_score = int(sum(overall_scores) / max(1, len(overall_scores)))
                    st.success(
                        f"Coding journey complete. Overall score: {overall_score}% ({summarize_coding_stage_score(overall_score)})."
                    )

        if reset_clicked:
            st.session_state.coding_room_source_sig = ""
            st.session_state.coding_room_payload = None
            st.session_state.coding_room_stage_index = 0
            st.session_state.coding_room_stage_scores = {}
            st.session_state.coding_room_messages = []
            st.session_state.coding_room_session_started = False
            st.session_state.coding_room_clear_input = True
            st.session_state.coding_room_scroll_pending = False
            st.session_state.coding_room_stage_started_at = {}
            st.session_state.coding_room_hidden_tests = {}
            st.session_state.coding_room_stage_approaches = {}
            st.rerun()

    if stage_scores:
        st.markdown("### Coding Evaluation Snapshot")
        approach_summary_map = st.session_state.get("coding_room_stage_approaches", {})
        if not isinstance(approach_summary_map, dict):
            approach_summary_map = {}
        summary_rows: list[dict[str, str]] = []
        for idx in range(total_stages):
            result = stage_scores.get(str(idx), {})
            approach_status = "Provided" if str(approach_summary_map.get(str(idx), "")).strip() else "Missing"
            if not isinstance(result, dict) or not result:
                summary_rows.append(
                    {
                        "Stage": f"Stage {idx + 1}",
                        "Title": str(stages[idx].get("title", "")),
                        "Score": "--",
                        "Verdict": "Pending",
                        "Approach": approach_status,
                    }
                )
                continue
            summary_rows.append(
                {
                    "Stage": f"Stage {idx + 1}",
                    "Title": str(stages[idx].get("title", "")),
                    "Score": f"{int(result.get('score', 0))}%",
                    "Verdict": str(result.get("verdict", "")),
                    "Approach": approach_status,
                }
            )
        st.dataframe(summary_rows, use_container_width=True, hide_index=True)



