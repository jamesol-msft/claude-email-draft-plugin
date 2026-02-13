---
name: email-draft
description: Generate draft email replies with executive style matching using a 3-stage workflow (search → context → generate). Integrates Agent 365 Mail MCP server with embedded executive style profiles for high-quality, personalized draft generation.
compatibility: Requires agent365-mail-proxy MCP server (included in plugin)
license: MIT
metadata:
  author: WorkIQ Skills
  version: "1.0"
  category: communication
  auto_generated: false
  mcp_servers:
    - agent365-mail-proxy
---

# Email Draft Generator

## Purpose

Intelligent email draft generator that creates high-quality, style-matched draft replies using a 3-stage workflow. Combines email search, context analysis, and executive writing style profiles to generate draft replies that match the recipient's communication preferences.

**Key Features**:
- **Email Search**: Natural language search with fallback strategies
- **Context Analysis**: Extracts key points and themes from original email
- **Style Matching**: 6-level fallback algorithm with 4 executive profiles
- **Draft Generation**: Claude-generated drafts matching recipient style
- **MCP Integration**: Uses agent365-mail-proxy for email operations

## MCP Servers Used

- **agent365-mail-proxy** - Email search, retrieval, draft creation (included in plugin package)

## Mandatory Workflow: 3-Stage Process

### Stage 1: Email Search & Discovery

**Purpose**: Locate the email requiring a reply using natural language search.

**Search Strategies** (3 strategies with fallback):

1. **Direct Email ID** (Highest confidence: 100%)
   - User provides exact message ID
   - Fastest, no ambiguity
   - Example: `email_id: "AAMkAGI2T..."`

2. **Natural Language Search** (High confidence: 85-95%)
   - User provides search query with sender/subject/keywords
   - Uses Agent 365 natural language processing
   - Example: `query: "email from Charles about Q4 budget"`

3. **Most Recent Email** (Fallback: 50-70%)
   - Returns most recent email from inbox
   - Used when search returns no results
   - Example: `query: "latest email"`

**MCP Tool Integration**:

```python
# Strategy 1: Direct Email ID
if email_id:
    message = mcp__agent365_mail_proxy__get_message(id=email_id)

# Strategy 2: Natural Language Search
else:
    results = mcp__agent365_mail_proxy__search_messages(
        query=user_query,  # e.g., "emails from Sarah about budget"
        top=5
    )
    # Parse results and select most relevant match
    message = results[0] if results else None

# Strategy 3: Fallback to latest
if not message:
    results = mcp__agent365_mail_proxy__search_messages(
        query="recent emails",
        top=1
    )
    message = results[0] if results else None
```

**Output**:
- Message ID, sender, subject, received date
- Confidence score (0.5-1.0)
- Search strategy used

### Stage 2: Context Analysis

**Purpose**: Extract key context from the original email to inform the draft reply.

**Context Elements Extracted**:
1. **Email metadata**: Sender name/email, subject, date
2. **Key points**: Main topics and questions in the email
3. **Tone indicators**: Urgency level, formality, sentiment
4. **Questions**: Explicit or implicit questions requiring answers
5. **Action items**: Any requests or action items mentioned

**Implementation**:

```python
# Retrieve full message content
message = mcp__agent365_mail_proxy__get_message(id=message_id)

# Extract context elements
context = {
    "sender": {
        "name": message.from.name,
        "email": message.from.address
    },
    "subject": message.subject,
    "received_date": message.receivedDateTime,
    "body_preview": message.bodyPreview[:500],  # First 500 chars
    "key_points": extract_key_points(message.body),
    "questions": extract_questions(message.body),
    "tone": analyze_tone(message.body),
    "urgency": detect_urgency(message.subject, message.body)
}
```

**Analysis Techniques**:
- **Key points**: Extract sentences with high information density
- **Questions**: Identify sentences ending with "?" or containing "when", "what", "how", "why"
- **Tone**: Analyze formality markers (contractions, greetings, signoffs)
- **Urgency**: Detect keywords like "urgent", "asap", "deadline", dates in subject

