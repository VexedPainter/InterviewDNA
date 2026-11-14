"""
scripts/generate_synthetic_archive.py
======================================
Generates a realistic 10-year (2016-2025) campus placement interview archive
as data/interview_archive.csv.

Design goals
------------
* At least 1,500 rows, each uniquely crafted via template expansion + seeded
  randomness -- no LLM dependency required (fully offline).
* Company-specific "DNA": question pool, difficulty distribution, rejection
  reasons, and round composition differ per company.
* No real student names are stored (anonymisation by design).
* Deterministic output for a given RANDOM_SEED so results are reproducible.

Run:
    python scripts/generate_synthetic_archive.py
"""

from __future__ import annotations

import csv
import logging
import random
import sys
from dataclasses import dataclass
from pathlib import Path

# Fix Windows console UTF-8 output encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

RANDOM_SEED = 42
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "interview_archive.csv"
TARGET_ROWS = 1_600

YEARS = list(range(2016, 2026))

FIELDNAMES = [
    "record_id",
    "year",
    "company",
    "role",
    "round_type",
    "topic",
    "difficulty",
    "question",
    "expected_points",
    "candidate_answer_summary",
    "feedback_text",
    "feedback_tags",
    "score_given",
    "outcome",
]


@dataclass
class CompanyDNA:
    """Encodes all statistical and content preferences for one company."""
    name: str
    roles: list[str]
    round_weights: dict[str, float]
    topic_weights: dict[str, float]
    difficulty_distribution: list[tuple[int, float]]
    selection_rate: float
    rejection_tags: list[str]
    positive_tags: list[str]
    target_rows: int


