from __future__ import annotations

# Transitional extraction: page rendering moved out of app_runtime.
from src.app_runtime import *  # noqa: F401,F403

def render_ai_workspace_view(user: dict[str, Any]) -> None:
    full_name = str(user.get("full_name", "")).strip()
    first_name = full_name.split()[0] if full_name else "Candidate"
    user_name_label = first_name if first_name else "Candidate"
    email = str(user.get("email", "")).strip().lower()
    logo_data_uri = get_logo_data_uri()

    if st.session_state.get("ai_workspace_clear_input"):
        st.session_state.ai_workspace_input = ""
        st.session_state.ai_workspace_clear_input = False

    unlocked_in_db = has_promo_redemption(email)
    if bool(st.session_state.get("ai_workspace_unlock_ok")) != unlocked_in_db:
        st.session_state.ai_workspace_unlock_ok = unlocked_in_db
        if unlocked_in_db and not str(st.session_state.get("ai_workspace_unlock_status", "")).strip():
            st.session_state.ai_workspace_unlock_status = "Access unlocked for this account."

    if not st.session_state.get("ai_workspace_messages"):
        st.session_state.ai_workspace_messages = default_ai_workspace_messages(full_name)
    else:
        # Clean up legacy user entries that may contain full attached-file payloads.
        current_msgs = st.session_state.get("ai_workspace_messages", [])
        if isinstance(current_msgs, list):
            updated_msgs: list[dict[str, str]] = []
            changed = False
            for msg in current_msgs:
                role = str(msg.get("role", "")).strip().lower()
                raw_content = str(msg.get("content", ""))
                if role == "user":
                    compact = compress_ai_workspace_user_message(raw_content)
                    if compact != raw_content:
                        changed = True
                    updated_msgs.append({"role": "user", "content": compact})
                else:
                    updated_msgs.append({"role": "assistant", "content": raw_content})
            if changed:
                st.session_state.ai_workspace_messages = updated_msgs

    st.markdown(
        """
        <style>
        .ai-workspace-shell {
            border: 1px solid #dbeafe;
            border-radius: 16px;
            background:
                radial-gradient(800px 300px at -8% -18%, rgba(14, 165, 233, 0.18) 0%, transparent 58%),
                radial-gradient(680px 260px at 108% 0%, rgba(20, 184, 166, 0.16) 0%, transparent 62%),
                #ffffff;
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
            padding: 0.92rem;
        }
        .ai-workspace-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.7rem;
            margin-bottom: 0.64rem;
        }
        .ai-workspace-title {
            margin: 0;
            color: #0f172a;
            font-size: 1.18rem;
            line-height: 1.2;
            font-weight: 900;
            display: inline-flex;
            align-items: baseline;
            gap: 0.42rem;
        }
        .ai-workspace-title-brand {
            background: linear-gradient(120deg, #67e8f9 0%, #60a5fa 34%, #a78bfa 68%, #c084fc 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .ai-workspace-title-role {
            color: #0f172a;
        }
        .ai-workspace-sub {
            margin: 0.2rem 0 0 0;
            color: #475569;
            font-size: 0.84rem;
        }
        .ai-workspace-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.36rem;
            border: 1px solid #99f6e4;
            background: #f0fdfa;
            color: #0f766e;
            border-radius: 999px;
            padding: 0.26rem 0.62rem;
            font-size: 0.75rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .ai-workspace-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #14b8a6;
            box-shadow: 0 0 0 6px rgba(20, 184, 166, 0.2);
            animation: aiWorkspacePulse 1.7s ease-out infinite;
        }
        @keyframes aiWorkspacePulse {
            0% { transform: scale(0.85); opacity: 0.88; }
            70% { transform: scale(1.12); opacity: 1; }
            100% { transform: scale(0.86); opacity: 0.84; }
        }
        .st-key-ai_workspace_unlock_apply_btn button,
        .st-key-ai_workspace_insert_btn button,
        .st-key-ai_workspace_insert_send_btn button,
        .st-key-ai_workspace_send_btn button {
            border-radius: 999px !important;
            min-height: 2.05rem !important;
            font-size: 0.76rem !important;
            font-weight: 700 !important;
            padding: 0.18rem 0.62rem !important;
        }
        .st-key-ai_workspace_unlock_apply_btn button {
            border: 1px solid #0f766e !important;
            background: linear-gradient(130deg, #14b8a6 0%, #0ea5e9 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 8px 18px rgba(20, 184, 166, 0.22) !important;
        }
        .st-key-ai_workspace_insert_send_btn button,
        .st-key-ai_workspace_send_btn button {
            border: 1px solid #0f766e !important;
            background: linear-gradient(130deg, #14b8a6 0%, #0284c7 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 8px 18px rgba(2, 132, 199, 0.2) !important;
        }
        .st-key-ai_workspace_reset_btn button {
            border-radius: 999px !important;
            width: 1.96rem !important;
            min-width: 1.96rem !important;
            max-width: 1.96rem !important;
            min-height: 1.96rem !important;
            padding: 0 !important;
            font-size: 0.92rem !important;
            font-weight: 800 !important;
            border: 1px solid #bfdbfe !important;
            background: #eff6ff !important;
            color: #1e3a8a !important;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.18) !important;
        }
        .st-key-ai_workspace_reset_btn {
            display: flex !important;
            justify-content: flex-end !important;
            align-items: center !important;
        }
        .st-key-ai_workspace_reset_btn button:hover {
            border-color: #93c5fd !important;
            background: #dbeafe !important;
        }
        .st-key-ai_workspace_unlock_shell [data-testid="stTextInput"] input,
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] input {
            min-height: 2.1rem !important;
            border-radius: 999px !important;
            border: 1px solid #cbd5e1 !important;
            padding-left: 0.82rem !important;
        }
        .st-key-ai_workspace_input_wrap {
            border: 1px solid #cfe3f7 !important;
            border-radius: 16px !important;
            padding: 0.3rem 0.34rem !important;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06) !important;
        }
        .st-key-ai_workspace_input_wrap [data-testid="stHorizontalBlock"] {
            align-items: center !important;
        }
        .st-key-ai_workspace_prefix_wrap {
            position: relative !important;
            min-height: 2rem !important;
            display: flex !important;
            align-items: center !important;
            overflow: visible !important;
            margin-right: -0.18rem !important;
        }
        .aiws-prefix-visual {
            display: inline-flex;
            align-items: center;
            gap: 0.24rem;
            min-height: 2rem;
            color: #0f172a;
            white-space: nowrap;
            user-select: none;
            pointer-events: none;
        }
        .aiws-prefix-plus {
            font-size: 1.5rem;
            line-height: 1;
            font-weight: 900;
            color: #082f49;
            text-shadow: 0 1px 0 rgba(255, 255, 255, 0.88), 0 0 1px rgba(8, 47, 73, 0.2);
            margin-right: 0.02rem;
        }
        .aiws-prefix-brand {
            font-size: 0.82rem;
            font-weight: 900;
            letter-spacing: 0.01em;
            color: #8b5cf6;
            background: linear-gradient(120deg, #67e8f9 0%, #60a5fa 34%, #a78bfa 68%, #c084fc 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
            position: relative;
            top: 2px;
        }
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] {
            margin-bottom: 0 !important;
        }
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] > div {
            border: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] input {
            border-color: #93c5fd !important;
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.85),
                0 1px 2px rgba(14, 116, 144, 0.08) !important;
            background: #ffffff !important;
        }
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] input:focus,
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] input:focus-visible,
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] input[aria-invalid="true"] {
            border-color: #0284c7 !important;
            box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.16) !important;
            outline: none !important;
        }
        .st-key-ai_workspace_input_wrap [data-testid="stTextInput"] input:invalid {
            border-color: #93c5fd !important;
            box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.12) !important;
        }
        .st-key-ai_workspace_chat_wrap {
            border: 1px solid #dbeafe;
            border-radius: 14px;
            padding: 0.45rem;
            margin-top: 0.5rem;
            background:
                url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='340' height='140' viewBox='0 0 340 140'%3E%3Ctext x='50%25' y='54%25' dominant-baseline='middle' text-anchor='middle' font-family='Segoe UI,Arial,sans-serif' font-size='52' font-weight='700' fill='%230284c7' fill-opacity='0.11'%3EZoSwi%3C/text%3E%3C/svg%3E"),
                linear-gradient(transparent 96%, rgba(148, 163, 184, 0.05) 96%),
                linear-gradient(90deg, rgba(148, 163, 184, 0.03) 1px, transparent 1px),
                linear-gradient(180deg, rgba(239, 246, 255, 0.74) 0%, rgba(248, 250, 252, 0.96) 46%, #ffffff 100%);
            background-repeat: no-repeat, repeat, repeat, no-repeat;
            background-position: center center, 0 0, 0 0, center center;
            background-size: 220px auto, 100% 1.55rem, 1.55rem 100%, 100% 100%;
        }
        .st-key-ai_workspace_insert_wrap [data-testid="stSelectbox"] > label {
            display: none !important;
        }
        .st-key-ai_workspace_insert_wrap [data-testid="stSelectbox"] {
            max-width: 420px !important;
        }
        .st-key-ai_workspace_insert_wrap {
            margin: 0.02rem 0 0.1rem 0 !important;
        }
        .st-key-ai_workspace_insert_wrap [data-testid="stHorizontalBlock"] {
            align-items: center !important;
            flex-wrap: nowrap !important;
        }
        .st-key-ai_workspace_insert_wrap [data-baseweb="select"] > div {
            min-height: 1.9rem !important;
            border-radius: 12px !important;
            border: 1px solid #bfdbfe !important;
            background: #ffffff !important;
            box-shadow: 0 1px 2px rgba(2, 132, 199, 0.08) !important;
        }
        .st-key-ai_workspace_insert_wrap [data-baseweb="select"] span {
            font-size: 0.78rem !important;
            font-weight: 600 !important;
        }
        .st-key-ai_workspace_insert_btn button {
            min-height: 1.9rem !important;
            border-radius: 10px !important;
            padding: 0.06rem 0.72rem !important;
            font-size: 0.74rem !important;
            font-weight: 800 !important;
            border: 1px solid #bfdbfe !important;
            background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%) !important;
            color: #1e3a8a !important;
            box-shadow: 0 1px 2px rgba(30, 58, 138, 0.1) !important;
        }
        .st-key-ai_workspace_insert_send_btn button {
            min-height: 1.9rem !important;
            border-radius: 10px !important;
            padding: 0.06rem 0.76rem !important;
            font-size: 0.74rem !important;
            font-weight: 800 !important;
            border: 1px solid #14b8a6 !important;
            background: linear-gradient(135deg, #14b8a6 0%, #0ea5e9 100%) !important;
            color: #f8fafc !important;
            box-shadow: 0 2px 6px rgba(14, 116, 144, 0.24) !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploader"] > label {
            display: none !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploader"] {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 1.5rem !important;
            min-width: 1.5rem !important;
            max-width: 1.5rem !important;
            height: 2rem !important;
            min-height: 2rem !important;
            overflow: hidden !important;
            padding: 0 !important;
            margin: 0 !important;
            z-index: 2 !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzone"] {
            border-radius: 0 !important;
            padding: 0 !important;
            min-height: 2rem !important;
            height: 2rem !important;
            width: 1.5rem !important;
            border: 0 !important;
            background: transparent !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: none !important;
            position: relative !important;
            overflow: hidden !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzone"]::before {
            content: "" !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzone"] button {
            position: absolute !important;
            inset: 0 !important;
            width: 100% !important;
            min-width: 100% !important;
            height: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            opacity: 0 !important;
            color: transparent !important;
            font-size: 0 !important;
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            cursor: pointer !important;
            z-index: 2 !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzoneInstructions"],
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzoneInstructions"] > div,
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzoneInstructions"] small,
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderFileName"],
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderFile"],
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderUploadedFile"],
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDeleteBtn"],
        .st-key-ai_workspace_prefix_wrap [class*="uploadedFile"],
        .st-key-ai_workspace_prefix_wrap [class*="fileUploaderFile"],
        .st-key-ai_workspace_prefix_wrap [class*="fileUploaderUploadedFile"],
        .st-key-ai_workspace_prefix_wrap small {
            display: none !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzone"]:hover {
            border: 0 !important;
            background: transparent !important;
        }
        .st-key-ai_workspace_prefix_wrap [data-testid="stFileUploaderDropzone"] > div {
            display: none !important;
        }
        .st-key-ai_workspace_send_btn button {
            min-height: 2rem !important;
            border-radius: 10px !important;
            font-size: 0.8rem !important;
            letter-spacing: 0 !important;
            border: 1px solid #0ea5e9 !important;
            background: #e0f2fe !important;
            color: #0c4a6e !important;
            box-shadow: none !important;
        }
        .aiws-row {
            width: 100%;
            display: flex;
            margin-bottom: 0.52rem;
        }
        .aiws-chat-brand {
            display: inline-flex;
            align-items: center;
            gap: 0.36rem;
            margin: 0.06rem 0 0.48rem 0.08rem;
            font-size: 0.86rem;
            font-weight: 900;
            letter-spacing: 0.015em;
            color: #0f172a;
        }
        .aiws-chat-brand .brand-text {
            background: linear-gradient(120deg, #67e8f9 0%, #60a5fa 34%, #a78bfa 68%, #c084fc 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .aiws-chat-brand .brand-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: linear-gradient(120deg, #14b8a6 0%, #0ea5e9 58%, #a78bfa 100%);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.12);
            animation: aiwsLiveBlink 1.15s ease-in-out infinite;
            transform-origin: center;
        }
        @keyframes aiwsLiveBlink {
            0% {
                opacity: 0.42;
                transform: scale(0.84);
                box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.28);
            }
            50% {
                opacity: 1;
                transform: scale(1.02);
                box-shadow: 0 0 0 6px rgba(14, 165, 233, 0.1);
            }
            100% {
                opacity: 0.42;
                transform: scale(0.84);
                box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.22);
            }
        }
        .aiws-row.assistant {
            justify-content: flex-start;
        }
        .aiws-row.user {
            justify-content: flex-end;
        }
        .aiws-msg {
            border-radius: 14px;
            padding: 0.56rem 0.7rem;
            border: 1px solid transparent;
            max-width: min(86%, 930px);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
        }
        .aiws-msg.assistant {
            background: linear-gradient(132deg, #eef9ff 0%, #ecfeff 36%, #f5f3ff 70%, #faf5ff 100%);
            border-color: #a5b4fc;
        }
        .aiws-msg.user {
            background: linear-gradient(132deg, #f0f9ff 0%, #dcfce7 100%);
            border-color: #86efac;
        }
        .aiws-msg-head {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            margin-bottom: 0.2rem;
        }
        .aiws-msg-head.assistant {
            gap: 0.42rem;
        }
        .aiws-name {
            font-size: 0.86rem;
            font-weight: 950;
            color: #0f172a;
            letter-spacing: 0.01em;
        }
        .aiws-name.assistant {
            background: linear-gradient(120deg, #67e8f9 0%, #60a5fa 34%, #a78bfa 68%, #c084fc 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .aiws-name.user {
            color: #0f172a;
        }
        .aiws-msg-text {
            color: #0f172a;
            font-size: 0.85rem;
            line-height: 1.45;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .aiws-input-note {
            margin: 0.18rem auto 0.08rem auto;
            text-align: center;
            color: #6b7280;
            font-size: 0.72rem;
            line-height: 1.3;
            font-weight: 500;
            width: 100%;
            animation: aiwsInputNoteBlink 1.15s ease-in-out infinite;
        }
        @keyframes aiwsInputNoteBlink {
            0% {
                opacity: 0.42;
            }
            50% {
                opacity: 0.95;
            }
            100% {
                opacity: 0.42;
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
            .st-key-ai_workspace_chat_wrap {{
                background:
                    linear-gradient(rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.9)),
                    url("{logo_data_uri}"),
                    linear-gradient(transparent 96%, rgba(148, 163, 184, 0.05) 96%),
                    linear-gradient(90deg, rgba(148, 163, 184, 0.03) 1px, transparent 1px),
                    linear-gradient(180deg, rgba(239, 246, 255, 0.74) 0%, rgba(248, 250, 252, 0.96) 46%, #ffffff 100%) !important;
                background-repeat: no-repeat, no-repeat, repeat, repeat, no-repeat !important;
                background-position: center center, center center, 0 0, 0 0, center center !important;
                background-size: 100% 100%, 520px auto, 100% 1.55rem, 1.55rem 100%, 100% 100% !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="ai-hero">
            <div class="ai-chip">Promo Workspace</div>
            <h1>ZoSwi AI Workspace</h1>
            <p>Chat in a full-screen assistant experience with real-time streaming responses for {html.escape(first_name)}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not bool(st.session_state.get("ai_workspace_unlock_ok")):
        st.info("Unlock AI Workspace with your promo code. This access can be redeemed once per account.")
        with st.container(key="ai_workspace_unlock_shell"):
            _, center_col, _ = st.columns([1.2, 2.6, 1.2], gap="small")
            with center_col:
                unlock_cols = st.columns([4.0, 1.15], gap="small")
                with unlock_cols[0]:
                    promo_code_text = st.text_input(
                        "Promo code",
                        key="ai_workspace_unlock_code",
                        placeholder="Enter promo code",
                        label_visibility="collapsed",
                    )
                with unlock_cols[1]:
                    unlock_clicked = st.button(
                        "Unlock",
                        key="ai_workspace_unlock_apply_btn",
                        use_container_width=True,
                    )
        if unlock_clicked:
            ok_unlock, unlock_message = redeem_promo_code(promo_code_text, email)
            st.session_state.ai_workspace_unlock_ok = bool(ok_unlock)
            st.session_state.ai_workspace_unlock_status = unlock_message
            if ok_unlock:
                st.rerun()
        unlock_status = str(st.session_state.get("ai_workspace_unlock_status", "")).strip()
        if unlock_status:
            if bool(st.session_state.get("ai_workspace_unlock_ok")):
                st.success(unlock_status)
            else:
                st.error(unlock_status)
        return

    pending_prompt = st.session_state.get("ai_workspace_pending_prompt")
    waiting_for_reply = bool(pending_prompt)
    st.caption("Access active for this account.")
    with st.container(key="ai_workspace_shell"):
        st.markdown(
            """
            <div class="ai-workspace-shell">
                <div class="ai-workspace-top">
                    <div>
                        <p class="ai-workspace-title"><span class="ai-workspace-title-brand">ZoSwi</span><span class="ai-workspace-title-role">Assistant</span></p>
                        <p class="ai-workspace-sub">Natural conversational mode tuned for practical, high-quality answers.</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="ai_workspace_chat_wrap"):
            header_cols = st.columns([9.1, 0.9], gap="small")
            with header_cols[0]:
                st.markdown(
                    '<div class="aiws-chat-brand"><span class="brand-dot"></span><span class="brand-text">ZoSwi</span></div>',
                    unsafe_allow_html=True,
                )
            with header_cols[1]:
                if st.button("\u21bb", key="ai_workspace_reset_btn", help="Reset chat", use_container_width=False):
                    st.session_state.ai_workspace_messages = default_ai_workspace_messages(full_name)
                    st.session_state.ai_workspace_pending_prompt = None
                    st.session_state.ai_workspace_clear_input = True
                    st.session_state.ai_workspace_attachments = []
                    st.session_state.ai_workspace_upload_nonce = int(st.session_state.get("ai_workspace_upload_nonce", 0) or 0) + 1
                    st.rerun()
            with st.container(height=560):
                chat_history_container = st.container()
                live_reply_container = st.container()
                with chat_history_container:
                    for msg in st.session_state.get("ai_workspace_messages", []):
                        st.markdown(
                            format_ai_workspace_message_html(
                                str(msg.get("role", "assistant")),
                                str(msg.get("content", "")),
                                user_name_label,
                            ),
                            unsafe_allow_html=True,
                        )
                st.markdown('<div id="zoswi-scroll-anchor"></div>', unsafe_allow_html=True)
                render_zoswi_autoscroll()

        prompt_templates = {
            "Resume Improvement": "Review my resume and suggest 5 high-impact bullet improvements for the target role.",
            "JD Match Gaps": "Based on my JD analysis, what are my biggest skill gaps and how do I close them in 30 days?",
            "Interview Prep": "Ask me 5 technical interview questions for my role and then critique my answers.",
            "ATS Keywords": "Give me ATS keywords I should add for this job description and where to place them.",
            "Project Story": "Help me build a STAR story for one project with metrics and impact.",
        }
        if "ai_workspace_insert_topic" not in st.session_state:
            st.session_state.ai_workspace_insert_topic = next(iter(prompt_templates))
        with st.container(key="ai_workspace_insert_wrap"):
            insert_cols = st.columns([2.25, 0.86, 0.98, 5.91], gap="small")
            with insert_cols[0]:
                selected_topic = st.selectbox(
                    "Insert prompt topic",
                    options=list(prompt_templates.keys()),
                    key="ai_workspace_insert_topic",
                    label_visibility="collapsed",
                    disabled=waiting_for_reply,
                )
            with insert_cols[1]:
                insert_clicked = st.button(
                    "+ Insert",
                    key="ai_workspace_insert_btn",
                    use_container_width=True,
                    disabled=waiting_for_reply,
                )
            with insert_cols[2]:
                insert_send_clicked = st.button(
                    "Ask Now \u2192",
                    key="ai_workspace_insert_send_btn",
                    use_container_width=True,
                    disabled=waiting_for_reply,
                )
        st.caption("Use Insert to prefill, or Ask Now to send immediately.")
        selected_prompt = str(prompt_templates.get(selected_topic, "")).strip()
        if insert_clicked:
            st.session_state.ai_workspace_input = selected_prompt
            st.rerun()
        if insert_send_clicked and selected_prompt:
            ai_messages = st.session_state.get("ai_workspace_messages", [])
            if not isinstance(ai_messages, list):
                ai_messages = []
            ai_messages.append({"role": "user", "content": selected_prompt})
            st.session_state.ai_workspace_messages = ai_messages
            st.session_state.ai_workspace_pending_prompt = selected_prompt
            st.session_state.ai_workspace_clear_input = True
            st.rerun()

        upload_nonce = int(st.session_state.get("ai_workspace_upload_nonce", 0) or 0)
        upload_widget_key = f"ai_workspace_input_file_upload_{upload_nonce}"
        with st.container(key="ai_workspace_input_wrap"):
            row_cols = st.columns([0.54, 8.72, 0.74], gap="small")
            with row_cols[0]:
                with st.container(key="ai_workspace_prefix_wrap"):
                    st.markdown(
                        '<div class="aiws-prefix-visual"><span class="aiws-prefix-plus">+</span><span class="aiws-prefix-brand">ZoSwi</span></div>',
                        unsafe_allow_html=True,
                    )
                    attached_file = st.file_uploader(
                        "Attach file",
                        key=upload_widget_key,
                        type=AI_WORKSPACE_FILE_TYPES,
                        label_visibility="collapsed",
                        disabled=waiting_for_reply,
                    )
            with row_cols[1]:
                message = st.text_input(
                    "Message AI Workspace",
                    key="ai_workspace_input",
                    on_change=request_ai_workspace_submit,
                    placeholder="Ask anything...",
                    label_visibility="collapsed",
                    disabled=waiting_for_reply,
                )
            with row_cols[2]:
                send = st.button(
                    "\u2191",
                    key="ai_workspace_send_btn",
                    use_container_width=True,
                    help="Send",
                    disabled=waiting_for_reply,
                )
        st.markdown('<div class="aiws-input-note">ZoSwi can make mistakes. Please verify important responses.</div>', unsafe_allow_html=True)
        submit_requested = bool(send) or bool(st.session_state.get("ai_workspace_submit"))
        if submit_requested:
            st.session_state.ai_workspace_submit = False

        if submit_requested and not waiting_for_reply:
            clean_message = str(message or "").strip()
            final_message = clean_message
            display_message = clean_message
            if attached_file is not None:
                ok_file, file_text, file_notice = extract_ai_workspace_file_text(attached_file)
                if not ok_file:
                    st.error(file_notice)
                    final_message = ""
                    display_message = ""
                else:
                    uploaded_name = str(getattr(attached_file, "name", "") or "uploaded_file").strip() or "uploaded_file"
                    add_ai_workspace_attachment(uploaded_name, file_text)
                    if clean_message:
                        final_message = clean_message
                    else:
                        final_message = f"I attached file {uploaded_name}. Keep it as context for follow-up questions."
                    attach_line = f"Attached file: {uploaded_name}"
                    display_message = f"{clean_message}\n\n{attach_line}".strip() if clean_message else attach_line
            if final_message.strip():
                ai_messages = st.session_state.get("ai_workspace_messages", [])
                if not isinstance(ai_messages, list):
                    ai_messages = []
                ai_messages.append({"role": "user", "content": display_message.strip()})
                st.session_state.ai_workspace_messages = ai_messages
                st.session_state.ai_workspace_pending_prompt = final_message
                st.session_state.ai_workspace_clear_input = True
                st.session_state.ai_workspace_upload_nonce = upload_nonce + 1
                st.rerun()

        if pending_prompt:
            with live_reply_container:
                response_placeholder = st.empty()
                response_placeholder.markdown(
                    format_ai_workspace_message_html("assistant", "...", user_name_label),
                    unsafe_allow_html=True,
                )
                response_text = ""
                for chunk in ask_ai_workspace_stream(str(pending_prompt)):
                    response_text += str(chunk)
                    response_placeholder.markdown(
                        format_ai_workspace_message_html("assistant", response_text + " \u258c", user_name_label),
                        unsafe_allow_html=True,
                    )
                if not response_text.strip():
                    response_text = "I hit a temporary issue generating a response. Please try again."
                response_placeholder.markdown(
                    format_ai_workspace_message_html("assistant", response_text, user_name_label),
                    unsafe_allow_html=True,
                )

            ai_messages = st.session_state.get("ai_workspace_messages", [])
            if not isinstance(ai_messages, list):
                ai_messages = []
            ai_messages.append({"role": "assistant", "content": response_text})
            st.session_state.ai_workspace_messages = ai_messages
            st.session_state.ai_workspace_pending_prompt = None
            st.rerun()