**Performance**:
- Execution time: 5-15 seconds
- No external API calls (local processing)

### Stage 3: Style Profile Selection & Draft Generation

**Purpose**: Select appropriate writing style and generate draft reply using Claude.

**Profile Matching Algorithm** (6-level fallback):

1. **Level 1: Exact email match** (100% confidence)
   - Matches sender email to known executive profiles
   - Example: charles.lamanna@microsoft.com → charles-lamanna

2. **Level 2: Fuzzy name match** (80-95% confidence)
   - Matches sender name with variations
   - Example: "Charles Lamanna" → charles-lamanna

3. **Level 3: Context-based inference** (60-80% confidence)
   - Analyzes subject/body keywords to infer appropriate profile
   - Example: "architecture review" → nirav-shah (technical)

4. **Level 4: Audience-level fallback** (50-60% confidence)
   - Maps to profile by organizational level
   - Example: Unknown VP → charles-lamanna (executive profile)

5. **Level 5: User default profile** (45% confidence)
   - Uses user's configured default profile if set

6. **Level 6: System default fallback** (40% confidence)
   - Uses james-oleinik (collaborative, balanced) as universal fallback

**Profile Matching Implementation**:

```python
def match_profile(sender_email, sender_name, email_context):
    """Match sender to executive style profile using 6-level fallback"""
    email_lower = sender_email.lower()

    # Level 1: Exact email match
    for profile_name, patterns in PROFILE_EMAIL_PATTERNS.items():
        if any(pattern in email_lower for pattern in patterns):
            return {
                "profile": profile_name,
                "confidence": 1.0,
                "level": 1,
                "reason": "Exact email match"
            }

    # Level 2: Fuzzy name match (not implemented in this version)

    # Level 3: Context-based inference
    keywords = extract_keywords(email_context["subject"], email_context["body_preview"])
    for profile_name, triggers in PROFILE_KEYWORD_TRIGGERS.items():
        if any(kw in keywords for kw in triggers):
            return {
                "profile": profile_name,
                "confidence": 0.7,
                "level": 3,
                "reason": f"Context keywords: {keywords}"
            }

    # Levels 4-5: Not implemented in this version

    # Level 6: System default fallback
    return {
        "profile": "james-oleinik",
        "confidence": 0.4,
        "level": 6,
        "reason": "Default fallback (collaborative, balanced style)"
    }
```

**Draft Generation with Claude**:

```python
# Build prompt with style guidance and context
prompt = f"""You are drafting an email reply in the style of {profile_name}.

STYLE PROFILE:
{get_profile_guidance(profile_name)}

ORIGINAL EMAIL:
From: {context["sender"]["name"]} <{context["sender"]["email"]}>
Subject: {context["subject"]}
Date: {context["received_date"]}

{context["body_preview"]}

KEY POINTS TO ADDRESS:
{format_key_points(context["key_points"])}

QUESTIONS TO ANSWER:
{format_questions(context["questions"])}

Generate a draft reply that:
1. Matches the style profile exactly (tone, structure, length)
2. Addresses all key points and questions
3. Maintains appropriate formality for the relationship
4. Includes clear next steps if needed
5. Uses recipient's name in greeting if appropriate

Draft reply (email body only, no subject line):
"""

# Call Claude API (via agent or direct)
draft_body = generate_with_claude(prompt)

# Create draft in mailbox
draft_id = mcp__agent365_mail_proxy__create_draft(
    to=context["sender"]["email"],
    subject=f"Re: {context['subject']}",
    body=draft_body
)
```

**Output**:
- Draft ID (AAMkAD...)
- Draft body content
- Style profile used
- Confidence score
- Location: Drafts folder in mailbox

## Executive Style Profiles

### Profile Matching Patterns

