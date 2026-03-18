from __future__ import annotations

import streamlit as st

from src.dto.runtime_dto import AppRuntimeHandlersDTO, PageConfigDTO


def run_app_runtime(config: PageConfigDTO, handlers: AppRuntimeHandlersDTO) -> None:
    """Top-level controller for app startup and page routing."""
    st.set_page_config(
        page_title=config.page_title,
        layout=config.layout,
        initial_sidebar_state=config.initial_sidebar_state,
        page_icon=config.page_icon,
    )
    if not bool(st.session_state.get("_runtime_bootstrap_ready")):
        with st.spinner("Preparing your workspace..."):
            handlers.bootstrap_runtime()
        st.session_state._runtime_bootstrap_ready = True
    else:
        handlers.bootstrap_runtime()
    handlers.init_state()
    handlers.try_restore_user_from_cookie()
    handlers.sync_user_from_oauth_session()
    handlers.render_auth_cookie_sync()

    if handlers.get_current_user() is None:
        handlers.render_auth_screen()
        return
    handlers.render_main_screen()
