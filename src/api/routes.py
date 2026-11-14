"""
src/api/routes.py — Endpoint definitions for the InterviewDNA REST API.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from config import settings
from src.api.deps import (
    get_active_sessions,
    get_archive_record_by_id,
    get_dna_builder,
    get_orchestrator,
    get_sqlite_store,
)
from src.api.schemas import (
    AgentTrace,
    CompaniesResponse,
    CompanyInfo,
    CreateSessionRequest,
    CreateSessionResponse,
    HealthResponse,
    SendMessageRequest,
    SendMessageResponse,
    UserProgressResponse,
)
from src.memory.session_memory import SessionMemory
from src.schemas.models import (
    InterviewState,
    SessionReport,
)
from src.schemas.rag import CompanyDNAProfile
from src.schemas.router import IntentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["InterviewDNA"])

# Company & round structure definitions
SUPPORTED_COMPANIES = [
    "Zoho",
    "Amazon",
    "Google",
    "TCS",
    "Infosys",
    "Accenture",
    "Deloitte",
    "Flipkart",
]

COMPANY_ROLES: dict[str, list[str]] = {
    "Zoho": ["Software Developer", "Member Technical Staff", "UI Developer", "DevOps Engineer"],
    "Amazon": ["SDE-I", "SDE-II", "Business Analyst", "Data Engineer", "Solutions Architect"],
    "Google": ["Software Engineer", "SWE-II", "Site Reliability Engineer", "Data Scientist"],
    "TCS": ["Software Engineer", "Data Analyst", "Systems Engineer", "Business Analyst"],
    "Infosys": ["Systems Engineer", "Technology Analyst", "Digital Specialist", "Process Executive"],
    "Accenture": ["Associate Software Engineer", "Analyst", "Cloud Engineer", "Packaged App Developer"],
    "Deloitte": ["Technology Analyst", "Analyst", "Consultant", "Risk Advisory Analyst"],
    "Flipkart": ["SDE-I", "SDE-II", "Data Engineer", "Platform Engineer", "Product Analyst"],
}

COMPANY_ROUND_STRUCTURES: dict[str, list[str]] = {
    "Zoho": ["Aptitude", "Technical", "Technical", "Technical", "HR"],
    "Amazon": ["Aptitude", "Technical", "Technical", "Managerial", "HR"],
    "Google": ["Technical", "Technical", "Technical", "Managerial", "HR"],
    "TCS": ["Aptitude", "Technical", "Managerial", "HR"],
    "Infosys": ["Aptitude", "Technical", "HR"],
    "Accenture": ["Aptitude", "Technical", "Managerial", "HR"],
    "Deloitte": ["Aptitude", "Technical", "Managerial", "HR"],
    "Flipkart": ["Aptitude", "Technical", "Technical", "Managerial", "HR"],
}


# -----------------------------------------------------------------------------
# 1. Health
# -----------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def get_health():
    """Health check endpoint to verify backend availability."""
    chroma_ready = False
    try:
        from src.api.deps import get_retriever
        r = get_retriever()
        chroma_ready = r is not None and getattr(r, "q_col", None) is not None and r.q_col.count() > 0
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        service="InterviewDNA API",
        version="1.0.0",
        models_loaded=True,
        chroma_ready=chroma_ready,
        llm_provider=getattr(settings, "llm_provider", "gemini"),
    )


# -----------------------------------------------------------------------------
# 2. Companies & Metadata
# -----------------------------------------------------------------------------

@router.get("/companies", response_model=CompaniesResponse)
async def get_companies():
    """Returns list of supported companies, target roles, and interview rounds."""
    details = [
        CompanyInfo(
            company=c,
            roles=COMPANY_ROLES.get(c, []),
            rounds=COMPANY_ROUND_STRUCTURES.get(c, ["Aptitude", "Technical", "HR"]),
        )
        for c in SUPPORTED_COMPANIES
    ]
    return CompaniesResponse(
        companies=SUPPORTED_COMPANIES,
        roles=COMPANY_ROLES,
        round_structures=COMPANY_ROUND_STRUCTURES,
        company_details=details,
    )


# -----------------------------------------------------------------------------
# 3. Company DNA Profile
# -----------------------------------------------------------------------------

@router.get("/companies/{company}/dna", response_model=CompanyDNAProfile)
async def get_company_dna(company: str, role: str | None = Query(default=None)):
    """
    Returns the statistical and behavioural DNA profile for a company/role.
    Includes topic distribution, difficulty trends, selection rate, and interviewer style.
    """
    # Normalize company case
    matched_company = next(
        (c for c in SUPPORTED_COMPANIES if c.lower() == company.strip().lower()),
        company.strip(),
    )
    dna_builder = get_dna_builder()
    try:
        profile = dna_builder.get_or_build(matched_company, role)
        return profile
    except Exception as exc:
        logger.error("Error building DNA for %s (%s): %s", matched_company, role, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Could not build Company DNA for '{company}': {exc}",
        )


# -----------------------------------------------------------------------------
# 4. Session Creation
# -----------------------------------------------------------------------------

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(payload: CreateSessionRequest):
    """
    Initializes a new interview session and retrieves the first question.
    """
    session_id = uuid.uuid4().hex[:12]
    sessions = get_active_sessions()
    sqlite_store = get_sqlite_store()
    orchestrator = get_orchestrator()

    initial_state = InterviewState(
        session_id=session_id,
        company=payload.company,
        role=payload.role,
        round_type=payload.round_mode,
        difficulty_level=payload.difficulty_mode,
    )

    memory = SessionMemory(
        session_id=session_id,
        company=payload.company,
        role=payload.role,
        round_type=payload.round_mode,
        difficulty_level=payload.difficulty_mode,
        user_nickname=payload.nickname,
        sqlite_store=sqlite_store,
        initial_state=initial_state,
    )
    sessions[session_id] = memory

    # Pick the opening interview question (style_with_llm=False for fast startup)
    first_turn = orchestrator.interviewer.run(memory, style_with_llm=False)

    return CreateSessionResponse(
        session_id=session_id,
        company=payload.company,
        role=payload.role,
        round_type=payload.round_mode,
        difficulty_level=payload.difficulty_mode,
        first_question=first_turn,
        message=f"Session {session_id} initialized. Question #1 ready.",
    )


# -----------------------------------------------------------------------------
# 5. Send Message (Turn Evaluation & Routing)
# -----------------------------------------------------------------------------

@router.post("/sessions/{session_id}/message", response_model=SendMessageResponse)
async def send_message(session_id: str, payload: SendMessageRequest):
    """
    Processes a candidate's answer or prompt through the Intent Router and agents.
    Returns routed agent, score evaluation, coaching advice, or follow-up question.
    """
    sessions = get_active_sessions()
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Please create a session first.",
        )

    memory = sessions[session_id]
    orchestrator = get_orchestrator()

    start_time = time.perf_counter()
    try:
        result = orchestrator.handle_message(
            session_id=session_id,
            user_message=payload.message,
            sessions_dict=sessions,
            company=memory.state.company,
            role=memory.state.role,
            user_nickname=memory.user_nickname,
        )
    except Exception as exc:
        logger.error("Error processing message for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Turn execution failed: {exc}",
        )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    routing = result["routing"]

    # Build agent trace
    retrieved_count = 0
    fallback_level = "none"
    if routing.intent in (IntentType.PRACTICE, IntentType.COACH):
        retrieved_count = 5
        fallback_level = "company_role"

    trace = AgentTrace(
        retrieved_count=retrieved_count,
        fallback_level=fallback_level,
        latency_ms=latency_ms,
    )

    turn = result.get("turn")
    is_fu = turn.is_followup if turn else False

    return SendMessageResponse(
        routed_to=routing.target_agent,
        confidence=routing.confidence,
        reply_type=routing.intent.value,
        response_text=result.get("response", ""),
        question=turn if (turn and not is_fu) else None,
        evaluation=result.get("evaluation"),
        coaching=result.get("coaching"),
        followup=turn if (turn and is_fu) else None,
        agent_trace=trace,
    )


# -----------------------------------------------------------------------------
# 6. Stream Response via Server-Sent Events (SSE)
# -----------------------------------------------------------------------------

@router.get("/sessions/{session_id}/stream")
async def stream_session_message(session_id: str, message: str = Query(..., min_length=1, max_length=4000)):
    """
    Server-Sent Events endpoint streaming real-time tokens and agent activity.
    Allows frontend to show dynamic typing indicators and live agent trace badges.
    """
    sessions = get_active_sessions()
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Please create a session first.",
        )

    memory = sessions[session_id]
    orchestrator = get_orchestrator()

    async def event_generator():
        yield f"data: {json.dumps({'event': 'start', 'session_id': session_id})}\n\n"
        yield f"data: {json.dumps({'event': 'status', 'stage': 'routing', 'message': 'Classifying intent and retrieving company context...' })}\n\n"

        start_time = time.perf_counter()
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: orchestrator.handle_message(
                    session_id=session_id,
                    user_message=message,
                    sessions_dict=sessions,
                    company=memory.state.company,
                    role=memory.state.role,
                    user_nickname=memory.user_nickname,
                ),
            )
        except Exception as exc:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(exc)})}\n\n"
            return

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        routing = result["routing"]

        # 1. Routing event
        yield f"data: {json.dumps({'event': 'routing', 'data': {'routed_to': routing.target_agent, 'confidence': routing.confidence, 'intent': routing.intent.value}})}\n\n"

        # 2. Agent trace event
        trace_data = {
            "retrieved_count": 5 if routing.intent in (IntentType.PRACTICE, IntentType.COACH) else 0,
            "fallback_level": "company_role",
            "latency_ms": latency_ms,
        }
        yield f"data: {json.dumps({'event': 'trace', 'data': trace_data})}\n\n"

        # 3. Stream response text chunks
        response_text = result.get("response", "")
        words = response_text.split(" ")
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size]) + (" " if i + chunk_size < len(words) else "")
            yield f"data: {json.dumps({'event': 'token', 'content': chunk})}\n\n"
            await asyncio.sleep(0.02)

        # 4. Final structured completion event
        turn = result.get("turn")
        is_fu = turn.is_followup if turn else False
        complete_payload = {
            "routed_to": routing.target_agent,
            "confidence": routing.confidence,
            "reply_type": routing.intent.value,
            "response_text": response_text,
            "evaluation": result["evaluation"].model_dump() if result.get("evaluation") else None,
            "coaching": result["coaching"].model_dump() if result.get("coaching") else None,
            "question": turn.model_dump() if (turn and not is_fu) else None,
            "followup": turn.model_dump() if (turn and is_fu) else None,
            "agent_trace": trace_data,
        }
        yield f"data: {json.dumps({'event': 'complete', 'data': complete_payload})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# -----------------------------------------------------------------------------
# 7. End Session & Compile Report
# -----------------------------------------------------------------------------

@router.post("/sessions/{session_id}/end", response_model=SessionReport)
async def end_session(session_id: str):
    """
    Finalizes the interview, generates post-interview analytics, compiles
    PDF + Markdown scorecards, and saves results to SQLite.
    """
    sessions = get_active_sessions()
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )

    memory = sessions[session_id]
    orchestrator = get_orchestrator()
    dna_builder = get_dna_builder()

    try:
        dna = dna_builder.get_or_build(memory.state.company, memory.state.role)
        report = orchestrator.report_agent.run(memory, dna_profile=dna)
        return report
    except Exception as exc:
        logger.error("Failed to generate report for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Report compilation failed: {exc}",
        )


# -----------------------------------------------------------------------------
# 8. Report Downloads (PDF & Markdown)
# -----------------------------------------------------------------------------

@router.get("/sessions/{session_id}/report.pdf")
async def download_report_pdf(session_id: str):
    """Downloads the generated PDF scorecard for a session."""
    reports_dir = Path(settings.archive_csv_path).parent / "reports"
    pdf_path = reports_dir / f"{session_id}.pdf"

    if not pdf_path.exists():
        # Try compiling if session is in memory
        sessions = get_active_sessions()
        if session_id in sessions:
            try:
                orch = get_orchestrator()
                dna = get_dna_builder().get_or_build(sessions[session_id].state.company, sessions[session_id].state.role)
                orch.report_agent.run(sessions[session_id], dna_profile=dna)
            except Exception as exc:
                logger.warning("Could not automatically compile report: %s", exc)

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"PDF report for session '{session_id}' not found.",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"InterviewDNA_Report_{session_id}.pdf",
    )


@router.get("/sessions/{session_id}/report.md")
async def download_report_markdown(session_id: str):
    """Downloads the generated Markdown scorecard for a session."""
    reports_dir = Path(settings.archive_csv_path).parent / "reports"
    md_path = reports_dir / f"{session_id}.md"

    if not md_path.exists():
        sessions = get_active_sessions()
        if session_id in sessions:
            try:
                orch = get_orchestrator()
                dna = get_dna_builder().get_or_build(sessions[session_id].state.company, sessions[session_id].state.role)
                orch.report_agent.run(sessions[session_id], dna_profile=dna)
            except Exception as exc:
                logger.warning("Could not automatically compile report: %s", exc)

    if not md_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Markdown report for session '{session_id}' not found.",
        )

    return FileResponse(
        path=str(md_path),
        media_type="text/markdown",
        filename=f"InterviewDNA_Report_{session_id}.md",
    )


# -----------------------------------------------------------------------------
# 9. User Progress & History
# -----------------------------------------------------------------------------

@router.get("/users/{nickname}/progress", response_model=UserProgressResponse)
async def get_user_progress(nickname: str):
    """
    Retrieves all past interview sessions, overall scores, and verdicts
    for a user nickname to render progress and trend charts.
    """
    sqlite_store = get_sqlite_store()
    try:
        sessions = sqlite_store.get_user_sessions(user_nickname=nickname)
        return UserProgressResponse(
            nickname=nickname,
            total_sessions=len(sessions),
            sessions=sessions,
        )
    except Exception as exc:
        logger.error("Error retrieving progress for user %s: %s", nickname, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load user progress: {exc}",
        )


# -----------------------------------------------------------------------------
# 10. Archive Record Lookup (Citation Popover)
# -----------------------------------------------------------------------------

@router.get("/records/{record_id}")
async def get_archive_record(record_id: str):
    """
    Retrieves raw historical archive feedback record by ID for citation popovers.
    """
    record = get_archive_record_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Archive record '{record_id}' not found.",
        )
    return record