COMPANIES: list[CompanyDNA] = [
    CompanyDNA(
        name="TCS",
        roles=["Software Engineer", "Systems Engineer", "Business Analyst", "Data Analyst"],
        round_weights={"Aptitude": 0.25, "Technical": 0.35, "HR": 0.30, "Managerial": 0.10},
        topic_weights={
            "DSA": 0.10, "DBMS": 0.15, "OS": 0.12, "Networks": 0.08,
            "OOP": 0.15, "Aptitude": 0.20, "Behavioral": 0.15, "Projects": 0.05,
        },
        difficulty_distribution=[(1, 0.15), (2, 0.40), (3, 0.30), (4, 0.12), (5, 0.03)],
        selection_rate=0.70,
        rejection_tags=["weak aptitude score", "poor communication", "no project depth",
                        "unable to explain basics", "low energy"],
        positive_tags=["good communication", "confident", "knows fundamentals",
                       "positive attitude", "clear explanation"],
        target_rows=220,
    ),
    CompanyDNA(
        name="Infosys",
        roles=["Systems Engineer", "Technology Analyst", "Digital Specialist", "Process Executive"],
        round_weights={"Aptitude": 0.30, "Technical": 0.30, "HR": 0.30, "Managerial": 0.10},
        topic_weights={
            "DSA": 0.08, "DBMS": 0.14, "OS": 0.10, "Networks": 0.08,
            "OOP": 0.14, "Aptitude": 0.22, "Behavioral": 0.18, "Projects": 0.06,
        },
        difficulty_distribution=[(1, 0.10), (2, 0.38), (3, 0.33), (4, 0.14), (5, 0.05)],
        selection_rate=0.68,
        rejection_tags=["aptitude cutoff not met", "unclear communication", "weak logical reasoning",
                        "overconfident", "poor situational answers"],
        positive_tags=["structured answers", "good team player", "clear articulation",
                       "adaptable", "decent technical knowledge"],
        target_rows=200,
    ),
    CompanyDNA(
        name="Zoho",
        roles=["Software Developer", "Member Technical Staff", "UI Developer", "DevOps Engineer"],
        round_weights={"Technical": 0.65, "Aptitude": 0.20, "HR": 0.10, "Managerial": 0.05},
        topic_weights={
            "DSA": 0.35, "DBMS": 0.12, "OS": 0.10, "Networks": 0.05,
            "OOP": 0.18, "Aptitude": 0.10, "Behavioral": 0.05, "Projects": 0.05,
        },
        difficulty_distribution=[(1, 0.05), (2, 0.15), (3, 0.30), (4, 0.35), (5, 0.15)],
        selection_rate=0.35,
        rejection_tags=["no complexity analysis", "brute force only", "couldn't optimise",
                        "weak OOP design", "no edge case handling", "failed coding round"],
        positive_tags=["excellent problem solving", "wrote optimal solution", "clean code",
                       "explained time complexity", "handled edge cases"],
        target_rows=220,
    ),
    CompanyDNA(
        name="Amazon",
        roles=["SDE-I", "SDE-II", "Data Engineer", "Solutions Architect", "Business Analyst"],
        round_weights={"Technical": 0.50, "Managerial": 0.30, "HR": 0.10, "Aptitude": 0.10},
        topic_weights={
            "DSA": 0.28, "System Design": 0.15, "Behavioral": 0.25,
            "DBMS": 0.08, "OOP": 0.10, "OS": 0.06, "Projects": 0.08,
        },
        difficulty_distribution=[(1, 0.03), (2, 0.12), (3, 0.30), (4, 0.38), (5, 0.17)],
        selection_rate=0.28,
        rejection_tags=["weak leadership principle answer", "no STAR format",
                        "suboptimal DSA solution", "no ownership mindset",
                        "couldn't scale system design", "vague behavioral examples"],
        positive_tags=["strong LP alignment", "STAR format used well", "customer obsession evident",
                       "optimal algorithm", "clear system design", "data-driven thinking"],
        target_rows=200,
    ),
    CompanyDNA(
        name="Google",
        roles=["Software Engineer", "SWE-II", "Data Scientist", "Site Reliability Engineer"],
        round_weights={"Technical": 0.70, "Managerial": 0.20, "HR": 0.05, "Aptitude": 0.05},
        topic_weights={
            "DSA": 0.40, "System Design": 0.22, "OOP": 0.10,
            "OS": 0.08, "Behavioral": 0.12, "DBMS": 0.05, "Projects": 0.03,
        },
        difficulty_distribution=[(1, 0.02), (2, 0.08), (3, 0.20), (4, 0.42), (5, 0.28)],
        selection_rate=0.20,
        rejection_tags=["incorrect solution", "no edge case handling",
                        "poor code quality", "couldn't analyse complexity",
                        "system design not scalable", "didn't think about trade-offs"],
        positive_tags=["elegant solution", "correct complexity analysis", "clean code",
                       "great design intuition", "considered scalability", "excellent problem breakdown"],
        target_rows=160,
    ),
    CompanyDNA(
        name="Accenture",
        roles=["Associate Software Engineer", "Analyst", "Packaged App Developer", "Cloud Engineer"],
        round_weights={"Aptitude": 0.35, "Technical": 0.25, "HR": 0.30, "Managerial": 0.10},
        topic_weights={
            "Aptitude": 0.30, "Behavioral": 0.22, "DBMS": 0.10, "OOP": 0.10,
            "DSA": 0.08, "OS": 0.08, "Networks": 0.07, "Projects": 0.05,
        },
        difficulty_distribution=[(1, 0.18), (2, 0.42), (3, 0.28), (4, 0.10), (5, 0.02)],
        selection_rate=0.72,
        rejection_tags=["aptitude score below cutoff", "poor communication",
                        "not client-ready", "weak situational judgement", "low enthusiasm"],
        positive_tags=["good communication", "confident presenter", "client-facing demeanor",
                       "team oriented", "willing to learn"],
        target_rows=180,
    ),
    CompanyDNA(
        name="Deloitte",
        roles=["Analyst", "Consultant", "Technology Analyst", "Risk Advisory Analyst"],
        round_weights={"Aptitude": 0.30, "Technical": 0.20, "Managerial": 0.30, "HR": 0.20},
        topic_weights={
            "Aptitude": 0.25, "Behavioral": 0.28, "Domain": 0.15, "DBMS": 0.08,
            "OOP": 0.07, "DSA": 0.06, "Projects": 0.08, "Networks": 0.03,
        },
        difficulty_distribution=[(1, 0.12), (2, 0.35), (3, 0.32), (4, 0.16), (5, 0.05)],
        selection_rate=0.55,
        rejection_tags=["no business acumen", "weak case analysis",
                        "couldn't connect tech to business", "poor structured thinking",
                        "vague project contributions"],
        positive_tags=["strong analytical thinking", "business-aware", "structured communication",
                       "good problem decomposition", "leadership demonstrated"],
        target_rows=200,
    ),
    CompanyDNA(
        name="Flipkart",
        roles=["SDE-I", "SDE-II", "Data Engineer", "Product Analyst", "Platform Engineer"],
        round_weights={"Technical": 0.55, "Managerial": 0.25, "HR": 0.10, "Aptitude": 0.10},
        topic_weights={
            "DSA": 0.30, "System Design": 0.20, "DBMS": 0.10,
            "OOP": 0.12, "Behavioral": 0.12, "OS": 0.08, "Projects": 0.08,
        },
        difficulty_distribution=[(1, 0.03), (2, 0.14), (3, 0.28), (4, 0.37), (5, 0.18)],
        selection_rate=0.30,
        rejection_tags=["weak system design for scale", "suboptimal data structures",
                        "no product thinking", "couldn't debug under pressure",
                        "poor estimation skills"],
        positive_tags=["strong DSA", "good system design instincts", "product awareness",
                       "handles pressure well", "data-driven answers"],
        target_rows=220,
    ),
]

def make_record_id(company: str, year: int, index: int) -> str:
    return f"{company[:3].upper()}-{year}-{index:05d}"

