from enum import StrEnum


class UserRole(StrEnum):
    CANDIDATE = "candidate"
    STUDENT = "student"
    RECRUITER = "recruiter"
    ADMIN = "admin"


class ResumeSourceType(StrEnum):
    UPLOAD = "upload"
    PASTED_TEXT = "pasted_text"


class ResumeParseStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InterviewStatus(StrEnum):
    CREATED = "created"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class InterviewMode(StrEnum):
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    MIXED = "mixed"


class JobType(StrEnum):
    RESUME_ANALYSIS = "resume_analysis"
    INTERVIEW_SUMMARY = "interview_summary"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
