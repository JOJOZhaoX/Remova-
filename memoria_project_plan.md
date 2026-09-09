# Memoria — Personal Multimodal Memory Agent

## 1. Project Overview

**Memoria** is a mobile-first personal memory agent that turns everyday photos, videos, text notes, and voice notes into structured life events.

The system is designed around the pipeline:

**Capture → Understand → Segment → Store → Retrieve → Reason**

The goal is not to build a conventional AI diary, but a **multimodal episodic memory system for personal agents**.

### Core value

Traditional diary apps require users to manually write, classify, and organize entries.

Memoria instead aims to:

- capture low-friction daily observations;
- automatically group related observations into events;
- generate structured event memories;
- build daily and long-term episodic memory;
- support natural-language recall over personal history;
- always link answers back to evidence.

Example:

```text
12:31 lunch table photo
12:37 food photo
12:44 short video
12:57 restaurant exterior photo

            ↓ Agent

12:30–13:00
Lunch with friends
4 media files
```

---

## 2. Product Positioning

### Not

> An AI-powered diary.

### Instead

> A multimodal episodic memory system for personal agents.

The technical questions are:

- What should be remembered?
- When should observations be merged?
- How should memories be represented?
- How should memories be retrieved?
- How should the agent reason over memories?
- How should generated memories be verified?

---

## 3. Core Product Goals

Memoria should provide three primary capabilities.

| Capability | Goal |
|---|---|
| Record | Let users record daily life with minimal effort |
| Remember | Convert fragmented observations into structured memories |
| Recall | Answer natural-language questions about personal history |

Example queries:

- What was I doing around 2 PM yesterday?
- How many ballet sessions did I record this month?
- When did I last go to Amsterdam?
- Which days was I at university last week?
- What did I spend most of my time on this week?

Every answer should support:

```text
Answer
  ↓
Event
  ↓
Original Evidence
```

---

## 4. MVP Scope

### V0.1 Required Features

- Photo capture/upload
- Video capture/upload
- Text note
- Automatic timestamp
- AI-generated event title
- AI-generated event description
- Daily timeline
- Basic event grouping
- Daily summary
- Semantic memory search
- Ask My Memory

### Out of Scope for MVP

Do not implement initially:

- face recognition;
- continuous GPS tracking;
- automatic full-camera-roll ingestion;
- Health data;
- social features;
- multi-user sharing;
- complex autonomous-agent workflows;
- proactive background monitoring.

---

## 5. Mobile App Structure

Use four primary tabs.

### 5.1 Today

Purpose:

- show today's timeline;
- create new observations;
- display grouped events;
- review AI-generated event summaries.

Example:

```text
Wednesday
9 September

────────────────────────

09:18

[ Photo ]

Thesis work
LIACS

────────────────────────

12:32 — 13:06

[ Photo ] [ Photo ] [ Video ]

Lunch with friends

────────────────────────

14:20

[ Photo ]

Working on Memory Agent

────────────────────────

17:35 — 18:50

[ Video ]

Ballet class
```

The key design principle:

> One timeline entry represents an **event**, not one media file.

---

### 5.2 Memory

Purpose:

- browse historical memories;
- view by calendar;
- search events;
- later support categories such as activities, places, and topics.

Possible UI:

```text
Memory

[ Calendar ]

September
M T W T F S S
...

────────────

Activities
Places
Topics
```

Later examples:

```text
Activities

Thesis        42 events
Ballet        18 events
TA            13 events
Travel        11 events
Dining        37 events
```

---

### 5.3 Ask

Chat-style interface for querying personal memory.

Example:

```text
User:
How many ballet sessions did I have in August?

Agent:
I found 7 ballet-related events in August.

5 were classes.
2 were individual practice sessions.

[View evidence]
```

Design rule:

> Answer → Evidence → Original Memory

The model should never answer solely from generated text when supporting events are available.

---

### 5.4 Me

Settings and data controls.

Initial features:

- account;
- model configuration;
- data export;
- storage management;
- privacy settings;
- delete local/cloud data.

---

