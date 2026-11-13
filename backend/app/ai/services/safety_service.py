import re
from typing import List, Tuple
from app.core.config import settings

# Standardized Clinical Disclaimer
CLINICAL_DISCLAIMER = (
    "Medicall AI is an informational triage and healthcare coordination assistant, not a diagnostic or prescriptive medical device. "
    "All insights are preliminary and educational; they do not constitute formal medical diagnoses or clinical advice. "
    "Always consult a licensed medical practitioner for evaluation. In life-threatening emergencies, call "
    f"{settings.EMERGENCY_PHONE_NUMBER} or proceed immediately to the nearest Emergency Room."
)

# Deterministic Red-Flag Emergency Patterns
RED_FLAG_PATTERNS = [
    # Cardiac emergencies
    (
        r"\b(chest\s*pain|crushing\s*chest|radiating\s*to\s*(left\s*)?arm|heart\s*attack|cardiac\s*arrest|pressure\s*in\s*chest|chest\s*pressure|chest\s*tightness|tightness\s*in\s*chest)\b",
        "Suspected Acute Coronary Syndrome"
    ),
    # Stroke / FAST indicators (including clinical "rule out a stroke")
    (
        r"\b(face\s*droop(ing)?|slurr(ed)?\s*speech|loss\s*of\s*speech|sudden\s*paralysis|sudden\s*numbness|one\s*side(d)?\s*weakness|weakness\s*(on\s*)?(one|left|right)\s*side|stroke|cerebrovascular\s*accident|tia)\b",
        "Suspected Acute Cerebrovascular Event (Stroke)"
    ),
    # Severe respiratory distress (including "struggling to breathe", "difficulty breathing", "shortness of breath")
    (
        r"\b(cannot\s*breathe|can'?t\s*breathe|struggling\s*to\s*breathe|gasping\s*for\s*air|turning\s*blue|cyanosis|choking|severe\s*shortness\s*of\s*breath|shortness\s*of\s*breath|difficulty\s*breathing|trouble\s*breathing|stridor)\b",
        "Severe Respiratory Compromise"
    ),
    # Acute hemorrhage / trauma (including "bleeding has started again", "bleeding won't stop")
    (
        r"\b(coughing\s*blood|hemoptysis|vomiting\s*blood|hematemesis|uncontrolled\s*bleed(ing)?|arterial\s*bleed|heavy\s*bleed(ing)?|bleeding\s*heavily|bleeding\s*(has\s*)?started\s*again|bleeding\s*(won'?t|will\s*not)\s*stop|severe\s*bleed(ing)?|bleeding\s*profusely)\b",
        "Severe Hemorrhage / Acute Bleeding"
    ),
    # Altered consciousness
    (
        r"\b(unconscious|unresponsive|passing\s*out|fainting\s*repeatedly|seizure\s*ongoing|status\s*epilepticus)\b",
        "Altered Level of Consciousness"
    ),
    # Acute anaphylaxis (including "throat is swelling", "swelling in throat")
    (
        r"\b(anaphylaxis|throat\s*closing|swelling\s*of\s*(tongue|throat|lips)|(throat|tongue|lips)\s*(is\s*)?swelling|swelling\s*in\s*(throat|tongue|lips)|severe\s*allergic\s*reaction)\b",
        "Suspected Acute Anaphylaxis"
    ),
    # Crisis / Self-Harm Risk (including "hurting myself", "harming myself")
    (
        r"\b(kill\s*myself|suicid(e|al)|end\s*my\s*life|want\s*to\s*die|hurt(ing)?\s*myself|harm(ing)?\s*myself|injur(e|ing)\s*myself|self\s*harm)\b",
        "Crisis / Self-Harm Risk"
    ),
]

# True negation only - "rule out" is NEVER treated as negation
_NEGATION_PREFIX = re.compile(
    r"\b(no|not|never|don'?t|do\s+not|doesn'?t|does\s+not|didn'?t|did\s+not|denies|denied|denying|negative\s+for|without|free\s+of)\s+(any\s+)?([a-z0-9_-]+\s+){0,3}$",
    re.IGNORECASE
)

_FOLLOWING_NEGATION = re.compile(
    r"^\s*(is\s+absent|is\s+negative|not\s+present|is\s+not\s+present)",
    re.IGNORECASE
)

_HISTORICAL_PRECEDING = re.compile(
    r"\b(had|experienced|suffered|history\s+of|prior\s+history\s+of|past\s+history\s+of|diagnosed\s+with|treated\s+for)\s+(an?\s+)?([a-z0-9_-]+\s+){0,3}$",
    re.IGNORECASE
)

_HISTORICAL_FOLLOWING = re.compile(
    r"^\s*(\d+\s+(years?|months?|weeks?)\s+ago|three\s+years\s+ago|in\s+(19|20)\d\d|in\s+the\s+past|previously|which\s+resolved|that\s+resolved)",
    re.IGNORECASE
)

_RESOLVED_MARKER = re.compile(
    r"\b(stopped|resolved|recovered|went\s+away|ceased|disappeared|no\s+longer|fine|healed|okay|well)\b",
    re.IGNORECASE
)