```python
PROFILE_EMAIL_PATTERNS = {
    "charles-lamanna": ["charles@", "clamanna@", "charles.lamanna@"],
    "nirav-shah": ["nirav@", "nshah@", "nirav.shah@"],
    "robert-bruckner": ["robert@", "rbruckner@", "robert.bruckner@"],
    "james-oleinik": ["james@", "joleinik@", "james.oleinik@"]
}

PROFILE_KEYWORD_TRIGGERS = {
    "charles-lamanna": ["strategy", "business-strategy", "planning", "roadmap", "vision", "platform"],
    "nirav-shah": ["technical", "architecture", "engineering", "implementation", "timeline"],
    "robert-bruckner": ["budget", "financial", "cost", "data", "metrics", "analytics"],
    "james-oleinik": ["team", "collaboration", "alignment", "decision", "coordination"]
}
```

### Charles Lamanna

**Email**: charles.lamanna@microsoft.com
**Role**: Corporate Vice President, Business Applications and Platform

**Tone**: Conversational-professional (3.5/5), strategic, engaging
- Uses contractions: Yes
- Greeting: First-name basis
- Signoff: "Best, Charles" or "Thanks, Charles"

**Structure**:
- Paragraph length: Short (2-4 sentences)
- Email length: Moderate (150-400 words)
- Uses bullets: Frequently
- Paragraph count: 2-4 paragraphs

**Opening**:
- Acknowledges context: Yes
- Uses BLUF (Bottom Line Up Front): Yes
- Common phrases:
  - "Thanks for raising"
  - "Quick update on"
  - "Following up on our discussion"
  - "Good timing on this"

**Content**:
- Detail level: Balanced (business + tactical)
- Data usage: Moderate (key metrics only)
- Decision framing: Options with recommendation
- Problem-solving: Strategic-collaborative

**Closing**:
- Explicit next steps: Yes
- Clear timeline: Yes
- Common phrases:
  - "I'll sync with X this week"
  - "Will circle back by Friday"
  - "Let me know if you need anything before then"

**Example**:
```
Thanks for following up on Q4. Here's where we are:

• Revenue tracking to plan
• Cost overruns in cloud
• Timeline: finalize by Friday

I'll sync with Finance on the cloud costs this week and circle back with a revised forecast by Friday.

Let me know if you need anything before then.

Best,
Charles
```

---

### Nirav Shah

**Email**: nirav.shah@microsoft.com
**Role**: Corporate Vice President, Engineering

**Tone**: Action-oriented (3.0/5), decisive, technical, timeline-focused
- Uses contractions: Yes
- Greeting: First-name basis
- Signoff: "Thanks, Nirav" or "Nirav"

**Structure**:
- Paragraph length: Medium (3-5 sentences)
- Email length: Moderate (150-400 words)
- Uses bullets: Occasional
- Uses numbered lists: Frequently
- Paragraph count: 2-5 paragraphs

**Opening**:
- Acknowledges context: Yes
- Uses BLUF: Yes (direct)
- Common phrases:
  - "Here's the situation"
  - "Quick status on"
  - "Update on our timeline"
  - "Action needed on"

**Content**:
- Detail level: Tactical
- Data usage: Heavy (metrics, percentages, timelines)
- Decision framing: Single-path (decisive)
- Technical depth: High
- Problem-solving: Decisive

**Closing**:
- Explicit next steps: Yes
- Clear owners: Yes
- Common phrases:
  - "I'll have the team deliver X by Y"
  - "We'll complete this by end of week"
  - "Timeline: Z completes by Friday"
  - "Owner: [Name] to drive this"

**Example**:
```
Here's where we are on the architecture review:

1. Phase 1 complete (95% coverage)
2. Phase 2 in progress (ETA: Feb 15)
3. Timeline: Final review Feb 20

I'll have the team deliver the security assessment by Wednesday. Owner: Sarah Chen to drive completion.

Thanks,
Nirav
```

---

### Robert Bruckner

**Email**: robert.bruckner@microsoft.com
**Role**: Corporate Vice President, Data and Analytics

**Tone**: Direct (2.5/5), data-driven, strategic, analytical
- Uses contractions: No
- Greeting: First-name basis
- Signoff: "Robert" or "Regards, Robert"

**Structure**:
- Paragraph length: Short (2-3 sentences)
- Email length: Terse (50-150 words)
- Uses bullets: Frequently
- Paragraph count: 2-3 paragraphs (minimal)

