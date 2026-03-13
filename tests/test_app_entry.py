from __future__ import annotations

import app


def test_app_runner_run_calls_application_main(monkeypatch) -> None:
    state = {"called": False}

    monkeypatch.setattr(
        app,
        "application_main",
        lambda: state.__setitem__("called", True),
    )

    app.AppRunner.run()

    assert state["called"] is True


def test_main_calls_runner(monkeypatch) -> None:
    state = {"called": False}

    monkeypatch.setattr(
        app.AppRunner,
        "run",
        staticmethod(lambda: state.__setitem__("called", True)),
    )

    app.main()

    assert state["called"] is True
