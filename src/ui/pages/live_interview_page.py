from __future__ import annotations

# Transitional extraction: page rendering moved out of app_runtime.
from src.app_runtime import *  # noqa: F401,F403


def render_live_interview_view(user: dict[str, Any]) -> None:
    full_name = str(user.get("full_name", "")).strip()
    default_name = full_name or "Candidate"
    default_role = str(user.get("role", "")).strip() or "Software Engineer"

    if not str(st.session_state.get("live_interview_candidate_name", "")).strip():
        st.session_state.live_interview_candidate_name = default_name
    if not str(st.session_state.get("live_interview_role", "")).strip():
        st.session_state.live_interview_role = default_role
    st.session_state.live_interview_requirement_type = normalize_interview_requirement_type(
        str(st.session_state.get("live_interview_requirement_type", "mixed"))
    )

    st.markdown(
        """
        <style>
        .live-intv-shell {
            border: 1px solid #dbeafe;
            border-radius: 18px;
            padding: 1rem;
            background:
                radial-gradient(760px 250px at -10% -12%, rgba(14, 165, 233, 0.14) 0%, transparent 56%),
                radial-gradient(580px 240px at 100% 0%, rgba(20, 184, 166, 0.14) 0%, transparent 58%),
                #ffffff;
            box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
        }
        .live-intv-title {
            margin: 0;
            color: #0f172a;
            font-size: 1.38rem;
            line-height: 1.2;
            font-weight: 900;
        }
        .live-intv-sub {
            margin: 0.28rem 0 0 0;
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .live-intv-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            margin-top: 0.35rem;
            border-radius: 999px;
            border: 1px solid #0284c7;
            background: linear-gradient(130deg, #22d3ee 0%, #0284c7 100%);
            color: #ffffff;
            font-weight: 700;
            text-decoration: none;
            padding: 0.5rem 0.86rem;
            box-shadow: 0 10px 20px rgba(2, 132, 199, 0.24);
        }
        .live-intv-link:hover {
            filter: brightness(1.05);
            text-decoration: none;
            color: #ffffff;
        }
        .live-intv-url {
            margin-top: 0.45rem;
            font-size: 0.72rem;
            color: #334155;
            word-break: break-all;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.55rem 0.7rem;
        }
        </style>
        <div class="live-intv-shell">
            <h2 class="live-intv-title">Live AI Interview Integration</h2>
            <p class="live-intv-sub">
                Launch your real-time ZoSwi interview room with candidate context and requirement type.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Interview Launch Setup")
    is_mobile = is_mobile_browser()
    if is_mobile:
        candidate_name = st.text_input("Candidate Name", key="live_interview_candidate_name")
        target_role = st.text_input("Target Role", key="live_interview_role")
        requirement_type = st.selectbox(
            "Requirement Type",
            options=["mixed", "technical", "behavioral"],
            key="live_interview_requirement_type",
            format_func=lambda value: str(value).title(),
        )
    else:
        col1, col2, col3 = st.columns([3.6, 3.2, 2.2], gap="small")
        with col1:
            candidate_name = st.text_input("Candidate Name", key="live_interview_candidate_name")
        with col2:
            target_role = st.text_input("Target Role", key="live_interview_role")
        with col3:
            requirement_type = st.selectbox(
                "Requirement Type",
                options=["mixed", "technical", "behavioral"],
                key="live_interview_requirement_type",
                format_func=lambda value: str(value).title(),
            )

    requirement_type = normalize_interview_requirement_type(requirement_type)
    launch_url = build_zoswi_live_interview_launch_url(candidate_name, target_role, requirement_type)
    base_url = get_zoswi_live_interview_base_url()

    if not base_url:
        st.error(
            "Interview app URL is not configured. Set ZOSWI_INTERVIEW_APP_URL in env or [interview].app_url in "
            "Streamlit secrets."
        )
        return

    if not launch_url:
        st.warning("Enter both candidate name and target role to generate the launch URL.")
        return

    open_now = st.button("Open Live Interview in New Tab", key="live_interview_open_btn", use_container_width=True)
    safe_launch_url = html.escape(launch_url, quote=True)

    if open_now:
        st.components.v1.html(
            f"<script>window.open('{safe_launch_url}', '_blank', 'noopener,noreferrer');</script>",
            height=0,
        )

    st.markdown(
        f'<a class="live-intv-link" href="{safe_launch_url}" target="_blank" rel="noopener noreferrer">'
        "Launch Live Interview</a>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="live-intv-url">{safe_launch_url}</div>', unsafe_allow_html=True)

    embed_inside = st.toggle("Embed interview inside Streamlit (beta)", key="live_interview_embed")
    if embed_inside:
        iframe_height = 620 if is_mobile else 840
        st.components.v1.html(
            f"""
            <iframe
                src="{safe_launch_url}"
                style="width:100%;height:{iframe_height}px;border:1px solid #dbeafe;border-radius:16px;background:#fff;"
                allow="microphone; camera; autoplay; clipboard-read; clipboard-write"
            ></iframe>
            """,
            height=iframe_height + 30,
            scrolling=True,
        )
        st.caption("If mic/camera permissions are blocked in embed mode, use the new-tab launch button.")
