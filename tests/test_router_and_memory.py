"""
tests/test_router_and_memory.py — Tests for Intent Router accuracy on 30+ labelled messages,
state-aware dispatching, and SQLite memory persistence & history condensation.
"""

from __future__ import annotations

from pathlib import Path

from src.memory.session_memory import SessionMemory, SQLiteSessionStore
from src.router.intent_router import IntentRouter
from src.schemas.models import EvaluationResult
from src.schemas.router import IntentType

# ==============================================================================
# 1. 30+ Labelled Test Dataset for Routing Accuracy
# ==============================================================================

ROUTING_DATASET = [
    # ── PRACTICE (8 examples) ─────────────────────────────────────────────────
    {"text": "I am ready to start the interview", "has_pending": False, "expected": IntentType.PRACTICE},
    {"text": "Let's begin the mock round", "has_pending": False, "expected": IntentType.PRACTICE},
    {"text": "Please ask me the first question", "has_pending": False, "expected": IntentType.PRACTICE},
    {"text": "Give me the next technical question", "has_pending": False, "expected": IntentType.PRACTICE},
    {"text": "I want to start practicing for Zoho", "has_pending": False, "expected": IntentType.PRACTICE},
    {"text": "Next question please", "has_pending": False, "expected": IntentType.PRACTICE},
    {"text": "Let's proceed with the interview", "has_pending": False, "expected": IntentType.PRACTICE},
    {"text": "Ask me another question", "has_pending": False, "expected": IntentType.PRACTICE},

    # ── EVALUATE (8 examples with active pending question) ─────────────────────
    {"text": "I would use a hash map to store elements with their indices for O(1) lookups.", "has_pending": True, "expected": IntentType.EVALUATE},
    {"text": "A process has its own virtual memory space while threads share the process memory.", "has_pending": True, "expected": IntentType.EVALUATE},
    {"text": "To implement LRU cache, we combine a doubly linked list with a hash map to achieve O(1) get and put.", "has_pending": True, "expected": IntentType.EVALUATE},
    {"text": "In TCP there is a 3-way handshake with SYN, SYN-ACK, and ACK before transmission begins.", "has_pending": True, "expected": IntentType.EVALUATE},
    {"text": "I used the STAR method: Situation was a production crash, Task was to recover, Action was rollback.", "has_pending": True, "expected": IntentType.EVALUATE},
    {"text": "Dijkstra algorithm uses a priority queue to greedily find the shortest path in O(E log V).", "has_pending": True, "expected": IntentType.EVALUATE},
    {"text": "Binary search works by dividing the search range in half each step giving O(log n) time.", "has_pending": True, "expected": IntentType.EVALUATE},
    {"text": "Deadlock requires four conditions: mutual exclusion, hold and wait, no preemption, and circular wait.", "has_pending": True, "expected": IntentType.EVALUATE},

    # ── COACH (8 examples) ────────────────────────────────────────────────────
    {"text": "How can I improve my interview performance?", "has_pending": False, "expected": IntentType.COACH},
    {"text": "Give me coaching tips for Amazon SDE interviews", "has_pending": False, "expected": IntentType.COACH},
    {"text": "What does Google look for in system design?", "has_pending": False, "expected": IntentType.COACH},
    {"text": "What are the common rejection reasons for Zoho candidates?", "has_pending": False, "expected": IntentType.COACH},
    {"text": "Can you give me feedback and tips on how to improve?", "has_pending": False, "expected": IntentType.COACH},
    {"text": "What does Amazon care about regarding leadership principles?", "has_pending": False, "expected": IntentType.COACH},
    {"text": "Show me company insights for Deloitte", "has_pending": False, "expected": IntentType.COACH},
    {"text": "Why do candidates fail Flipkart interviews?", "has_pending": False, "expected": IntentType.COACH},

    # ── REPORT (6 examples) ───────────────────────────────────────────────────
    {"text": "I want to end the interview now", "has_pending": True, "expected": IntentType.REPORT},
    {"text": "Please give me the session report and final scores", "has_pending": True, "expected": IntentType.REPORT},
    {"text": "Wrap up the interview and show my scorecard", "has_pending": False, "expected": IntentType.REPORT},
    {"text": "I am done with the session, summarize my results", "has_pending": True, "expected": IntentType.REPORT},
    {"text": "Finish interview and show summary", "has_pending": False, "expected": IntentType.REPORT},
    {"text": "Stop the interview session", "has_pending": True, "expected": IntentType.REPORT},

    # ── SMALLTALK_OR_UNCLEAR (5 examples) ─────────────────────────────────────
    {"text": "Hello there!", "has_pending": False, "expected": IntentType.SMALLTALK_OR_UNCLEAR},
    {"text": "Good morning, how are you?", "has_pending": False, "expected": IntentType.SMALLTALK_OR_UNCLEAR},
    {"text": "Who are you and what do you do?", "has_pending": False, "expected": IntentType.SMALLTALK_OR_UNCLEAR},
    {"text": "Hi", "has_pending": False, "expected": IntentType.SMALLTALK_OR_UNCLEAR},
    {"text": "What is InterviewDNA?", "has_pending": False, "expected": IntentType.SMALLTALK_OR_UNCLEAR},
]