# Question bank pools
DSA_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "What is the difference between an array and a linked list? When would you prefer one over the other?", "expected_points": ["random access O(1) for array|O(n) for linked list", "contiguous vs dynamic memory", "insertion/deletion cost", "cache locality of arrays", "linked list for frequent insertion at head"], "topic": "DSA"},
    {"difficulty_band": "low", "question": "Explain the concept of recursion with an example. What is a base case and why is it necessary?", "expected_points": ["function calling itself", "base case to terminate recursion", "stack frames explanation", "example: factorial or fibonacci", "risk of stack overflow without base case"], "topic": "DSA"},
    {"difficulty_band": "low", "question": "What is the time complexity of binary search? Explain how it works.", "expected_points": ["O(log n) time complexity", "requires sorted array", "divide search space in half each step", "low mid high pointer logic", "comparison to linear search O(n)"], "topic": "DSA"},
    {"difficulty_band": "low", "question": "Describe the difference between a stack and a queue. Give a real-world use case for each.", "expected_points": ["LIFO for stack vs FIFO for queue", "stack: function call stack/undo", "queue: print spooler/BFS", "push/pop for stack", "enqueue/dequeue for queue"], "topic": "DSA"},
    {"difficulty_band": "low", "question": "What is a hash table? How does it handle collisions?", "expected_points": ["key-value mapping", "hash function maps key to bucket", "collision: chaining vs open addressing", "average O(1) lookup", "worst case O(n) with many collisions"], "topic": "DSA"},
    {"difficulty_band": "mid", "question": "Given an unsorted array of integers, find all pairs that sum to a target value. What is the optimal time complexity?", "expected_points": ["brute force O(n^2)", "hash set approach O(n) time O(n) space", "iterate and check complement in set", "handle duplicates", "two-pointer for sorted variant O(n)"], "topic": "DSA"},
    {"difficulty_band": "mid", "question": "Explain Dijkstra's shortest path algorithm. What data structure makes it efficient?", "expected_points": ["greedy algorithm for weighted graph", "min-heap/priority queue gives O((V+E) log V)", "relaxation step", "doesn't work with negative edges", "comparison to BFS for unweighted"], "topic": "DSA"},
    {"difficulty_band": "mid", "question": "How does merge sort work? Prove that its time complexity is O(n log n).", "expected_points": ["divide and conquer", "split into halves recursively", "merge step O(n)", "log n levels of recursion", "T(n) = 2T(n/2) + O(n) recurrence"], "topic": "DSA"},
    {"difficulty_band": "mid", "question": "Explain how a binary search tree (BST) works. What is the worst-case complexity for search?", "expected_points": ["left child < parent < right child", "search O(h) where h is height", "balanced BST: O(log n)", "degenerate (sorted input): O(n)", "need AVL/Red-Black for guaranteed balance"], "topic": "DSA"},
    {"difficulty_band": "mid", "question": "What is dynamic programming? Solve the 0/1 knapsack problem using DP.", "expected_points": ["overlapping subproblems + optimal substructure", "memoization vs tabulation", "knapsack recurrence: dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt[i]]+val[i])", "O(n*W) time and space", "space optimisation to 1D array"], "topic": "DSA"},
    {"difficulty_band": "mid", "question": "Describe how BFS and DFS differ. When would you choose each for graph problems?", "expected_points": ["BFS uses queue level-by-level", "DFS uses stack/recursion depth-first", "BFS for shortest path in unweighted graph", "DFS for cycle detection/topological sort", "BFS O(V+E) with visited set"], "topic": "DSA"},
    {"difficulty_band": "high", "question": "Design an LRU (Least Recently Used) cache with O(1) get and put operations. Walk through your data structure choices.", "expected_points": ["doubly linked list + hashmap", "hashmap for O(1) lookup", "move accessed node to front", "evict tail on capacity overflow", "explain both get and put with examples"], "topic": "DSA"},
    {"difficulty_band": "high", "question": "Find the longest palindromic substring in a given string. Discuss at least two approaches and their complexities.", "expected_points": ["brute force O(n^3)", "expand around center O(n^2)", "Manacher's algorithm O(n)", "DP approach O(n^2) space", "edge cases: single char, all same chars"], "topic": "DSA"},
    {"difficulty_band": "high", "question": "Given a stream of integers, design a data structure that returns the median in O(log n) time for each insertion.", "expected_points": ["two heaps: max-heap for lower half, min-heap for upper half", "balance heaps to differ by at most 1", "median = top of heaps or average", "insertion O(log n)", "rebalancing strategy"], "topic": "DSA"},
    {"difficulty_band": "high", "question": "Solve the N-Queens problem. Explain your backtracking approach and how you prune the search space.", "expected_points": ["place queens row by row", "check column and diagonal conflicts", "backtrack when no valid placement", "pruning: use sets for attacked columns/diagonals", "O(n!) worst case but pruned effectively"], "topic": "DSA"},
    {"difficulty_band": "high", "question": "Explain segment trees. How would you use one to answer range sum queries with point updates efficiently?", "expected_points": ["tree where each node stores sum of a range", "build in O(n)", "query O(log n)", "update O(log n)", "lazy propagation for range updates"], "topic": "DSA"},
]

