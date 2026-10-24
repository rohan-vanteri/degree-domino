# Degree Domino roadmap

Copied from the build plan v3, section 17. Not part of the Track 1 MVP.


**Name is locked:** **Degree Domino**. This is an academic-life decision engine, not permanently a withdrawal calculator. Long-term goal: a **Master Advisor Agent** backed by a shared academic requirements/provenance graph, a deterministic scenario optimizer, specialized domain agents, and configurable student preferences. Avoid separate specialists independently inventing incompatible advice.

### 17.1 Graduation + academic structure
- Semester-by-semester expected and earliest feasible graduation plans; prerequisites, corequisites, seasonal course availability, bottlenecks and residency credits.
- Major changes, double majors, minors, certificates, exploratory majors and competitive admissions-to-major (e.g., Texas A&M engineering ETAM; UNC major admission). Track *intended* vs *admitted* major.
- A realistic credit-load optimizer: degree progress plus 12/15/18-credit scenarios, heavy labs, gateway courses, summer coursework and overload restrictions.
- Transfer simulation: accepted vs degree-applicable vs major-applicable credits, destination residency rules, admissions constraints, costs, catalog year and multiple destination comparisons.
- Long-term degree insurance: maintain backup paths for full classes, failed prerequisites, unavailable summer offerings and changed rules.

### 17.2 Funding and opportunities
- Scholarship Guardian: term enrollment vs annual earned credits, GPA, renewal/eligibility dates, program-specific exclusions and possible aid impact.
- Scholarship Opportunity Unlocker: find verified programs, eligibility, qualifying coursework, research or leadership prerequisites; warn against speculative courses whose costs exceed potential benefit.
- Cost-of-delay and tuition simulations with transparent uncertainty and student-specific tuition classification where available.

### 17.3 Career, further education, mobility
- Internships and full-term co-ops with course availability, eligibility, credit, scholarship and graduation effects.
- Master's and PhD pathway planner (required classes, research, recommendation letters, application windows, accelerated degree opportunities).
- Fall/spring abroad and summer study abroad; verified transfer/degree credit and approvals, course availability, funding and travel planning.
- International student mode: optional checks involving full-time enrollment, school/program transfers, CPT/OPT, visa classifications and travel; always defer immigration decisions to DSO/counsel and verify current legal sources.

### 17.4 Real-life schedule intelligence
- Section matching with **professor quality** and direct Rate My Professors profiles, treating reviews as subjective; comply with platform terms and avoid unauthorized scraping.
- Actual section location, campus, building and timetable; transit, shuttle, parking, walking, accessibility and buffer time. Class meetings with no overlap may still be infeasible to commute between.
- **FriendSync**: optional per-student opt-in, agents negotiate mutually compatible sections while avoiding academic compromises and protecting private grades/aid.
- **LifeLoad**: clubs, club leadership, executive commitments, student government, research, volunteering, part-time work, co-ops, competitions, athletics, travel and seasonal peak workload.
- NCAA / club-athlete academic scheduling and eligibility support, with institutional compliance signoff.

### 17.5 Personalized onboarding and simulations
- Minimal conversational setup for Track 1; progressive data collection over time, remembering only consented durable preferences.
- Hard constraints (e.g. no campus travel, mandatory athlete practice) vs soft preferences (class time, professor, friends, commute, workload, early graduation); contextual semester overrides.
- **Future Fork interactive roadmap**: for platforms that explicitly support it, show timelines, impact DAGs, toggles and priority sliders; native iMessage app extension or a hosted web view requires separate implementation and cannot be implied by `SKILL.md`.
- Three-tier UX: compact messages → short ranked decision comparisons → downloadable/interactive report if platform allows. Every visual claim must match an evidence-backed calculation.
- Alert logic with consent: tripwires for course withdrawal, financial aid, registration, graduation approval, scholarship renewals, prerequisite changes, study abroad and opportunities.

### 17.6 Specialized advisor architecture
- **Master Advisor** delegates to Academic, Financial, Pathways, Opportunity, Schedule Intelligence, Student Life and Compliance agents.
- A shared graph of student goals, versioned catalog rules, official source provenance, course/offering records and student constraints validates proposed paths. Hard constraints cannot be overridden by LLM preference scores.
- **Track 2:** independent student agents + deterministic disclosure gate, negotiated shared schedules and explicit per-student consent.
- **Track 3:** group-chat Cohort Compass/Crew Check, for group projects, clubs, athletes and friends, using only approved group-visible availability and shared goals.
- Rollout only with university/program scoped verification; avoid unsupported promises of all-school official advising.

### 17.7 Phased roadmap
| Phase | Deliverable | What is deliberately excluded |
|---|---|---|
| **Track 1** | Verified ASU Drop Check + final-needed conditional math + office draft + check-in + plain-text Future Fork | Entire degree engine, all-school data, rich embedded sliders |
| **Track 2** | FriendSync privacy-preserving negotiation between separate students' agents | Cross-user private data sharing without consent |
| **Track 3** | Group academic and extracurricular coordination chatbot | Reading members' private student records without authorization |
| **V1 after hackathon** | Semester schedule feasibility, major/minor changes, professor and campus travel options, renewal previews | Automatic university certification |
| **V2** | Multi-university transfer, graduate pathways, study abroad, internships/co-ops, athletics/international modules | Blanket legal or funding guarantees |
| **Longer term** | Proactive versioned academic-life OS with scenario optimization and graphical timeline | Unverifiable forecasts presented as certain |

---