def test_intent_router_accuracy_on_35_examples(capsys):
    """
    Evaluates classification accuracy across 35 labelled test cases
    and prints a detailed performance report.
    """
    router = IntentRouter()
    correct = 0
    total = len(ROUTING_DATASET)
    mismatches = []

    for item in ROUTING_DATASET:
        decision = router.classify_intent(
            message=item["text"],
            has_pending_question=item["has_pending"],
        )
        if decision.intent == item["expected"]:
            correct += 1
        else:
            mismatches.append({
                "text": item["text"],
                "has_pending": item["has_pending"],
                "expected": item["expected"].value,
                "got": decision.intent.value,
                "reasoning": decision.reasoning,
            })

    accuracy = (correct / total) * 100.0

    with capsys.disabled():
        print("\n==================================================")
        print("INTENT ROUTER ACCURACY REPORT")
        print(f"Total Test Messages: {total}")
        print(f"Correctly Classified: {correct}")
        print(f"Accuracy Rate: {accuracy:.1f}%")
        if mismatches:
            print("Mismatches:")
            for m in mismatches:
                print(f"  - '{m['text']}' (pending={m['has_pending']}) -> Expected: {m['expected']}, Got: {m['got']}")
        print("==================================================")

    # Require at least 95% routing accuracy
    assert accuracy >= 95.0, f"Router accuracy was {accuracy:.1f}%, expected >= 95.0%"


# ==============================================================================
# 2. State-Aware Routing Override Tests
# ==============================================================================

def test_override_takes_precedence_over_pending_question():
    """Verify explicit REPORT or COACH request is not swallowed by pending question state."""
    router = IntentRouter()

    # Even with a pending question, 'end interview' must route to REPORT
    dec_report = router.classify_intent("end interview", has_pending_question=True)
    assert dec_report.intent == IntentType.REPORT
    assert dec_report.fast_path_used is True

    # Even with a pending question, 'give me tips' must route to COACH
    dec_coach = router.classify_intent("give me coaching tips and feedback", has_pending_question=True)
    assert dec_coach.intent == IntentType.COACH


# ==============================================================================
# 3. SQLite Persistence & Session Memory Tests
# ==============================================================================

def test_sqlite_session_and_turn_storage(tmp_path: Path):
    """Test SQLite store persists session records, turn evaluations, and retrieves them."""
    test_db = str(tmp_path / "test_sessions.db")
    store = SQLiteSessionStore(db_path=test_db)

    memory = SessionMemory(
        session_id="sess_integration_01",
        company="Zoho",
        role="Software Developer",
        user_nickname="Kavitha",
        sqlite_store=store,
    )

    # Turn 1
    memory.start_new_turn(
        question="What is a hash table?",
        expected_points=["key-value", "hash function", "collision handling"],
        question_id="ZOH-2023-0001",
    )
    assert memory.has_pending_question is True

    memory.record_candidate_answer("It is a key value data structure using hashing.")
    assert memory.has_pending_question is False

    ev1 = EvaluationResult(correctness=8.0, depth=7.0, communication=8.0)
    memory.complete_active_turn(ev1)
    assert len(memory.state.history) == 1

    # Verify persisted in SQLite
    user_sessions = store.get_user_sessions("Kavitha")
    assert len(user_sessions) == 1
    assert user_sessions[0]["company"] == "Zoho"
    assert user_sessions[0]["user_nickname"] == "Kavitha"

    db_turns = store.get_session_turns("sess_integration_01")
    assert len(db_turns) == 1
    assert db_turns[0].question_id == "ZOH-2023-0001"
    assert db_turns[0].evaluation.correctness == 8.0


def test_session_history_condensation(tmp_path: Path):
    """Test that when turn count exceeds threshold, older turns are condensed to protect context."""
    test_db = str(tmp_path / "test_condense.db")
    store = SQLiteSessionStore(db_path=test_db)

    memory = SessionMemory(
        session_id="sess_condense_01",
        company="Amazon",
        role="SDE-I",
        condense_threshold=3,  # Condense when history > 3 turns
        sqlite_store=store,
    )

    for i in range(1, 6):
        memory.start_new_turn(
            question=f"Question number {i} on system design and algorithms.",
            expected_points=["scalability", "complexity"],
            question_id=f"AMZ-2024-{i:04d}",
        )
        memory.record_candidate_answer(f"Answer for turn {i} with concrete examples.")
        memory.complete_active_turn(
            EvaluationResult(
                correctness=7.0 + (i * 0.4),
                depth=7.0,
                communication=8.0,
                missed_points=["failure scenarios"] if i % 2 == 0 else [],
            )
        )

    # 5 turns completed with threshold 3 -> condensation should be populated
    assert len(memory.state.history) == 5
    assert memory.condensed_summary != ""
    assert "Turn 1" in memory.condensed_summary
    assert "Turn 2" in memory.condensed_summary
    assert "Turn 3" in memory.condensed_summary
    # Latest 2 turns (Turns 4 & 5) are kept intact
    assert "Turn 4" not in memory.condensed_summary