**Opening**:
- Acknowledges context: No (direct BLUF)
- Uses BLUF: Yes
- Common phrases:
  - "Bottom line"
  - "Key findings"
  - "Data shows"
  - "Analysis indicates"

**Content**:
- Detail level: Tactical
- Data usage: Heavy (metrics, data-focused)
- Decision framing: Options with recommendation
- Problem-solving: Data-driven
- No small talk or preamble

**Closing**:
- Explicit next steps: Yes
- Clear dates: Yes
- Common phrases:
  - "I will follow up by [date]"
  - "Next step: [action] by [date]"
  - "Will provide update on [date]"

**Example**:
```
Bottom line: $150K over budget in Q4.

• Revenue: On track (102% of target)
• Costs: 8% over ($150K)
• Recommendation: Defer Feature X to Q1

Next: CFO approval by Friday

Robert
```

---

### James Oleinik

**Email**: james.oleinik@microsoft.com
**Role**: Senior Technical Program Manager

**Tone**: Collaborative (3.2/5), balanced, team-focused, thoughtful
- Uses contractions: Yes
- Greeting: First-name basis
- Signoff: "Thanks, James" or "Happy to discuss further, James"

**Structure**:
- Paragraph length: Short (2-4 sentences)
- Email length: Moderate (150-400 words)
- Uses bullets: Frequently
- Paragraph count: 2-4 paragraphs

**Opening**:
- Acknowledges context: Yes
- Uses BLUF: Yes
- Common phrases:
  - "Thanks for bringing this up"
  - "Following up on"
  - "Quick update"
  - "Wanted to share"

**Content**:
- Detail level: Balanced (business + technical)
- Data usage: Moderate
- Decision framing: Options with recommendation
- Technical depth: Balanced
- Problem-solving: Collaborative

**Closing**:
- Explicit next steps: Yes
- Clear timeline: Yes
- Team accountability: Yes
- Common phrases:
  - "Let's sync on this"
  - "I'll coordinate with the team"
  - "Will follow up by [date]"
  - "Happy to discuss further"

**Example**:
```
Thanks for the Q4 planning discussion. Here's my take:

• Budget: Aligned with finance (Sarah confirming)
• Timeline: Feb 28 realistic
• Next: Team sync Friday to finalize

I'll coordinate with the team on the timeline details and follow up with you by Thursday.

Happy to discuss further if needed.

Thanks,
James
```

---

## MCP Tool Integration

### search_messages

**Description**: Search for email messages using natural language queries.

**Parameters**:
- `query` (string, required): Natural language search query
  - Examples: "emails from Sarah", "budget discussion last week", "unread messages"
- `top` (integer, optional): Max results (default: 10, max: 50)

**Returns**: Array of message objects with:
- `id`: Message ID (for get_message)
- `from`: Sender name and email
- `subject`: Email subject line
- `receivedDateTime`: When received
- `bodyPreview`: First 100 chars of body

**Example**:
```python
results = mcp__agent365_mail_proxy__search_messages(
    query="emails from Charles about Q4 budget",
    top=5
)
```

### get_message

**Description**: Retrieve full details of a specific email message.

**Parameters**:
- `id` (string, required): Message ID from search results

**Returns**: Full message object with:
- `id`, `from`, `toRecipients`, `subject`
- `body`: Full email body (HTML or text)
- `receivedDateTime`, `conversationId`
- `bodyPreview`: Preview text

**Example**:
```python
message = mcp__agent365_mail_proxy__get_message(
    id="AAMkAGI2T..."
)
```

### create_draft

**Description**: Create a draft email message in the user's mailbox.

**Parameters**:
- `to` (string, required): Recipient email address
- `subject` (string, required): Email subject line
- `body` (string, required): Email body content
- `cc` (string, optional): CC recipient email

**Returns**: Draft ID (AAMkAD...)

**Example**:
```python
draft_id = mcp__agent365_mail_proxy__create_draft(
    to="charles.lamanna@microsoft.com",
    subject="Re: Q4 Budget Review",
    body=draft_content,
    cc="finance-team@microsoft.com"
)
```