DBMS_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "What is the difference between a primary key and a foreign key? Give an example.", "expected_points": ["primary key: unique identifier for each row", "foreign key: references primary key of another table", "ensures referential integrity", "example: student_id in Student and Enrollment tables", "primary key cannot be NULL"], "topic": "DBMS"},
    {"difficulty_band": "low", "question": "Explain the concept of database normalization. What problem does it solve?", "expected_points": ["removes data redundancy", "1NF: atomic values, no repeating groups", "2NF: no partial dependency", "3NF: no transitive dependency", "prevents update/insert/delete anomalies"], "topic": "DBMS"},
    {"difficulty_band": "low", "question": "What is a SQL JOIN? Explain INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with examples.", "expected_points": ["INNER JOIN returns matching rows in both", "LEFT JOIN returns all from left and matching from right", "FULL OUTER JOIN returns all rows from both tables", "NULL for non-matching rows", "example with Employee and Department tables"], "topic": "DBMS"},
    {"difficulty_band": "mid", "question": "What are ACID properties in database transactions? Explain each property with an example.", "expected_points": ["Atomicity: all or nothing", "Consistency: DB moves from one valid state to another", "Isolation: concurrent transactions don't interfere", "Durability: committed data survives failures", "example: bank transfer illustrating all four"], "topic": "DBMS"},
    {"difficulty_band": "mid", "question": "Explain database indexing. What types of indexes exist and when would you use each?", "expected_points": ["index speeds up data retrieval", "B-tree index for range queries", "hash index for equality lookups", "composite index for multi-column queries", "trade-off: faster reads vs slower writes and storage"], "topic": "DBMS"},
    {"difficulty_band": "mid", "question": "What is the difference between clustered and non-clustered indexes?", "expected_points": ["clustered index determines physical storage order", "only one clustered index per table", "non-clustered index has separate structure with pointers", "clustered faster for range scans", "primary key is typically the clustered index"], "topic": "DBMS"},
    {"difficulty_band": "high", "question": "Design a database schema for a ride-sharing application like Ola/Uber. Discuss your normalisation choices.", "expected_points": ["entities: User Driver Ride Payment Vehicle", "relationships and cardinality", "normalization up to 3NF", "indexing on frequently queried columns", "consideration for scalability and partitioning"], "topic": "DBMS"},
    {"difficulty_band": "high", "question": "Explain the difference between optimistic and pessimistic concurrency control. When is each appropriate?", "expected_points": ["pessimistic: lock resources before accessing", "optimistic: proceed then validate at commit", "optimistic better for low-conflict scenarios", "pessimistic avoids wasted work in high-conflict", "MVCC as a form of optimistic control"], "topic": "DBMS"},
]

OS_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "What is the difference between a process and a thread? Why are threads called lightweight processes?", "expected_points": ["process has its own memory space", "threads share process memory", "thread creation cheaper than process creation", "context switch faster for threads", "threads communicate via shared memory"], "topic": "OS"},
    {"difficulty_band": "low", "question": "Explain what deadlock is. What are the four necessary conditions for a deadlock to occur?", "expected_points": ["mutual exclusion", "hold and wait", "no preemption", "circular wait", "example: two processes each holding one resource and waiting for the other"], "topic": "OS"},
    {"difficulty_band": "mid", "question": "Compare FCFS, SJF, and Round Robin CPU scheduling algorithms. What are their trade-offs?", "expected_points": ["FCFS: simple but convoy effect", "SJF: optimal average waiting time but starvation", "Round Robin: fair preemptive with time quantum", "context switch overhead for small quantum", "how to choose quantum size"], "topic": "OS"},
    {"difficulty_band": "mid", "question": "What is virtual memory? How does paging work?", "expected_points": ["illusion of large memory using disk", "page table maps virtual to physical pages", "page fault triggers disk access", "TLB caches recent translations", "thrashing when too many page faults"], "topic": "OS"},
    {"difficulty_band": "high", "question": "Explain the differences between mutex, semaphore, and monitor for process synchronisation.", "expected_points": ["mutex: binary lock owned by thread that acquires it", "semaphore: counting signal mechanism", "monitor: high-level synchronisation with condition variables", "mutex prevents priority inversion", "semaphore for producer-consumer"], "topic": "OS"},
]

NETWORKS_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "What happens when you type www.google.com in a browser and press Enter? Walk through the full process.", "expected_points": ["DNS resolution", "TCP three-way handshake", "TLS/HTTPS handshake", "HTTP request sent", "server responds with HTML", "browser renders page", "CDN and caching"], "topic": "Networks"},
    {"difficulty_band": "low", "question": "What is the difference between TCP and UDP? When would you use each?", "expected_points": ["TCP: reliable ordered connection-oriented", "UDP: unreliable connectionless faster", "TCP: file transfer email web", "UDP: video streaming gaming VoIP", "TCP overhead vs UDP speed trade-off"], "topic": "Networks"},
    {"difficulty_band": "mid", "question": "Explain the OSI model layers. Give an example protocol at each layer.", "expected_points": ["Physical Data-Link Network Transport Session Presentation Application", "examples: Ethernet IP TCP HTTP at respective layers", "encapsulation as data moves down", "decapsulation at receiver", "where firewalls and routers operate"], "topic": "Networks"},
    {"difficulty_band": "high", "question": "Design a load balancer. What algorithms would you support and how would you handle sticky sessions?", "expected_points": ["round robin weighted least connections", "health checks for backend servers", "sticky sessions via cookies or IP hash", "consistent hashing for distributed cache", "Layer 4 vs Layer 7 load balancing"], "topic": "Networks"},
]