## 6. Capture UX

Recording must be extremely fast.

A floating action button can provide:

```text
+
├── Photo
├── Video
├── Voice
└── Note
```

For an image observation, automatically capture:

```text
timestamp
media file
optional location
```

Then asynchronously generate:

```text
12:43
Lunch at a restaurant
```

The user should normally only need to review or correct the result.

---

## 7. Memory Model

Use a hierarchical representation.

```text
Observation
    ↓
Event
    ↓
Daily Memory
    ↓
Long-term Memory
```

---

## 8. Observation Model

An observation is the raw unit of captured information.

Example:

```json
{
  "id": "obs_001",
  "timestamp": "2026-09-09T12:31:00",
  "type": "image",
  "media_path": "...",
  "text": null,
  "metadata": {}
}
```

Possible observation types:

- image;
- video;
- text;
- voice;
- calendar;
- location.

Only image, video, and text are required for the MVP.

---

## 9. Event Model

An event is a semantic grouping of one or more observations.

Example:

```json
{
  "id": "evt_001",
  "start_time": "2026-09-09T12:30:00",
  "end_time": "2026-09-09T13:05:00",
  "title": "Lunch with friends",
  "summary": "Had lunch at a restaurant.",
  "observation_ids": [
    "obs_001",
    "obs_002",
    "obs_003"
  ],
  "tags": [
    "food",
    "social"
  ],
  "confidence": 0.87
}
```

Event is the primary retrieval unit for the agent.

---

## 10. Daily Memory Model

A daily memory summarizes the event sequence for one day.

Example:

```json
{
  "date": "2026-09-09",
  "summary": "Spent most of the day working at university, followed by ballet practice.",
  "event_ids": [
    "evt_001",
    "evt_002",
    "evt_003"
  ]
}
```

---

## 11. System Architecture

```text
                    Mobile App
                        │
          ┌─────────────┼─────────────┐
          │             │             │
       Photo          Video          Text
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                Observation Layer
                        ↓
               Multimodal Analysis
                        ↓
                Event Segmentation
                        ↓
                 Event Generation
                        ↓
                 Memory Manager
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
      PostgreSQL     pgvector      Media Store
          │
          ↓
       Retrieval
          ↓
     Memory Agent
          ↓
     User Question
```

---

## 12. Agent Modules

Keep the initial architecture modular rather than building one monolithic autonomous agent.

### 12.1 Observer

Responsibilities:

- analyze images;
- analyze text;
- extract concise semantic descriptions;
- extract possible activity/category information;
- produce embeddings.

Output example:

```json
{
  "activity": "working",
  "scene": "office",
  "objects": ["laptop", "monitor"],
  "summary": "Working on a laptop in an office environment.",
  "confidence": 0.82
}
```

---

### 12.2 Segmenter

Responsibilities:

- decide whether a new observation belongs to an existing event;
- determine event boundaries;
- create a new event when necessary.

Signals:

- temporal distance;
- semantic similarity;
- visual similarity;
- location similarity.

Possible baseline score:

```text
event_score =
    α × temporal_similarity
  + β × semantic_similarity
  + γ × visual_similarity
  + δ × location_similarity
```

If score is above a threshold:

```text
merge
```

Otherwise:

```text
create new event
```

The first version should use a deterministic heuristic or lightweight scoring function.

No model training is required.

---

### 12.3 Memory Manager

Responsibilities:

- create events;
- merge observations;
- update event start/end time;
- regenerate event title/summary when new evidence arrives;
- create daily summaries;
- maintain embeddings;
- preserve links to raw observations.

---

### 12.4 Retriever

Responsibilities:

- parse user questions;
- detect temporal constraints;
- filter events by metadata;
- retrieve semantically similar events;
- rerank evidence;
- pass relevant evidence to the LLM.

---

## 13. Retrieval Pipeline

Example query:

> Which days was I at university last week?

Pipeline:

```text
Question
   ↓
Intent Parsing
   ↓
Temporal Parsing
   ↓
Metadata Filter
   ↓
Vector Retrieval
   ↓
Reranking
   ↓
Relevant Events
   ↓
LLM Reasoning
   ↓
Answer + Evidence
```

