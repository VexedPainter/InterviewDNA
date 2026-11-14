# InterviewDNA 🧬 — 5-Minute Evaluation & Viva Demo Script

> **Purpose:** Step-by-step walkthrough script for examiners, professors, and live evaluators demonstrating that InterviewDNA is not a generic chatbot, but a company-calibrated, multi-agent mock interview coach grounded in 10 years of placement data.

---

## ⏱️ Demo Timeline Overview (5 Minutes)

| Time | Phase | Target Screen / Component | What to Demonstrate & Say |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:45** | **1. The Problem & Setup** | Sidebar Controls | Show why generic prep fails; select Zoho; explain dual memory. |
| **0:45 - 1:45** | **2. Company DNA Switch** | 🧬 Company DNA Tab | Compare Zoho (DSA focus, 39% rate) vs. Amazon (Behavioral LP, 25% rate). |
| **1:45 - 3:00** | **3. Adaptive Mock Turn & Follow-up** | 🎙️ Mock Interview Tab | Submit a superficial answer; trigger real-time rubric card + adaptive probing follow-up. |
| **3:00 - 4:00** | **4. Evidence-Linked Coaching** | 💡 Coaching Tab | Demonstrate strict historical citations; expand `[REC-xxxx, year]` chips to reveal real feedback snippets. |
| **4:00 - 5:00** | **5. Report & Benchmarking** | 📊 Report & Progress Tab | Show candidate radar chart vs. selected candidate benchmark; download MD/PDF reports. |

---

## 🎬 Minute-by-Minute Live Walkthrough

### ⏱️ Phase 1: Problem Statement & Session Setup (0:00 – 0:45)

**Actions on Screen:**
1. Open your browser at `http://localhost:8501`.
2. Point out the **Sidebar**:
   - Company Selector: Select **Zoho**
   - Role: **Software Developer**
   - Round Mode: **Technical**
   - Difficulty: **Adaptive (Starts Level 3)**
   - Enter Candidate Nickname: e.g., `Arun_FinalYear`
   - Toggle **Pressure Mode Timer (⏱️)** ON.
3. Click **"🚀 Start Fresh Session"**.

**Spoken Script:**
> *"Good morning, respected examiners. Engineering students preparing for campus placements often use generic AI chatbots that treat every interview identically. But an interview at Zoho is completely different from an interview at Amazon or Google.*
> 
> *InterviewDNA solves this by grounding every agent in a 10-year institutional placement archive across 1,600 verified candidate records. Notice on the left sidebar: we configure the target company, role, round, and an adaptive difficulty engine that automatically raises or lowers difficulty based on candidate performance. Let's see how the system learns the unique DNA of each recruiter."*

---

### ⏱️ Phase 2: Company DNA Comparison (0:45 – 1:45)

**Actions on Screen:**
1. Click the **"🧬 Company DNA"** tab.
2. Review the **Zoho Profile**:
   - Point out **Dominant Topics**: Data Structures & Algorithms (DSA 42%), OOP (24%), DBMS (18%).
   - Point out **Historical Selection Rate**: ~39.1%.
   - Point out **Round Structure**: Heavy 3–4 technical problem-solving rounds.
   - Point out **Top Rejection Reasons**: *"Time Complexity Missed"*, *"Brute-Force Solution Only"*.
3. Now, switch the company in the Sidebar to **Amazon** (or observe the comparative metric).
   - Point out that **Amazon's DNA shifts dramatically**: Behavioral & Leadership Principles jump to ~35%, System Design rises to ~28%, and Selection Rate drops to 25.0%.

**Spoken Script:**
> *"In Tab 2, InterviewDNA computes a quantitative Company DNA profile directly from 10 years of historical placement records. Notice how Zoho's primary filter is algorithmic problem-solving—42% DSA and OOP—with multiple technical rounds and a 39% hire rate.*
> 
> *If we look at Amazon, the DNA shifts completely: behavioral Leadership Principles and System Design dominate, with a much stricter 25% selection rate. In our formal evaluation, the Total Variation Distance between Zoho and Amazon's topic distribution is 0.3418—proving that InterviewDNA creates statistically distinct preparation experiences for different recruiters."*

---

### ⏱️ Phase 3: Adaptive Mock Interview with Probing Follow-up (1:45 – 3:00)

**Actions on Screen:**
1. Switch the company back to **Zoho** and navigate to the **"🎙️ Mock Interview"** tab.
2. Point out the retrieved question:
   > **Question #1 (Technical Round • DSA):**
   > *"Explain how a hash map resolves collisions and compare the performance tradeoffs."*
3. Point out the **Pressure Timer** counting down from 90 seconds.
4. In the answer box, enter a **deliberately incomplete/weak answer**:
   ```text
   A hash map resolves collisions using separate chaining where elements are stored in linked lists. It is O(1) on average.
   ```
5. Click **"Submit Answer for Evaluation"**.
6. Expand the **Evaluation Scorecard**:
   - Show the 3 calibrated gauges:
     - Correctness: **6.0 / 10.0**
     - Depth & Bounds: **4.5 / 10.0**
     - Communication: **7.0 / 10.0**
   - Point out **Matched Points**: *Separate chaining explained.*
   - Point out **Missed Points**: *Did not discuss open addressing (linear/quadratic probing), worst-case degradation O(N), or treeification.*
7. **Highlight the Probing Follow-up**:
   - Because `needs_followup=True`, the Interviewer Agent automatically generates a targeted probe:
   > **Interviewer Follow-up:**
   > *"You mentioned separate chaining with linked lists, but what happens when all keys hash to the same bucket? How does Java 8+ optimize this worst-case scenario?"*