OOP_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "Explain the four pillars of OOP: encapsulation, inheritance, polymorphism, and abstraction with examples.", "expected_points": ["encapsulation: data hiding via access modifiers", "inheritance: child class reuses parent code", "polymorphism: same interface different behaviour", "abstraction: hiding implementation details", "real-world example for each"], "topic": "OOP"},
    {"difficulty_band": "low", "question": "What is the difference between method overloading and method overriding?", "expected_points": ["overloading: same name different parameters compile-time", "overriding: child redefines parent method runtime", "overloading in same class", "overriding requires inheritance", "@Override annotation in Java"], "topic": "OOP"},
    {"difficulty_band": "mid", "question": "Explain SOLID principles. Give a code-level example of the Single Responsibility Principle.", "expected_points": ["Single Responsibility: one class one reason to change", "Open-Closed: open for extension closed for modification", "Liskov Substitution: subclass substitutable for parent", "Interface Segregation: no fat interfaces", "Dependency Inversion: depend on abstractions"], "topic": "OOP"},
    {"difficulty_band": "mid", "question": "What are design patterns? Explain the Singleton and Factory patterns with use cases.", "expected_points": ["Singleton: one instance per application", "thread-safe Singleton with double-checked locking", "Factory: creates objects without specifying exact class", "Factory decouples client from concrete classes", "real use: logging connection pool"], "topic": "OOP"},
    {"difficulty_band": "high", "question": "Design a parking lot system using OOP principles. Identify classes, relationships, and design patterns used.", "expected_points": ["classes: ParkingLot Floor Spot Vehicle Ticket", "inheritance: Vehicle -> Car Bike Truck", "Factory for vehicle/spot creation", "Strategy for pricing", "Observer for spot availability"], "topic": "OOP"},
]

APTITUDE_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "A train 150 m long passes a pole in 15 seconds. What is the speed of the train in km/h?", "expected_points": ["speed = distance/time", "speed = 150/15 = 10 m/s", "convert to km/h: 10 * 18/5 = 36 km/h", "correct unit conversion", "shows clear working"], "topic": "Aptitude"},
    {"difficulty_band": "low", "question": "If 6 men can complete a work in 10 days, how many days will 4 men take to complete the same work?", "expected_points": ["total work = 6 * 10 = 60 man-days", "days = 60 / 4 = 15 days", "inverse proportion concept", "shows working clearly", "correct answer: 15 days"], "topic": "Aptitude"},
    {"difficulty_band": "mid", "question": "In a class of 50 students, 30 passed in Mathematics, 25 passed in Science, and 10 passed in both. How many failed in both?", "expected_points": ["use inclusion-exclusion: 30+25-10=45 passed at least one", "50 - 45 = 5 failed both", "correct Venn diagram reasoning", "correct use of set union formula", "answer: 5"], "topic": "Aptitude"},
    {"difficulty_band": "mid", "question": "What is the probability of drawing two red cards consecutively from a standard deck without replacement?", "expected_points": ["26 red cards in 52 card deck", "first draw: 26/52 = 1/2", "second draw: 25/51", "combined: 26/52 * 25/51 = 25/102", "without replacement reduces denominator"], "topic": "Aptitude"},
    {"difficulty_band": "high", "question": "A mixture of milk and water in the ratio 3:1. If 8 litres of water is added, the ratio becomes 3:2. Find the initial quantity of the mixture.", "expected_points": ["let milk = 3x water = x", "after adding 8: 3x/(x+8) = 3/2", "cross multiply: 6x = 3x+24", "x = 8 so initial = 4x = 32 litres", "verify: 24 milk 8 water ratio 3:1 -> add 8 water -> 24:16 = 3:2"], "topic": "Aptitude"},
]

BEHAVIORAL_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "Tell me about yourself and why you are interested in this company.", "expected_points": ["structured intro: education skills projects", "genuine reason tied to company values", "links personal strengths to role", "concise under 2 minutes", "no reading from resume"], "topic": "Behavioral"},
    {"difficulty_band": "low", "question": "Describe a time you faced a conflict in a team. How did you resolve it?", "expected_points": ["STAR format used", "specific conflict described", "own role in resolution", "outcome and learning", "professional tone no blame"], "topic": "Behavioral"},
    {"difficulty_band": "mid", "question": "Tell me about a time you took ownership of a project that wasn't going well. What did you do?", "expected_points": ["clear situation with struggling project", "proactive ownership not assigned", "specific actions taken", "measurable positive outcome", "reflection on what was learned"], "topic": "Behavioral"},
    {"difficulty_band": "mid", "question": "Describe a situation where you had to learn a new technology under time pressure. How did you approach it?", "expected_points": ["specific technology and timeline", "structured learning approach", "resources used: docs tutorials peers", "applied knowledge to deliver", "speed vs depth trade-off discussed"], "topic": "Behavioral"},
    {"difficulty_band": "mid", "question": "Give an example of when you disagreed with your manager or mentor. How did you handle it?", "expected_points": ["respectful constructive disagreement", "data or reasoning used to make case", "listened to their perspective", "outcome: either changed mind or found compromise", "maintained professional relationship"], "topic": "Behavioral"},
    {"difficulty_band": "high", "question": "Describe the most ambitious project you have worked on. What was your contribution and what did you achieve?", "expected_points": ["genuine ambitious scope described", "personal contribution clearly separated from team", "quantifiable or concrete achievement", "challenges overcome", "impact beyond the immediate team"], "topic": "Behavioral"},
    {"difficulty_band": "high", "question": "Tell me about a time you had to make a difficult decision with incomplete information. What was your process?", "expected_points": ["acknowledges uncertainty explicitly", "describes information-gathering process", "reasoning framework used", "decision made and rationale", "outcome and reflection"], "topic": "Behavioral"},
]