Recommended retrieval strategy:

1. parse dates first;
2. apply hard time filters;
3. use vector similarity within that range;
4. optionally rerank;
5. answer only from retrieved events.

---

## 14. Hallucination Control

This system contains personal memory, so unsupported inference should be avoided.

Use three concepts:

```text
AI Generated Content
        ↓
Confidence
        ↓
Evidence
```

Bad:

```text
Meeting with thesis supervisor.
```

when the only evidence is a laptop photo.

Better:

```text
Working at university.
Confidence: 62%
```

If ambiguous:

```text
What were you doing?

[ Thesis ]
[ TA ]
[ Other ]
```

User corrections should overwrite or annotate the generated memory.

---

## 15. Recommended Tech Stack

### Mobile

```text
React Native
Expo
TypeScript
```

### Backend

```text
Python
FastAPI
```

### Database

```text
PostgreSQL
pgvector
```

### Media Storage

For development:

```text
local filesystem
```

For hosted version:

```text
S3-compatible object storage
```

Possible providers:

- Supabase Storage;
- Cloudflare R2;
- AWS S3.

### AI

Possible options:

```text
Multimodal LLM:
GPT / Gemini / Qwen-VL

Embeddings:
OpenAI embeddings / BGE / Qwen embeddings

Speech:
Whisper
```

### Authentication

Optional for local prototype.

Later:

```text
Supabase Auth
```

---

## 16. Suggested MVP Stack

For speed of development:

```text
React Native + Expo
        ↓
FastAPI
        ↓
PostgreSQL + pgvector
        ↓
Supabase Storage
        ↓
LLM API
```

---

## 17. Database Schema

Initial tables:

```text
users
observations
events
event_observations
daily_memories
embeddings
conversations
messages
```

Core relationships:

```text
User
 │
 ├── Observation
 │
 ├── Event
 │     └── Observation[]
 │
 ├── DailyMemory
 │
 └── Conversation
```

---

## 18. Initial SQL Concept

### observations

