# InterviewDNA REST API Specification

The InterviewDNA backend exposes a high-performance local REST API built with **FastAPI** and **uvicorn**. It cleanly wraps the underlying Agentic RAG architecture (Intent Router, Interviewer Agent, Evaluator Agent, Coach Agent, Report Agent, ChromaDB, and SQLite) without altering agent logic.

## Base Configuration

- **Base URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **CORS Allowed Origins:**
  - `http://localhost:5173` (Vite / React default development server)
  - `http://127.0.0.1:5173`
  - `http://localhost:3000`

---

## Error Handling Standard

All endpoints return a uniform error format for client-side handling:

```json
{
  "error": "Not Found",
  "detail": "Session 'a1b2c3d4' not found. Please create a session first."
}
```

HTTP Status Codes used:
- `200 OK`: Successful retrieval or action.
- `404 Not Found`: Missing session ID, invalid record ID, or missing report.
- `422 Unprocessable Content`: Schema validation error (e.g. empty message, out-of-range difficulty).
- `500 Internal Server Error`: Agent execution or database failure.

---

## Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and version info |
| `GET` | `/api/companies` | List of supported companies, available roles, and round structures |
| `GET` | `/api/companies/{company}/dna` | Company DNA statistical and behavioural profile |
| `POST` | `/api/sessions` | Initialize a new interview session and fetch question #1 |
| `POST` | `/api/sessions/{id}/message` | Send answer or query; returns routing, evaluation, and coaching |
| `GET` | `/api/sessions/{id}/stream` | Server-Sent Events (SSE) streaming real-time tokens & traces |
| `POST` | `/api/sessions/{id}/end` | Finalize session, generate 7-day plan, and compile reports |
| `GET` | `/api/sessions/{id}/report.pdf` | Download PDF session scorecard |
| `GET` | `/api/sessions/{id}/report.md` | Download Markdown session scorecard |
| `GET` | `/api/users/{nickname}/progress` | Retrieve past sessions and scores for trend analysis |
| `GET` | `/api/records/{record_id}` | Fetch raw archive feedback record for citation popovers |

---

## Detailed Endpoint Reference