SYSTEM_DESIGN_QUESTIONS: list[dict] = [
    {"difficulty_band": "mid", "question": "Design a URL shortening service (like bit.ly). What are the key components?", "expected_points": ["hashing for short URL generation", "database schema for URL mapping", "caching layer for hot URLs", "redirection logic", "scaling to millions of URLs"], "topic": "System Design"},
    {"difficulty_band": "mid", "question": "How would you design a notification system that sends emails, SMS, and push notifications at scale?", "expected_points": ["message queue for decoupling", "worker processes per channel", "retry logic with exponential backoff", "rate limiting per user", "monitoring and alerting"], "topic": "System Design"},
    {"difficulty_band": "high", "question": "Design Twitter's timeline feature. How do you handle the fan-out problem for users with millions of followers?", "expected_points": ["push vs pull model for timeline", "hybrid: push for normal users pull for celebrities", "Redis for timeline cache", "consistent hashing for sharding", "eventual consistency trade-off"], "topic": "System Design"},
    {"difficulty_band": "high", "question": "Design a distributed rate limiter that works across multiple servers. What algorithm would you use?", "expected_points": ["token bucket or sliding window algorithm", "Redis for shared state", "Lua scripts for atomic operations", "handling clock skew across servers", "graceful degradation"], "topic": "System Design"},
    {"difficulty_band": "high", "question": "Design a search engine index for a large e-commerce platform. How would you support fuzzy search and filters?", "expected_points": ["inverted index structure", "tokenisation and stemming", "distributed index sharding by category/brand", "faceted filtering with pre-aggregation", "Elasticsearch or similar internals"], "topic": "System Design"},
]

PROJECTS_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "Walk me through your final year project. What was the problem statement and your role?", "expected_points": ["clear problem statement", "own contribution separated from team", "tech stack mentioned with reasoning", "outcome or demo available", "challenges and solutions"], "topic": "Projects"},
    {"difficulty_band": "mid", "question": "What was the most technically challenging aspect of your best project? How did you overcome it?", "expected_points": ["genuine specific challenge", "research or debugging process described", "solution implemented and explained", "what they would do differently", "shows depth not surface level"], "topic": "Projects"},
    {"difficulty_band": "high", "question": "If you were to scale your final year project to serve 1 million users, what changes would you make to the architecture?", "expected_points": ["identifies current bottlenecks", "horizontal scaling strategy", "caching and CDN consideration", "database sharding or replication", "monitoring and observability"], "topic": "Projects"},
]

DOMAIN_QUESTIONS: list[dict] = [
    {"difficulty_band": "low", "question": "What is digital transformation? Give an example of a company that successfully underwent it.", "expected_points": ["technology-enabled business model change", "example: Netflix Dominos Amazon", "involves cultural and process change", "not just IT upgrade", "measurable business outcomes"], "topic": "Domain"},
    {"difficulty_band": "mid", "question": "What is cloud computing? Compare IaaS, PaaS, and SaaS with examples.", "expected_points": ["IaaS: raw compute storage networking (AWS EC2)", "PaaS: platform for app development (Heroku)", "SaaS: ready-to-use software (Gmail Salesforce)", "shared responsibility model", "cost flexibility vs control trade-off"], "topic": "Domain"},
    {"difficulty_band": "mid", "question": "Explain the concept of ERP systems. Why do large organisations use them?", "expected_points": ["integrated management of business processes", "single source of truth for data", "modules: finance HR supply chain", "reduces data silos and duplication", "examples: SAP Oracle"], "topic": "Domain"},
    {"difficulty_band": "high", "question": "A retail client wants to reduce inventory costs by 20%. What data-driven approach would you recommend?", "expected_points": ["demand forecasting using historical data", "ABC analysis of inventory", "safety stock optimisation", "supplier lead time reduction", "just-in-time vs safety buffer trade-off"], "topic": "Domain"},
]

ALL_QUESTIONS: dict[str, list[dict]] = {
    "DSA": DSA_QUESTIONS,
    "DBMS": DBMS_QUESTIONS,
    "OS": OS_QUESTIONS,
    "Networks": NETWORKS_QUESTIONS,
    "OOP": OOP_QUESTIONS,
    "Aptitude": APTITUDE_QUESTIONS,
    "Behavioral": BEHAVIORAL_QUESTIONS,
    "System Design": SYSTEM_DESIGN_QUESTIONS,
    "Projects": PROJECTS_QUESTIONS,
    "Domain": DOMAIN_QUESTIONS,
}

