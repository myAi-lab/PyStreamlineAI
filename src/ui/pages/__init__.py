"""Page-level UI modules for dashboard sections."""

from .ai_workspace_page import render_ai_workspace_view
from .careers_page import render_careers_profile_setup, render_careers_motivation_hero, render_job_match_mvp_panel, render_careers_view
from .coding_room_page import render_coding_room_view
from .immigration_updates import render_immigration_updates_view

__all__ = [
    "render_ai_workspace_view",
    "render_careers_profile_setup",
    "render_careers_motivation_hero",
    "render_job_match_mvp_panel",
    "render_careers_view",
    "render_coding_room_view",
    "render_immigration_updates_view",
]