### 1. Health Check
`GET /api/health`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "InterviewDNA API",
  "version": "1.0.0"
}
```

---

### 2. Supported Companies & Roles
`GET /api/companies`

**Response (200 OK):**
```json
{
  "companies": [
    "Zoho", "Amazon", "Google", "TCS",
    "Infosys", "Accenture", "Deloitte", "Flipkart"
  ],
  "roles": {
    "Zoho": ["Software Developer", "Member Technical Staff", "UI Developer", "DevOps Engineer"],
    "Amazon": ["SDE-I", "SDE-II", "Business Analyst", "Data Engineer", "Solutions Architect"]
  },
  "round_structures": {
    "Zoho": ["Aptitude", "Technical", "Technical", "Technical", "HR"]
  },
  "company_details": [
    {
      "company": "Zoho",
      "roles": ["Software Developer", "Member Technical Staff", "UI Developer", "DevOps Engineer"],
      "rounds": ["Aptitude", "Technical", "Technical", "Technical", "HR"]
    }
  ]
}
```

---

### 3. Company DNA Profile
`GET /api/companies/{company}/dna?role={optional_role}`

**Query Parameters:**
- `role` *(string, optional)*: Specific role name to filter DNA metrics.

**Response (200 OK):**
```json
{
  "company": "Zoho",
  "role": "Software Developer",
  "total_records": 200,
  "selection_rate": 28.5,
  "avg_difficulty": 3.42,
  "difficulty_trend_by_year": {
    "2021": 3.2,
    "2022": 3.4,
    "2023": 3.5,
    "2024": 3.6
  },
  "topic_distribution": {
    "Data Structures & Algorithms": 42.5,
    "Database Management Systems": 24.0,
    "Object-Oriented Programming": 18.5,
    "System Design": 15.0
  },
  "round_distribution": {
    "Technical": 60.0,
    "Aptitude": 25.0,
    "HR": 15.0
  },
  "top_rejection_tags": [
    {"tag": "Brute Force Only", "count": 28},
    {"tag": "Weak Complexity Analysis", "count": 22}
  ],
  "top_positive_tags": [
    {"tag": "Optimal Two-Pointer", "count": 35},
    {"tag": "Clear Edge Case Handling", "count": 26}
  ],
  "interviewer_style_summary": "Zoho technical rounds emphasize in-depth implementation from scratch without built-in library shortcuts.",
  "generated_at": "2026-11-14T11:16:00"
}
```

---

### 4. Create Interview Session
`POST /api/sessions`

**Request Body:**
```json
{
  "nickname": "Alex",
  "company": "Zoho",
  "role": "Software Developer",
  "round_mode": "Technical",
  "difficulty_mode": 3,
  "pressure_mode": false
}
```

**Response (200 OK):**
```json
{
  "session_id": "a93e82d1f4b0",
  "company": "Zoho",
  "role": "Software Developer",
  "round_type": "Technical",
  "difficulty_level": 3,
  "first_question": {
    "turn_number": 1,
    "question_id": "ZOH-2024-00102",
    "question": "Implement an in-place string compression algorithm without additional allocations.",
    "expected_points": [
      "Two-pointer read/write indices",
      "O(1) auxiliary space",
      "Edge handling for single character runs"
    ],
    "candidate_answer": "",
    "is_followup": false,
    "evaluation": null,
    "topic": "Data Structures & Algorithms",
    "round_type": "Technical"
  },
  "message": "Session a93e82d1f4b0 initialized. Question #1 ready."
}
```

---

### 5. Send Message / Answer Question
`POST /api/sessions/{session_id}/message`

**Request Body:**
```json
{
  "message": "We can maintain a write index and a read index. Traverse each character run, count length, and write the count if > 1 in O(1) memory."
}
```

**Response (200 OK):**
```json
{
  "routed_to": "Evaluator Agent",
  "confidence": 1.0,
  "reply_type": "EVALUATE",
  "response_text": "### 📊 Answer Evaluation (Overall: 8.6/10)\n\n- **Correctness**: 9.0/10\n- **Depth & Complexity**: 8.5/10\n- **Communication**: 8.0/10\n\n**✅ What you covered:**\n- Two-pointer read/write indices\n- O(1) auxiliary space",
  "question": {
    "turn_number": 2,
    "question": "Explain indexing strategies in PostgreSQL and how B-Trees handle range scans."
  },
  "evaluation": {
    "correctness": 9.0,
    "depth": 8.5,
    "communication": 8.0,
    "overall": 8.6,
    "matched_points": ["Two-pointer read/write indices", "O(1) auxiliary space"],
    "missed_points": [],
    "red_flags": [],
    "needs_followup": false,
    "followup_reason": null
  },
  "coaching": null,
  "followup": null,
  "agent_trace": {
    "retrieved_count": 5,
    "fallback_level": "company_role",
    "latency_ms": 342.15
  }
}
```

---

### 6. Real-Time Streaming via Server-Sent Events (SSE)
`GET /api/sessions/{session_id}/stream?message={encoded_message}`

Streams real-time event frames formatted as `text/event-stream`:

1. `event: start` -> Session handshake.
2. `event: status` -> Current processing step (`routing`, `retrieving`).
3. `event: routing` -> Intent routing decision `{ "routed_to": ..., "confidence": ... }`.
4. `event: trace` -> Retrieval metrics and latency `{ "retrieved_count": ..., "latency_ms": ... }`.
5. `event: token` -> Streamed response text chunks for live typewriter UI.
6. `event: complete` -> Full structured payload.
7. `data: [DONE]` -> Stream termination.

---

### 7. End Session
`POST /api/sessions/{session_id}/end`

**Response (200 OK):** Returns `SessionReport` containing:
- `verdict`: `"Selected Ready"` | `"Borderline"` | `"Needs Practice"`
- `averages`: Composite scores for Correctness, Depth, Communication, and Overall.
- `top_strengths`: Candidate's strongest topic areas.
- `top_gaps`: Weakest technical areas.
- `improvement_plan`: 7-day daily study roadmap.
- `benchmark_comparison`: Historical selected candidate averages at target company.

---

### 8. Download Scorecard Reports
- `GET /api/sessions/{session_id}/report.pdf`: Binary PDF file download (`application/pdf`).
- `GET /api/sessions/{session_id}/report.md`: Markdown file download (`text/markdown`).

---

### 9. User Progress & History
`GET /api/users/{nickname}/progress`

**Response (200 OK):**
```json
{
  "nickname": "Alex",
  "total_sessions": 3,
  "sessions": [
    {
      "session_id": "a93e82d1f4b0",
      "company": "Zoho",
      "role": "Software Developer",
      "round_type": "Technical",
      "difficulty_level": 3,
      "status": "COMPLETED",
      "created_at": "2026-11-14T11:45:00",
      "overall_score": 8.4,
      "final_verdict": "Selected Ready"
    }
  ]
}
```

---

### 10. Archive Record Citation Lookup
`GET /api/records/{record_id}`

Fetches the complete historical row from the 10-year placement archive for evidence hover cards and citation modals.

**Response (200 OK):**
```json
{
  "record_id": "AMA-2025-00832",
  "year": 2025,
  "company": "Amazon",
  "role": "SDE-I",
  "round_type": "Technical",
  "topic": "Data Structures & Algorithms",
  "difficulty": 4,
  "question": "Given a stream of integers, find the median in real-time.",
  "expected_points": ["Two heaps (min-heap and max-heap)", "Balancing property", "O(log N) insertion"],
  "candidate_answer_summary": "Candidate used two heaps to balance numbers and retrieved median in O(1).",
  "feedback_text": "Strong structural reasoning and immediate identification of heap balancing.",
  "feedback_tags": ["Optimal Two-Heap", "Clean Space Complexity"],
  "score_given": 9.2,
  "outcome": "Selected"
}
```