ANSWER_TIERS = {
    "poor": [
        "Candidate gave a vague answer with no technical specifics. Could not provide examples.",
        "Response was largely off-topic. Candidate confused basic concepts.",
        "Candidate admitted they were not sure and provided a rough guess.",
        "Very brief response that skipped all key points. No depth shown.",
        "Candidate attempted but made critical factual errors.",
        "Response showed surface-level preparation with no real understanding.",
    ],
    "average": [
        "Candidate covered the basics but lacked depth on optimisation and edge cases.",
        "Good conceptual understanding but struggled to apply to a concrete example.",
        "Answer was correct at a high level but missed two or three key expected points.",
        "Candidate explained the concept adequately but couldn't discuss trade-offs.",
        "Reasonable answer given in an unstructured manner; needed prompting to expand.",
        "Showed partial understanding; correct on the 'what' but weak on the 'why'.",
    ],
    "good": [
        "Candidate gave a well-structured answer covering most key points with a clear example.",
        "Strong conceptual grasp; addressed trade-offs and gave a relevant real-world analogy.",
        "Answer was accurate and detailed; minor gap on one sub-point but recovered with follow-up.",
        "Candidate explained the concept clearly, then applied it to their project experience.",
        "Good response with correct complexity analysis; communication was clear and confident.",
        "Demonstrated solid understanding; mentioned alternatives and their pros/cons.",
    ],
    "excellent": [
        "Outstanding answer covering all expected points, complexity analysis, and edge cases.",
        "Candidate not only answered correctly but proactively discussed optimisations and trade-offs.",
        "Exceptional depth and clarity; drew on personal project experience to ground the answer.",
        "Perfect STAR-format response with specific metrics and clear personal impact.",
        "Candidate's answer went beyond the expected; introduced a creative alternative approach.",
        "Flawless response: correct, concise, well-structured, with spontaneous counter-examples.",
    ],
}

FEEDBACK_TEMPLATES = {
    "poor": [
        "The candidate showed very little preparation. {gap}. For a {company} {role} role this is a critical gap.",
        "Disappointing response. {gap}. We expect candidates to at least demonstrate {baseline}.",
        "Could not answer even the fundamentals. {gap}. Would need significant upskilling before being considered.",
        "The answer was superficial and contained factual errors. {gap}. Not at the bar for {company}.",
    ],
    "average": [
        "Candidate knows the basics but needs to go deeper. {gap}. For {company}, we expect {baseline}.",
        "Adequate but not outstanding. {gap}. Showed potential but lacked rigour in the explanation.",
        "The response covered the surface but missed the key insight around {gap}. With more practice, could meet the bar.",
        "Decent conceptual understanding, but {gap}. We would want to see more structured thinking in the {company} context.",
    ],
    "good": [
        "Solid response overall. {strength}. Only minor gap: {gap}. Close to the bar for {company}.",
        "Good performance. {strength}. The candidate demonstrated readiness for a {company} {role} role.",
        "{strength}. Would have been excellent with a deeper dive into {gap}. Recommended for next round.",
        "Strong candidate. {strength}. Minor improvement needed on {gap} but the foundation is excellent.",
    ],
    "excellent": [
        "Exceptional answer. {strength}. This is exactly what we look for in a {company} {role}.",
        "{strength}. The candidate demonstrated outstanding mastery. Strongly recommended.",
        "Perfect response. {strength}. Showed both technical depth and clear communication -- rare combination.",
        "{strength}. Candidate went beyond the question and demonstrated real-world insight. Top performer.",
    ],
}

STRENGTHS = [
    "clearly articulated the concept with a good analogy",
    "provided correct complexity analysis without prompting",
    "structured the answer using STAR format effectively",
    "drew a direct link to their project experience",
    "handled follow-up questions with equal clarity",
    "identified edge cases proactively",
    "showed awareness of trade-offs between approaches",
    "communicated with confidence and precision",
    "demonstrated deep practical knowledge beyond textbook definitions",
    "broke down a complex problem into manageable steps",
]

GAPS = [
    "did not discuss time/space complexity",
    "missed the edge case of an empty input",
    "could not distinguish between similar approaches",
    "lacked a concrete example to support the explanation",
    "skipped the optimisation step",
    "did not apply the concept to a real-world scenario",
    "answer was theoretically correct but lacked depth",
    "communication was unclear and needed multiple rephrasing",
    "did not discuss failure modes or error handling",
    "showed no awareness of scalability concerns",
    "could not recall the exact formula or algorithm steps",
    "STAR format was absent; answer was unstructured",
]

BASELINES = {
    "TCS": "basic fundamentals and clear communication",
    "Infosys": "structured answers and logical reasoning",
    "Zoho": "optimal solutions with complexity analysis",
    "Amazon": "STAR-format behavioral answers and clean DSA solutions",
    "Google": "elegant algorithms with proven correctness",
    "Accenture": "clear communication and client-ready presentation",
    "Deloitte": "structured analytical thinking and business awareness",
    "Flipkart": "product-aware DSA and system design thinking",
}

def difficulty_to_band(d: int) -> str:
    if d <= 2:
        return "low"
    if d == 3:
        return "mid"
    return "high"

def sample_difficulty(dna: CompanyDNA, rng: random.Random) -> int:
    vals, weights = zip(*dna.difficulty_distribution)
    return rng.choices(vals, weights=weights, k=1)[0]

def quality_tier_from_score(score: float) -> str:
    if score < 4.0:
        return "poor"
    if score < 6.5:
        return "average"
    if score < 8.5:
        return "good"
    return "excellent"

