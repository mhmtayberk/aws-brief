"""
Centralized prompt templates for AI engines.

This module provides consistent, high-quality prompts for all AI engines
to ensure uniform output quality and structure.
"""
from src.utils.config import settings


def get_system_prompt() -> str:
    """
    Get the system prompt for AI engines.
    
    Returns:
        System prompt string with role definition and guidelines
    """
    return f"""You are a Senior Cloud Architect & Security Analyst specializing in AWS.

**Your Audience**: DevOps Engineers, CTOs, Cloud Architects, SREs
**Output Language**: {settings.SUMMARY_LANGUAGE}
**Format**: Markdown with bold headers
**Tone**: Professional, direct, actionable

Your task is to analyze AWS updates and provide actionable insights that help teams make informed decisions."""


def get_summarize_prompt(text: str) -> str:
    """
    Get the summarization prompt for a given AWS update text.
    
    Args:
        text: The AWS update text to analyze
        
    Returns:
        Formatted prompt string with structure and guidelines
    """
    return f"""Analyze this AWS update with precision and provide actionable insights:

**Required Structure**:
1. **Title**: Punchy 5-8 words capturing core value
2. **What**: 2-3 sentences explaining the technical change
3. **Why**: Business/technical impact (cost savings? security improvement? performance boost?)
4. **Impact Level**: Exactly ONE of [CRITICAL, HIGH, MEDIUM, LOW, INFO]
5. **Action Required**: Yes/No + brief action if Yes (max 1 sentence)

**Guidelines**:
- Be direct and avoid marketing fluff
- Use bullet points for clarity when listing multiple items
- Highlight specific numbers, percentages, and metrics
- Focus on practical implications for engineering teams
- Maximum 200 words total

**Example Output**:
**Title**: RDS Blue/Green Deployments Now GA

**What**: Amazon RDS now supports blue/green deployments for MySQL and PostgreSQL databases. This feature enables zero-downtime database updates with automatic traffic switching and instant rollback capabilities. The system maintains two identical environments and switches traffic only after validation.

**Why**: Eliminates traditional maintenance windows (saving 2-4 hours per deployment), reduces deployment risk by 90% through instant rollback, and enables safe production schema changes without downtime. Critical for high-availability applications with strict SLA requirements.

**Impact Level**: HIGH

**Action Required**: Yes - Audit critical production databases within 30 days. Prioritize databases with frequent schema changes or those requiring maintenance windows. Plan migration for high-availability workloads first.

---

**Now analyze this AWS update**:
{text}
"""


def get_smart_digest_prompt(items_text: str) -> str:
    """
    Get the smart digest prompt for categorizing and prioritizing multiple AWS updates.
    
    Args:
        items_text: Formatted list of news items with titles, summaries, and metadata
        
    Returns:
        Formatted prompt string for smart digest generation
    """
    return f"""Analyze these AWS updates and create a prioritized smart digest with actionable categorization.

**Updates to Analyze**:
{items_text}

**Categorization Rules** (assign each update to exactly ONE category):

1. **CRITICAL** - Immediate action required
   - Security patches, CVEs, breaking changes
   - Service outages, deprecations with deadlines
   - Include: Impact level (HIGH/MEDIUM/LOW), specific action, deadline
   - Example: "CVE-2024-1234: RDS PostgreSQL SQL injection - Patch by Feb 15"

2. **COST_OPTIMIZATION** - Money-saving opportunities
   - New pricing models, cost reduction features
   - Efficiency improvements, resource optimization
   - Include: Estimated savings percentage, implementation complexity
   - Example: "Graviton3: 30% cost reduction, drop-in replacement"

3. **NEW_FEATURES** - Capabilities worth exploring
   - New services, features, integrations
   - GA announcements, regional expansions
   - Include: Brief description, primary use case
   - Example: "S3 Express One Zone: 10x faster, ideal for analytics workloads"

4. **GENERAL** - Informational updates
   - Minor improvements, documentation updates
   - Non-urgent announcements

**Output Format**:

🚨 **CRITICAL - Action Required** (X items)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[For each item:]
- **[Title]**: [Impact] - [Required Action] - Deadline: [Date]
  [1-2 sentence explanation]

💰 **COST OPTIMIZATION** (X opportunities)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[For each item:]
- **[Title]**: [Savings %] - [Implementation effort: Low/Medium/High]
  [How to implement in 1 sentence]

✨ **NEW FEATURES** (X items)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[For each item:]
- **[Title]**: [Brief description + use case]

📌 **SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Total Updates: X
- Critical Actions: X (deadlines within 30 days: Y)
- Cost Savings Opportunities: X (estimated total savings: Z%)
- New Features: X
- Estimated Review Time: X minutes

**Quality Guidelines**:
- Prioritize by business impact and urgency
- Be specific with actions (not "review" but "migrate X to Y by date Z")
- Use emojis sparingly for visual hierarchy only
- Maximum 500 words total
- Language: {settings.SUMMARY_LANGUAGE}
- Focus on actionable insights, not just information

**Critical**: If no items fit CRITICAL or COST_OPTIMIZATION, state "None" for that category. Don't force categorization.
"""


# Helper function for backward compatibility
def format_prompt_for_engine(text: str, engine_type: str = "generic") -> dict:
    """
    Format prompts for specific engine types if needed.
    
    Args:
        text: The text to analyze
        engine_type: Type of AI engine (for future customization)
        
    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    return {
        "system": get_system_prompt(),
        "user": get_summarize_prompt(text)
    }
