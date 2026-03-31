from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Legacy Streamlit entrypoint removed.\n"
        "Use the platform services instead:\n"
        "  Backend:  cd zoswi-ai-interview/backend  && uvicorn app.main:app --reload\n"
        "  Frontend: cd zoswi-ai-interview/frontend && npm run dev\n"
    )


if __name__ == "__main__":
    main()