**Important**: Draft is saved to Drafts folder. User must review and send manually. This tool never sends emails automatically.

## Safety Rules

### ✅ SAFE OPERATIONS (Use Freely)

- `search_messages` - Search mailbox (read-only)
- `get_message` - Retrieve email (read-only)
- `create_draft` - Create draft in mailbox (safe, user reviews before sending)
- Local context analysis (no external API calls)
- Style profile matching (local processing)

### ⚠️ CONFIRMATION REQUIRED

- Draft creation without preview (show user draft content first)
- Drafts addressing >5 recipients (bulk communication risk)
- Drafts with sensitive keywords (budget, confidential, etc.)

### ❌ FORBIDDEN OPERATIONS

- **Never send emails automatically** - Always create drafts, never send
- **Never modify existing emails** - Only create new drafts
- **Never delete emails** - No destructive operations
- **Never access other users' mailboxes** - Only user's own mailbox
- **Never store email content permanently** - Process and discard after draft creation

## Tool Call Quality: Good vs Bad Examples

### ✅ GOOD: Complete 3-Stage Workflow

**Scenario**: "Draft a reply to Charles Lamanna's email about Q4 budget"

```python
# Stage 1: Email Search
results = mcp__agent365_mail_proxy__search_messages(
    query="emails from charles.lamanna@microsoft.com about Q4 budget",
    top=5
)
# ✅ Specific sender + subject
# ✅ Limited results

message_id = results[0]["id"]

# Stage 2: Context Gathering
message = mcp__agent365_mail_proxy__get_message(id=message_id)
context = analyze_email_context(message)
# ✅ Full message retrieval
# ✅ Context extraction

# Stage 3: Style & Generation
profile_match = match_profile(
    sender_email=message.from.address,
    sender_name=message.from.name,
    email_context=context
)
# ✅ Profile matching with fallback

draft_body = generate_draft(profile_match, context)
# ✅ Style-matched generation

draft_id = mcp__agent365_mail_proxy__create_draft(
    to=message.from.address,
    subject=f"Re: {message.subject}",
    body=draft_body
)
# ✅ Draft created in mailbox
# ✅ User can review before sending
```

**Why Good**:
- ✅ Complete 3-stage workflow
- ✅ Specific search criteria
- ✅ Full context analysis
- ✅ Style-matched with high confidence
- ✅ Draft saved for user review

### ❌ BAD: Skipped Stages and Auto-Send

**Scenario**: "Send a reply to latest email"

```python
# Anti-pattern 1: Vague search
results = mcp__agent365_mail_proxy__search_messages(query="latest email", top=1)
# ❌ No specific criteria (could be spam, newsletter, etc.)

# Anti-pattern 2: Skip context analysis
# (Proceeds directly to draft generation)
# ❌ No context extraction
# ❌ No key points identified

# Anti-pattern 3: Skip style matching
# (Uses generic tone)
# ❌ No profile matching
# ❌ May not match recipient's expectations

# Anti-pattern 4: Auto-send (FORBIDDEN)
send_email(...)  # This tool doesn't exist in MCP server
# ❌ NEVER send automatically
# ❌ User must review before sending
```

**Why Bad**:
- ❌ Vague search criteria
- ❌ Skipped context analysis
- ❌ No style matching
- ❌ Attempted auto-send (forbidden)

### ✅ GOOD: Graceful Fallback

**Scenario**: Search returns no results, fall back to recent emails

```python
# Stage 1: Specific search
results = mcp__agent365_mail_proxy__search_messages(
    query="emails from unknown.person@contoso.com about project alpha",
    top=5
)

if not results:
    # ✅ Graceful fallback to broader search
    print("No results for specific search, trying broader criteria...")
    results = mcp__agent365_mail_proxy__search_messages(
        query="emails from unknown.person@contoso.com",
        top=5
    )

if not results:
    # ✅ Final fallback to recent emails
    print("No emails found from sender, showing recent emails...")
    results = mcp__agent365_mail_proxy__search_messages(
        query="recent emails",
        top=10
    )
    # ✅ Ask user to select the correct email

# Continue with stages 2 and 3
# ✅ Workflow completes despite search challenges
```