def sample_score_and_outcome(dna: CompanyDNA, difficulty: int, rng: random.Random) -> tuple[float, str]:
    """
    Decide outcome first according to calibrated selection_rate, then sample score.
    This guarantees realistic positive and negative benchmarks for every company.
    """
    is_selected = rng.random() < dna.selection_rate
    outcome = "Selected" if is_selected else "Rejected"

    if is_selected:
        # Selected candidates score high (7.0 - 9.8)
        base = 7.5 + (0.5 if dna.selection_rate < 0.35 else 0.0)
        score = base + rng.gauss(0.8, 0.6) - (difficulty - 3) * 0.25
        score = max(6.8, min(10.0, score))
    else:
        # Rejected candidates score low to mediocre (1.0 - 6.5)
        base = 4.2 - (difficulty - 2) * 0.35
        score = base + rng.gauss(0.0, 1.3)
        score = max(0.5, min(6.4, score))

    return round(score, 1), outcome

def pick_question(topic: str, difficulty: int, rng: random.Random) -> dict:
    band = difficulty_to_band(difficulty)
    pool = ALL_QUESTIONS.get(topic, [])
    filtered = [q for q in pool if q["difficulty_band"] == band]
    if not filtered:
        filtered = pool if pool else [{"question": f"Explain the core concepts of {topic}.", "expected_points": ["accuracy", "depth", "examples", "clarity"], "topic": topic}]
    return rng.choice(filtered)

def generate_row(record_id: str, year: int, dna: CompanyDNA, rng: random.Random) -> dict:
    role = rng.choice(dna.roles)

    round_types = list(dna.round_weights.keys())
    round_weights = list(dna.round_weights.values())
    round_type = rng.choices(round_types, weights=round_weights, k=1)[0]

    topic_pool = list(dna.topic_weights.keys())
    topic_weights = list(dna.topic_weights.values())

    if round_type == "HR":
        topic = "Behavioral"
    elif round_type == "Aptitude":
        topic = rng.choices(["Aptitude", "DSA"], weights=[0.8, 0.2], k=1)[0]
    else:
        topic = rng.choices(topic_pool, weights=topic_weights, k=1)[0]

    difficulty = sample_difficulty(dna, rng)
    year_drift = (year - 2016) * 0.1
    if rng.random() < year_drift * 0.15:
        difficulty = min(5, difficulty + 1)

    q_data = pick_question(topic, difficulty, rng)
    question = q_data["question"]
    expected_pts = q_data["expected_points"]

    score, outcome = sample_score_and_outcome(dna, difficulty, rng)
    tier = quality_tier_from_score(score)

    answer_summary = rng.choice(ANSWER_TIERS[tier])
    strength = rng.choice(STRENGTHS)
    gap = rng.choice(GAPS)
    baseline = BASELINES.get(dna.name, "industry-standard competency")
    tmpl = rng.choice(FEEDBACK_TEMPLATES[tier])
    feedback = tmpl.format(
        company=dna.name,
        role=role,
        strength=f"Candidate {strength}",
        gap=gap,
        baseline=baseline,
    )

    if outcome == "Rejected":
        tags = rng.sample(dna.rejection_tags, k=min(2, len(dna.rejection_tags)))
        tags.append(gap.replace(" ", "_").replace("/", "_")[:30])
    else:
        tags = rng.sample(dna.positive_tags, k=min(2, len(dna.positive_tags)))
        if score >= 8.5:
            tags.append("top_performer")

    return {
        "record_id": record_id,
        "year": year,
        "company": dna.name,
        "role": role,
        "round_type": round_type,
        "topic": topic,
        "difficulty": difficulty,
        "question": question,
        "expected_points": "|".join(expected_pts),
        "candidate_answer_summary": answer_summary,
        "feedback_text": feedback,
        "feedback_tags": "|".join(tags),
        "score_given": score,
        "outcome": outcome,
    }

def generate_archive(output_path: Path, target_rows: int = TARGET_ROWS) -> None:
    rng = random.Random(RANDOM_SEED)
    rows: list[dict] = []
    global_index = 1

    for dna in COMPANIES:
        log.info("Generating rows for %s (target: %d)", dna.name, dna.target_rows)
        year_weights = [0.06, 0.07, 0.08, 0.09, 0.10, 0.10, 0.11, 0.12, 0.13, 0.14]
        year_counts = [0] * len(YEARS)
        remaining = dna.target_rows
        for i, w in enumerate(year_weights[:-1]):
            c = max(1, round(dna.target_rows * w))
            year_counts[i] = c
            remaining -= c
        year_counts[-1] = max(1, remaining)

        for year, count in zip(YEARS, year_counts):
            for _ in range(count):
                rid = make_record_id(dna.name, year, global_index)
                row = generate_row(rid, year, dna, rng)
                rows.append(row)
                global_index += 1

    rng.shuffle(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    log.info("Wrote %d rows to %s", len(rows), output_path)

if __name__ == "__main__":
    log.info("InterviewDNA -- Synthetic Archive Generator")
    log.info("Target: %d rows | Seed: %d", TARGET_ROWS, RANDOM_SEED)
    generate_archive(OUTPUT_PATH, TARGET_ROWS)
    log.info("Done. Run `python scripts/data_quality_report.py` to view the quality report.")
