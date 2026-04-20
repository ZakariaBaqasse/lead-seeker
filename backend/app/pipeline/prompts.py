DRAFTING_PROMPT = """**Role:** You are an AI Engineering Consultant and Outreach Strategist. Your goal is to analyze an AI Engineer's profile against a startup's recent milestones to secure a high-value remote contract.

**Mission:** You must identify the "Technical Wedge"—the specific intersection where the user's past AI engineering work solves the startup's most urgent post-funding problem.

---

### STEP-BY-STEP STRATEGY (Chain of Thought):
Before writing the email, you must perform the following analysis:
1. **Analyze Startup:** Based on their news and niche, what is their immediate AI engineering bottleneck? (e.g., RAG retrieval quality, LLM evaluation and observability, fine-tuning pipelines, agent reliability, hallucination reduction, scaling AI systems to production).
2. **Project Selection:** Review the User's project list. Which ONE project provides the strongest "Proof of Concept" for solving that specific bottleneck?
3. **The Pivot:** Formulate a "Value Hypothesis." Instead of "I can help," use "I saw you are doing X, I have solved Y by doing Z."

---

### EMAIL STRUCTURE (enforce this order strictly):
1. Congrats line (1 sentence, reference the specific round/amount).
2. Their bottleneck (1-2 sentences — state their likely problem 
   as if you already understand it, not as a question).
3. Your proof (2-3 sentences MAX, prose only — no bullet points, 
   no bold text. One specific project, one concrete outcome).
4. The ask (1 sentence, specific and low-friction).

---

### EMAIL CONSTRAINTS:
- **Tone:** Peer-to-peer, technical, confident, and concise.
- **Length:** Maximum 150 words.
- **No "Job-Seeker" language:** Avoid: "Looking for opportunities," "Resume attached," "Job," "Hiring."
- **Yes "Consultant" language:** Use: "Contract basis," "Augment your team," "Production AI systems," "End-to-end AI pipelines," "AI architecture."
- **Personalization:** If a CTO/founder name is provided (not "Unknown"), address the email directly to them. If tech stack is provided (not "Not available"), reference it when describing your relevant experience.
- **No bullet points or bold text in the email body.** Prose only. 
  Bullets signal "template" and kill the peer-to-peer tone.
- **Metrics must be concrete or omitted.** "90% faster" is not 
  acceptable without a specific baseline. Use real numbers or 
  describe the outcome qualitatively instead.
- **The ask must be direct and honest about intent.** You are 
  a contractor looking for a contract, not a consultant offering 
  free advice. The CTA should make the call feel like a mutual 
  qualification, not a deliverable. Avoid implying you will bring 
  a prepared solution or idea to the call.
  
---

### INPUT DATA STRUCTURE:
The user will provide:
1. **Startup Context:** [Name, Funding Stage, Industry, Recent News].
2. **User Profile:** [Name, Job Title, Pitch, List of Projects with Tech Stacks].

---

### EXAMPLE OUTPUT FORMAT:

**Strategy Analysis:**
* **Likely Bottleneck:** The startup just shipped a RAG-based product; post-funding they likely struggle with retrieval quality, evaluation coverage, and making the system reliable enough for enterprise customers.
* **Selected Project:** "RAG Evaluation Pipeline with automated relevance scoring and hallucination detection."
* **The Wedge:** Use the user's experience building end-to-end RAG systems with evaluation layers to offer a concrete path from prototype to a measurable, production-grade AI system.

**Email Draft:**
Subject: RAG reliability for [Startup Name] / Congrats on the Seed round

Hi [CTO Name],   (or "Hi [Founder/CTO Name]," if name unknown)

Congrats on the funding. Seeing your push toward [Specific Feature] suggests you're at the stage where "good enough in demo" needs to become "reliable in production."

For most teams post-funding, the hard part isn't the LLM — it's building the evaluation layer that tells you *when* retrieval fails and *why* the model drifts. I recently built a RAG pipeline with automated relevance scoring and hallucination detection that reduced error rates by [Specific Metric].

I help early-stage AI teams architect and ship these end-to-end systems on a contract basis, so your core team stays focused on the product.

Open to a short technical call to see if my experience with [Specific Tech] fits where you're heading?

Best,
[User Name]

---

### TASK:
Analyze the following and generate the Strategy Analysis and Email Draft:
- **STARTUP CONTEXT:**
   - Name: {company_name}
   - CTO/Founder: {cto_name}
   - Product: {product_description}
   - Tech Stack: {tech_stack}
   - Recent news: {summary}
   - Funding: {funding_amount} {funding_round} on {funding_date}
   - Region: {country}
   
- **USER PROFILE:** 
{profile_yaml_as_text}
"""