_RECURRENCE_MARKER = re.compile(
    r"\b(back\s*again|started\s*again|returned|recurred|recurring|recurrent|again|worse|worsening|severe|acute|(now|today|currently)\s+(having|experiencing|feeling|suffering|hurting|worse|severe|acute|pain))\b",
    re.IGNORECASE
)


class SafetyService:
    """
    Dedicated clinical safety layer for Medicall AI.
    Executes deterministic checks before any LLM processing to identify medical
    emergencies and safeguard patients from delays in acute clinical care.
    Incorporates syntactic negation and historical context handling to prevent false alerts
    while strictly protecting acute emergences and recurrences.
    """

    @classmethod
    def _is_active_emergency(cls, text: str, start: int, end: int) -> bool:
        """
        Evaluates context surrounding an emergency keyword to exclude:
        1. Negated expressions ('no chest pain', 'denies shortness of breath')
        2. Historical past events without acute recurrence ('had heart attack in 2020, feel fine today')
        """
        pre_text = text[:start]
        post_text = text[end:]

        # 1. Preceding negation check within the immediate clause
        last_punct = max(pre_text.rfind("."), pre_text.rfind(";"), pre_text.rfind("!"), pre_text.rfind("?"), pre_text.rfind(","))
        clause_pre = pre_text[last_punct + 1:] if last_punct != -1 else pre_text

        if _NEGATION_PREFIX.search(clause_pre):
            return False

        # 2. Following negation check (e.g. 'chest pain is absent')
        if _FOLLOWING_NEGATION.search(post_text):
            return False

        # 3. Historical framing check
        is_historical = False
        if _HISTORICAL_PRECEDING.search(clause_pre) or re.search(r"\b(history\s+of|prior\s+history\s+of|past\s+history\s+of)\b", clause_pre, re.IGNORECASE):
            is_historical = True
        elif _HISTORICAL_FOLLOWING.search(post_text):
            is_historical = True

        if is_historical:
            # Check for active recurrence vs resolved state
            has_recurrence = bool(_RECURRENCE_MARKER.search(post_text) or _RECURRENCE_MARKER.search(clause_pre))
            has_resolved = bool(_RESOLVED_MARKER.search(post_text))

            if has_recurrence and not has_resolved:
                return True
            if has_resolved:
                if re.search(r"\b(but|however)\s+([a-z0-9_-]+\s+){0,3}(started\s+again|back\s+again|recurred|worse|severe)", post_text, re.IGNORECASE):
                    return True
                return False
            return False

        return True

    @classmethod
    def evaluate_emergency_red_flags(cls, text: str) -> Tuple[bool, List[str], str]:
        """
        Scans input text for deterministic emergency indicators with negation and historical context awareness.

        Returns:
            Tuple[is_emergency: bool, matched_conditions: List[str], guidance: str]
        """
        if not text:
            return False, [], ""

        matched_conditions: List[str] = []

        for pattern, label in RED_FLAG_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                if cls._is_active_emergency(text, m.start(), m.end()):
                    if label not in matched_conditions:
                        matched_conditions.append(label)
                    break

        if matched_conditions:
            hotline = settings.EMERGENCY_PHONE_NUMBER
            guidance = (
                f"POTENTIAL MEDICAL EMERGENCY DETECTED ({', '.join(matched_conditions)}). "
                f"Please STOP using online appointment scheduling and call local emergency services ({hotline}) "
                f"or proceed directly to the nearest hospital Emergency Room immediately. "
                f"Medicall AI is an informational scheduling assistant and cannot dispatch emergency medical responders or provide emergency care."
            )
            return True, matched_conditions, guidance

        return False, [], ""

    @staticmethod
    def get_clinical_disclaimer() -> str:
        """Returns the standardized non-diagnostic clinical disclaimer."""
        return CLINICAL_DISCLAIMER

    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """
        Sanitizes text by filtering potential system instruction override attempts
        and trimming excessive whitespace.
        """
        if not text:
            return ""

        # Remove prompt injection patterns
        sanitized = re.sub(
            r"(ignore\s*all\s*previous\s*instructions|system\s*prompt|disregard\s*instructions)",
            "[filtered]",
            text,
            flags=re.IGNORECASE
        )
        return sanitized.strip()

    @staticmethod
    def verify_output_safety(output_text: str) -> str:
        """
        Validates AI response to prevent unintended diagnostic or prescriptive assertions.
        """
        if not output_text:
            return output_text

        # If model accidentally included strong diagnostic claims without hedging, reinforce disclaimer
        diagnostic_patterns = [
            r"\byou\s+have\s+(diabetes|cancer|pneumonia|appendicitis|covid)\b",
            r"\btake\s+\d+\s*(mg|milligrams|tablets|pills)\b",
        ]
        needs_reinforcement = any(re.search(p, output_text, re.IGNORECASE) for p in diagnostic_patterns)

        if needs_reinforcement and CLINICAL_DISCLAIMER not in output_text:
            return f"{output_text}\n\nNotice: {CLINICAL_DISCLAIMER}"

        return output_text