**Why Good**:
- ✅ Graceful fallback strategy
- ✅ User informed of fallback
- ✅ Workflow completes successfully
- ✅ User involved in email selection

## Usage Examples

### Example 1: Draft Reply to Known Executive

**Input**:
```
Draft a reply to Charles Lamanna's email about Q4 budget review
```

**Execution**:
```
[Stage 1] Searching for email...
✓ Found: "Q4 Budget Review - Final Decisions" from Charles Lamanna
  Email ID: AAMkAGI2T...
  Confidence: 0.95

[Stage 2] Analyzing context...
✓ Key points: Budget overrun discussion, revised forecast needed
✓ Questions: "What's the timeline?" "Who's accountable?"
✓ Urgency: High (deadline mentioned: Friday)

[Stage 3] Matching style profile...
✓ Profile: charles-lamanna (conversational-professional)
  Confidence: 1.0 (exact email match)

Generating draft with Claude...
✓ Draft generated (287 words, 3 paragraphs)

Creating draft in mailbox...
✓ Draft created: AAMkAD...

✅ Draft ready for review in Drafts folder
```

**Draft Content**:
```
Thanks for following up on Q4, Charles. Here's the revised outlook:

• Budget: $150K overrun (cloud costs)
• Forecast: Updated numbers ready by Thursday
• Timeline: Final review Friday

I'll sync with Finance on the cloud cost analysis this week and get you the revised forecast by Thursday morning. Sarah Chen is leading the detailed breakdown.

Let me know if you need anything before then.

Best,
[Your name]
```

### Example 2: Draft Reply to Unknown Sender

**Input**:
```
Draft a reply to the latest email from john.doe@contoso.com
```

**Execution**:
```
[Stage 1] Searching for email...
✓ Found: "Project Update Request" from John Doe
  Email ID: AAMkAGI2T...
  Confidence: 0.70

[Stage 2] Analyzing context...
✓ Key points: Project status request, timeline question
✓ Questions: "When will Phase 2 complete?"
✓ Urgency: Medium

[Stage 3] Matching style profile...
⚠ No exact match found for john.doe@contoso.com
✓ Using default profile: james-oleinik (collaborative, balanced)
  Confidence: 0.4 (system default)

Generating draft with Claude...
✓ Draft generated (215 words, 3 paragraphs)

Creating draft in mailbox...
✓ Draft created: AAMkAD...

✅ Draft ready for review in Drafts folder
⚠ Note: Used default style profile (collaborative)
```

## Performance Benchmarks

### Typical Execution Times

| Stage | Operation | Typical | Max |
|-------|-----------|---------|-----|
| 1 | Email Search | 3-10s | 30s |
| 2 | Context Analysis | 5-15s | 30s |
| 3 | Style & Generation | 10-20s | 45s |
| **Total** | **End-to-End** | **20-45s** | **90s** |

**Note**: Agent 365 natural language search can take 10-30s due to semantic processing.

### Resource Usage

- **Memory**: 50-150 MB per draft request
- **MCP Calls**: 2-4 (search + get_message + create_draft)
- **Network**: 2-5 MB (email retrieval + draft creation)

## Related Skills

- **email-context-gathering**: Full thread context analysis (more comprehensive than this skill's Stage 2)
- **executive-style-profiles**: Full profile selection with advanced matching
- **meeting-preparation**: Uses email-draft for meeting follow-ups
- **status-updates**: Uses email-draft for executive updates

## File Structure

```
plugin-package/
├── agent365_mcp_proxy.py           # MCP server (430 lines)
├── skills/
│   └── email-draft/
│       └── SKILL.md                # This file (760 lines)
└── README.md                       # Plugin installation guide
```

---

**Note**: This skill is part of the email-auto-draft plugin. It provides a simplified 3-stage workflow compared to the full email-auto-draft orchestrator skill in the main WorkIQ skills library. This version is optimized for direct Claude Desktop integration via MCP.