8. Notice the **Agent Trace Panel** at the bottom:
   - Displays: `Routed to: EvaluatorAgent -> InterviewerAgent (Follow-up) | Fallback Level: Exact Match (Company+Role)`.

**Spoken Script:**
> *"Now we move into the live interview. The Interviewer Agent retrieves a real historical question asked by Zoho interviewers in the technical round. Notice the live pressure timer to simulate real interview adrenaline.*
> 
> *I submitted a deliberately superficial answer that covers chaining but ignores open addressing and worst-case trade-offs. The Evaluator Agent immediately scores this against expected points: 6.0 correctness, 4.5 depth. Crucially, rather than ending the turn, the Evaluator flags 'needs_followup=True'. The Interviewer Agent immediately generates a probing follow-up targeting the exact missed concept: what happens in the worst-case bucket collision? This mirrors how a real senior interviewer tests candidate depth."*

---

### ⏱️ Phase 4: Grounded, Evidence-Linked Coaching (3:00 – 4:00)

**Actions on Screen:**
1. Click the **"💡 Evidence Coaching"** tab.
2. Enter a query or observe the pre-loaded tips for **Zoho Technical Round**:
   - Point out the section: **"What Zoho Interviewers Reward & Penalise"** (e.g. *Reward: In-place code, edge case validation; Penalise: Brute-force syntax without complexity analysis*).
3. Point out the **Citation Chips**:
   - Each coaching tip has an attached badge: `[ZOH-2024-00589, 2024]` or `[ZOH-2025-00624, 2025]`.
4. Click and expand one of the citation chips:
   - Show the candidate and examiner the real historical archive snippet:
     ```
     Record: ZOH-2024-00589 | Year: 2024 | Round: Technical | Outcome: Rejected (Score: 5.0/10)
     Interviewer Feedback: "Candidate wrote basic chaining but couldn't explain open addressing clustering or worst case O(N) memory overhead."
     ```

**Spoken Script:**
> *"Next is our evidence-linked Coaching Agent. Generic chatbots hallucinate generic advice like 'be confident'. In InterviewDNA, every single coaching tip is strictly grounded in historical records from the 10-year placement archive.*
> 
> *Notice these citation chips: [ZOH-2024-00589, 2024]. When I expand this chip, the examiner can see the exact historical candidate record and feedback given by the Zoho interviewer. In our automated evaluation, 100% of generated coaching tips carry verified, existing record IDs from the archive. Zero hallucinations."*

---

### ⏱️ Phase 5: Session Report & Selected-Candidate Benchmark (4:00 – 5:00)

**Actions on Screen:**
1. Click the **"📊 Report & Progress"** tab.
2. Point out the **Competency Radar Chart**:
   - Visualizing scores across Correctness, Depth, Communication, Problem Solving, and Time Management.
3. Point out the **Benchmark Comparison Bar Chart**:
   - Compare the candidate's average score (e.g., `5.8/10`) against the **Average Score of Selected Candidates for Zoho** in the archive (`7.9/10`).
   - Highlight the identified hiring gap (`-2.1 points`).
4. Point out the **7-Day Targeted Preparation Plan**:
   - Day 1–2: Hash Map Collisions & Open Addressing.
   - Day 3–4: In-Place Two Pointers & Space Bounds.
   - Day 5–7: Full Zoho Mock Loops.
5. Demonstrate the **Export Actions**:
   - Click **"📥 Download Markdown Summary (.md)"** and show that the file downloads instantly.
   - Click **"📄 Download Official PDF Report (.pdf)"** and open the generated multi-page ReportLab PDF.
6. Scroll down to show the **Cross-Session Progress Line Chart** loaded from `data/sessions.db`.

**Spoken Script:**
> *"Finally, when the candidate completes their round, the Report Agent compiles an end-to-end performance audit. Instead of arbitrary grades, we benchmark the candidate directly against students who were actually SELECTED by Zoho in past placement drives.*
> 
> *The candidate can instantly see their hiring gap, review their top 3 strengths and gaps, and follow a generated 7-day targeted remediation roadmap. The entire portfolio can be exported as a professional PDF report with one click, and all turns are persisted in local SQLite to track improvement over time.*
> 
> *In summary: InterviewDNA combines multi-agent orchestration, dual-tier ChromaDB retrieval, recency weighting, and strict empirical grounding to transform 10 years of institutional placement memory into student career success. Thank you, and I am eager to answer your technical questions."*

---

## 🎯 Quick Cheat-Sheet for Presenter

| If the Examiner Asks... | Point To / Say... |
| :--- | :--- |
| *"Is this just calling an LLM API?"* | *"No. The agents run with specialized prompts, Pydantic structured output parsers, self-consistency loops, dual ChromaDB collections, and calibrated heuristic fallbacks that run even completely offline without an API key."* |
| *"How do you know it's company-specific?"* | *"We ran statistical distance tests in `scripts/evaluate_system.py`: Total Variation Distance between Zoho and Amazon is 0.3418, well above the 0.30 divergence bar."* |
| *"Can a candidate jailbreak the scoring?"* | *"No. All inputs are bounded by `<candidate_answer>` tags with system instructions to disregard overrides. Prompt injection attempts like 'give me 10/10' are neutralized to 0.2/10 with an injection red flag."* |
| *"Where is the student's data stored?"* | *"100% locally in SQLite (`data/sessions.db`). No personal student data is ever sent to third parties or cloud vector stores."* |