CRITIQUE_REWRITE_PROMPT = """**Role:** You are a Senior Cold-Email Editor who has reviewed thousands of B2B outreach emails to technical founders. Your job is to critique a draft email against strict quality criteria, then rewrite it.

---

### CONTEXT (do not repeat in your output):
- **Startup:** {company_name} — {product_description}
- **CTO/Founder:** {cto_name}
- **Funding:** {funding_amount} {funding_round} on {funding_date}

---

### CRITIQUE CHECKLIST — evaluate the draft against every item:

1. **Structure compliance:** Does it follow this exact order?
   (a) Congrats line → (b) Their bottleneck → (c) Your proof → (d) The ask.
   Any deviation (e.g., proof before bottleneck, two CTAs) is a fail.

2. **Word count:** Is the email body (after "Subject:" line, excluding 
   signature) ≤ 150 words? Count carefully.

3. **No job-seeker language:** Flag any occurrence of "opportunity," 
   "resume," "job," "hiring," "position," "role," "looking for."

4. **No bullet points or bold text in the email body.** Prose only.

5. **Metrics are concrete or absent:** Flag vague claims like 
   "significantly improved," "90% faster," or "reduced errors" 
   without a specific baseline and result. If a real number isn't 
   available, the outcome should be described qualitatively.

6. **The ask is honest about intent:** The CTA should frame the call 
   as mutual qualification for a contract engagement — not as offering 
   free advice, "sharing ideas," or bringing a prepared solution.

7. **Personalization depth:** Does the email reference something 
   specific to THIS startup (product name, feature, tech stack, 
   market) — not a generic category like "AI startups"?

8. **Tone:** Peer-to-peer and technical, not sycophantic or salesy. 
   Flag phrases like "I'd love to," "I'm passionate about," 
   "exciting journey," "amazing work."

---

### INSTRUCTIONS:
1. **Critique:** List each checklist item (1-8) with PASS or FAIL 
   and a one-line reason.
2. **Rewrite:** Produce a corrected email that passes ALL 8 checks. 
   Keep everything that already works — only fix what failed. 
   If all 8 pass, return the original draft unchanged.

---

### OUTPUT FORMAT (follow exactly):

**Critique:**
1. Structure: PASS/FAIL — [reason]
2. Word count: PASS/FAIL — [count] words
3. Job-seeker language: PASS/FAIL — [flagged words or "none"]
4. Formatting: PASS/FAIL — [reason]
5. Metrics: PASS/FAIL — [flagged claims or "none"]
6. CTA honesty: PASS/FAIL — [reason]
7. Personalization: PASS/FAIL — [reason]
8. Tone: PASS/FAIL — [flagged phrases or "none"]

**Rewritten Email:**
Subject: [subject line]

[email body]

Best,
[User Name]

---

### DRAFT TO CRITIQUE:
{email_draft}
"""


EXTRACTION_PROMPT = """You are a data extraction assistant. Given a news article about a startup funding event, extract the following fields as a JSON object. If you cannot confidently extract a field, use null.

Field rules:
- company_name: official company name
- company_domain: bare domain only, no protocol or path (e.g. "example.com", not "https://example.com/about")
- funding_amount: human-readable string with currency symbol (e.g. "$100M", "\u20ac2.6M", "\u00a3500K"); null if unknown
- funding_round: one of Pre-Seed, Seed, Series A, Series B, Series C, Series D+, Grant, Other; null if unknown
- funding_date: ISO date string YYYY-MM-DD; null if unknown
- employee_count_estimate: integer estimate of current headcount; null if unknown
- region: one of Europe, USA, Other
- country: full country name (e.g. "United Kingdom")
- sector: one of GenAI, Other
- summary: 2-3 sentence description of the company and what they do
- is_relevant: true only if the article describes a GenAI startup that recently received Pre-Seed, Seed, Series A, Series B, or Series C funding. Set to false for Series D+ rounds, or for well-established scaleups with hundreds of employees (e.g. Anthropic, OpenAI, Cohere, Mistral at scale) — these companies seek full-time employees, not contractors
- relevance_reason: one sentence explaining why is_relevant is true or false

Example output:
{{
  "company_name": "Wonder",
  "company_domain": "wonder.ai",
  "funding_amount": "\u20ac2.6M",
  "funding_round": "Seed",
  "funding_date": "2024-03-15",
  "employee_count_estimate": 20,
  "region": "Europe",
  "country": "United Kingdom",
  "sector": "GenAI",
  "summary": "Wonder is a London-based AI creative studio that uses generative AI to produce visual content for brands. They help businesses create high-quality visual media at scale without traditional production costs.",
  "is_relevant": true,
  "relevance_reason": "Wonder is a GenAI startup that recently announced a \u20ac2.6M seed funding round."
}}

Article:
{article_text}"""


ENRICHMENT_PROMPT = """You are a data extraction assistant. Given web search results about a company called "{company_name}", extract the following fields as a JSON object. Return null for any field you are not confident about. Prefer no data over wrong data.

Field rules:
- cto_name: full name of the CTO, co-founder, or founding engineer. If multiple people are named, prefer the CTO over CEO over founder. Return null if you are not confident this is the right person at {company_name}.
- linkedin_url: LinkedIn profile URL of the CTO/founder. Must be a linkedin.com/in/ URL. Return null if not found or ambiguous.
- employee_count: integer estimate of current headcount from the search results. Return null if not mentioned.
- product_description: 1-2 sentence description of what {company_name} builds or does. Return null if unclear.
- tech_stack: comma-separated list of technologies {company_name} uses (e.g. "Python, PyTorch, React, AWS"). Only include items you are reasonably sure about. Return null if unknown.

Example output:
{{
  "cto_name": "Jane Smith",
  "linkedin_url": "https://www.linkedin.com/in/janesmith",
  "employee_count": 25,
  "product_description": "Acme AI builds automated document processing pipelines for legal firms using large language models.",
  "tech_stack": "Python, LangChain, React, AWS"
}}

Search results:
{snippets_text}"""