```sql
CREATE TABLE observations (
    id UUID PRIMARY KEY,
    user_id UUID,
    created_at TIMESTAMPTZ NOT NULL,
    type TEXT NOT NULL,
    media_url TEXT,
    text_content TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### events

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    user_id UUID,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    title TEXT,
    summary TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### event_observations

```sql
CREATE TABLE event_observations (
    event_id UUID REFERENCES events(id),
    observation_id UUID REFERENCES observations(id),
    PRIMARY KEY (event_id, observation_id)
);
```

### daily_memories

```sql
CREATE TABLE daily_memories (
    id UUID PRIMARY KEY,
    user_id UUID,
    date DATE NOT NULL,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 19. Initial API Design

### Observation APIs

```text
POST   /observations
GET    /observations/{id}
GET    /observations?date=YYYY-MM-DD
DELETE /observations/{id}
```

### Event APIs

```text
GET    /events
GET    /events/{id}
PATCH  /events/{id}
DELETE /events/{id}
POST   /events/resegment
```

### Daily Memory APIs

```text
GET    /daily-memory/{date}
POST   /daily-memory/{date}/regenerate
```

### Agent APIs

```text
POST   /agent/ask
POST   /agent/analyze-observation
POST   /agent/segment
```

---

## 20. Version Plan

### V0.1 — Diary

Goal:

> A usable daily logging app.

Implement:

- photo upload;
- video upload;
- text note;
- timestamp;
- timeline;
- AI-generated title;
- AI-generated description.

---

### V0.5 — Memory

Goal:

> The application begins to maintain episodic memory.

Implement:

- event segmentation;
- event merging;
- embeddings;
- semantic search;
- daily summary;
- evidence links.

---

### V1.0 — Memory Agent

Goal:

> Users can reason over their personal history.

Implement:

- Ask My Memory;
- temporal query parsing;
- filtered retrieval;
- vector retrieval;
- evidence-based answers;
- event correction;
- memory update workflow.

---

### V2.0 — Personal Intelligence

Possible future features:

- Calendar integration;
- location;
- Health integration;
- activity statistics;
- habit detection;
- weekly review;
- monthly review;
- people memory;
- place memory;
- pattern discovery;
- proactive reminders.

Examples:

```text
You recorded ballet once per week during the last three weeks,
compared with twice per week previously.
```

```text
Most of your thesis work this week happened in the afternoon.
```

---

## 21. Eight-Week Development Plan

| Week | Goal | Deliverable |
|---|---|---|
| 1 | Product design and architecture | Wireframes, schema, repository |
| 2 | Mobile shell | Today page and navigation |
| 3 | Capture | Photo/video/text upload |
| 4 | AI understanding | Caption/title generation |
| 5 | Event segmentation | Automatic event grouping |
| 6 | Memory retrieval | Embeddings and search |
| 7 | Ask My Memory | RAG-based QA |
| 8 | Polish and evaluation | Demo, README, tests, results |

---

## 22. Week 1 Tasks

### Repository

Recommended structure:

```text
memoria/
├── mobile/
├── backend/
├── docs/
├── scripts/
├── tests/
├── .env.example
├── docker-compose.yml
└── README.md
```

### Mobile

Initialize:

```text
Expo
TypeScript
React Navigation / Expo Router
```

Create four screens:

```text
Today
Memory
Ask
Me
```

### Backend

Initialize:

```text
FastAPI
SQLAlchemy
Pydantic
Alembic
```

Create:

```text
GET /health
POST /observations
GET /events
```

### Database

Create:

```text
observations
events
event_observations
daily_memories
```

### Deliverable

By the end of Week 1:

```text
App opens
↓
User can navigate
↓
Backend runs
↓
Database connects
↓
Mobile can call backend health endpoint
```

---

## 23. Week 2–3 Tasks

Implement capture pipeline.

```text
User captures photo
        ↓
Mobile creates observation
        ↓
Upload media
        ↓
POST /observations
        ↓
Store metadata
        ↓
Display on Today timeline
```

Acceptance criteria:

- photo can be uploaded;
- video can be uploaded;
- text note can be saved;
- timestamp is automatically recorded;
- observations survive app restart;
- Today page displays records chronologically.

---

## 24. Week 4 Tasks

Add multimodal analysis.

For each new observation:

```text
Observation
    ↓
LLM / Vision Model
    ↓
Structured Metadata
```

Expected schema:

```json
{
  "summary": "...",
  "activity": "...",
  "scene": "...",
  "tags": [],
  "confidence": 0.0
}
```

Acceptance criteria:

- image observations get a generated summary;
- title generation is asynchronous;
- failures do not block saving;
- original media is always preserved.

---

## 25. Week 5 Tasks

Implement event segmentation.

Baseline algorithm:

```python
if time_gap < threshold and semantic_similarity > threshold:
    merge_into_previous_event()
else:
    create_new_event()
```

Start simple.

Do not build a complex learned segmentation model yet.

Acceptance criteria:

- multiple related observations can become one event;
- unrelated observations create separate events;
- event start/end times update correctly;
- user can manually split or merge events later.

---

## 26. Week 6 Tasks

Implement retrieval.

Pipeline:

```text
Event
 ↓
Embedding
 ↓
pgvector
 ↓
Semantic Search
```

Acceptance criteria:

- text queries return top-k events;
- date filtering works;
- results link back to media;
- retrieval endpoint exposes similarity score.

---

## 27. Week 7 Tasks

Implement Ask My Memory.

Request:

```json
{
  "query": "What was I doing yesterday afternoon?"
}
```

Response:

```json
{
  "answer": "...",
  "evidence": [
    {
      "event_id": "...",
      "title": "...",
      "start_time": "...",
      "media": []
    }
  ]
}
```

The answer generation model must receive only retrieved evidence.

---

## 28. Week 8 Tasks

Polish:

- loading states;
- error handling;
- media preview;
- event detail page;
- editing;
- confidence display;
- screenshots;
- demo video;
- evaluation;
- documentation.

---

## 29. Evaluation Plan

A strong portfolio project should include system evaluation rather than only UI screenshots.

### 29.1 Event Segmentation

Create manually labeled sequences.

Measure:

```text
Precision
Recall
F1
```

Compare predicted event boundaries with manual event boundaries.

---

### 29.2 Retrieval

Create a small benchmark of personal-memory questions.

Examples:

```text
When did I last go to Amsterdam?
How many ballet sessions did I record last month?
What was I doing around 3 PM yesterday?
Which days was I at university last week?
```

Metrics:

```text
Recall@K
MRR
Answer Accuracy
```

---

### 29.3 Memory Representation Ablation

Compare:

```text
A. Raw observation retrieval
B. Event-based retrieval
C. Hierarchical memory retrieval
```

Evaluate whether event-level memory improves:

- retrieval precision;
- answer accuracy;
- latency;
- context efficiency.

This is one of the strongest technical components of the project.

---

## 30. Privacy Principles

This product handles highly sensitive personal data.

Design principles:

- preserve original source data;
- minimize cloud upload where possible;
- never perform hidden background recording;
- use explicit user permissions;
- support complete data export;
- support deletion;
- separate generated inference from user-authored content;
- show evidence for AI-generated claims.

Possible later option:

```text
Local-first mode
```

with local storage and optional local models.

---

## 31. Portfolio Deliverables

The GitHub repository should eventually include:

```text
README.md
docs/architecture.md
docs/memory-design.md
docs/evaluation.md
docs/api.md
screenshots/
demo/
tests/
```

Recommended README headline:

> **Memoria**
>
> A multimodal personal episodic memory agent that turns everyday photos,
> videos and notes into structured experiences and lets users search and
> reason over their personal history.

Tagline:

```text
Capture → Remember → Recall
```

---

## 32. Engineering Principles

1. **Event is the primary memory unit.**
2. **Raw observations are never discarded.**
3. **LLM output is treated as inference, not truth.**
4. **All answers should be traceable to evidence.**
5. **Time filtering should happen before semantic retrieval when possible.**
6. **Start with deterministic workflows before autonomous-agent complexity.**
7. **Do not optimize for many features before the memory pipeline works.**
8. **Evaluation should be designed alongside implementation.**

---

## 33. Immediate Development Order

Implement in this exact sequence:

```text
1. Repository setup
2. Mobile navigation
3. FastAPI backend
4. PostgreSQL schema
5. Observation creation
6. Photo/text capture
7. Today timeline
8. AI observation analysis
9. Event model
10. Event segmentation
11. Embeddings
12. Memory search
13. Ask My Memory
14. Daily summary
15. Evaluation
16. UI polish
```

---

## 34. Codex Starting Task

A good first implementation task for Codex:

```text
Create the initial monorepo for Memoria.

Requirements:

1. mobile/
   - React Native with Expo
   - TypeScript
   - Expo Router
   - Four tabs:
     - Today
     - Memory
     - Ask
     - Me

2. backend/
   - Python FastAPI
   - SQLAlchemy
   - Pydantic
   - Alembic
   - PostgreSQL
   - GET /health endpoint

3. Root:
   - docker-compose.yml for PostgreSQL
   - .env.example
   - README.md
   - Makefile or equivalent developer commands

4. Database models:
   - Observation
   - Event
   - EventObservation
   - DailyMemory

5. Add basic tests for:
   - backend health endpoint
   - database model creation

Do not implement AI functionality yet.

Prioritize clean project structure, typed interfaces, and a development setup
that can run locally with minimal configuration.
```

---

## 35. Definition of Success

The first meaningful milestone is not an autonomous agent.

It is this end-to-end workflow:

```text
Take a photo
      ↓
Observation stored
      ↓
AI understands observation
      ↓
Observation grouped into event
      ↓
Event appears on timeline
      ↓
Event becomes retrievable
      ↓
User asks a question
      ↓
System answers with evidence
```

Once this pipeline works reliably, more advanced memory-agent behavior can be added.
