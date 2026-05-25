import re
import random as _random
from formats.shared import ALLOWED_NAMES, normalize_quotes, base_validate

FORMAT_NAME = "letter"

SYSTEM_PROMPT = (
    "You write simple letters between two people using only very basic words. "
    "Start with 'Dear [Name],' and end with a sign-off like "
    "'Your friend, [Name]' or 'Love, [Name]'. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas."
)

RELATIONSHIPS = [
    "friend", "family", "neighbor", "pen pal", "classmate",
    "coworker", "old friend",
]

TOPICS = [
    # News sharing
    "telling about a new pet",
    "telling about a trip",
    "telling about school",
    "telling about a new baby in the family",
    "telling about a new job",
    "telling about moving to a new house",
    "telling about learning something new",
    "telling about growing a garden",
    "telling about a funny thing that happened",
    "telling about a big storm",
    "telling about a holiday",
    "telling about a birthday party",
    "telling about meeting someone new",
    "telling about finishing a hard task",
    # Requests
    "asking for help with something",
    "asking someone to visit",
    "asking to borrow something",
    "asking for a recipe",
    "asking for advice about a problem",
    "asking someone to write back",
    # Feelings
    "saying you miss someone",
    "saying thank you for a gift",
    "saying sorry for something",
    "sharing good news",
    "sharing sad news",
    "telling someone you are proud of them",
    "telling someone you think about them",
    "saying goodbye before a long trip",
    # Events and invitations
    "inviting someone to a party",
    "inviting someone to visit your town",
    "inviting someone to help with a project",
    "telling about a wedding",
    "telling about a concert or show",
    # Advice
    "giving advice about a problem",
    "giving advice about being sad",
    "warning someone about bad weather",
    "suggesting a book or game",
    "telling someone how to take care of a plant",
    # Pen pal / Distance
    "introducing yourself to a pen pal",
    "telling a pen pal about your town",
    "telling a pen pal about your family",
    "telling a pen pal about your favorite things",
    "describing your daily routine to someone far away",
    "telling someone far away about the seasons where you live",
    # Memories
    "remembering a fun time together",
    "talking about when you were young",
    "sharing a memory of someone who is gone",
    "remembering a trip you took together",
    # Updates
    "telling about how the garden is doing",
    "telling about how the kids are doing",
    "telling about how work is going",
    "telling about what the weather has been like",
    "telling about a book you just read",
    "telling about a meal you cooked",
    "telling about fixing something at home",
    "telling about a walk you took",
    # Apologies and conflicts
    "writing to make up after a fight",
    "explaining why you have not written in a long time",
    "saying sorry for missing a birthday",
    "asking for forgiveness",
    # Gratitude
    "thanking someone for their help",
    "thanking someone for being a good friend",
    "thanking a teacher",
    "thanking a neighbor for their kindness",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if t.startswith("telling about"):
        TOPIC_CATEGORIES[t] = "news"
    elif t.startswith("asking"):
        TOPIC_CATEGORIES[t] = "request"
    elif t.startswith("saying") or "miss" in t or "proud" in t or "think about" in t:
        TOPIC_CATEGORIES[t] = "feelings"
    elif t.startswith("inviting") or "wedding" in t or "concert" in t:
        TOPIC_CATEGORIES[t] = "events"
    elif t.startswith("giving advice") or t.startswith("warning") or t.startswith("suggesting"):
        TOPIC_CATEGORIES[t] = "advice"
    elif "pen pal" in t or "far away" in t or "routine" in t:
        TOPIC_CATEGORIES[t] = "pen pal"
    elif "remember" in t or "memory" in t or "when you were" in t:
        TOPIC_CATEGORIES[t] = "memories"
    elif "thank" in t:
        TOPIC_CATEGORIES[t] = "gratitude"
    elif "sorry" in t or "fight" in t or "forgive" in t or "not written" in t or "missing" in t:
        TOPIC_CATEGORIES[t] = "apology"
    else:
        TOPIC_CATEGORIES[t] = "general"


def get_extra_params(k, rng=None):
    rng = rng or _random
    names = rng.sample(ALLOWED_NAMES, 2)
    return {
        "sender_name": names[0],
        "recipient_name": names[1],
        "relationship": RELATIONSHIPS[k % len(RELATIONSHIPS)],
    }


def create_prompt(params):
    sender = params.get("sender_name", "Mia")
    recipient = params.get("recipient_name", "Leo")
    relationship = params.get("relationship", "friend")

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    ending_instruction = ""
    ending = params.get("story_ending", "")
    if ending == "sad":
        ending_instruction = "\n- The letter should have a sad or difficult tone, without forcing a happy ending"
    elif ending == "neutral":
        ending_instruction = "\n- The letter should feel ordinary and matter-of-fact"

    user_prompt = (
        f"Write a simple letter from {sender} to {recipient}. "
        f"They are {relationship}s. "
        f"The letter is about {params['topic']}. "
        f"The letter must mention {params['subject']}. "
        f"The letter should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Start with 'Dear {recipient},'\n"
        f"- End with a sign-off like 'Your {relationship}, {sender}' or 'Love, {sender}'\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- Start the first sentence after the greeting with {params['initial_word_type']} "
        f"that begins with the letter {params['initial_letter']}"
        f"{grammar_instruction}"
        f"{ending_instruction}\n\n"
        f"Write the letter now:"
    )

    return SYSTEM_PROMPT, user_prompt


def validate(text):
    errors = []
    metrics = base_validate(text)

    text_lower = text.lower()
    if not text_lower.startswith("dear "):
        errors.append("missing_greeting")

    has_signoff = bool(re.search(
        r"(your friend|love|sincerely|with love|your pal|yours truly|your neighbor|"
        r"your pen pal|take care|warmly|best wishes|from),?\s*\n?\s*[A-Z]",
        text, re.IGNORECASE,
    ))
    if not has_signoff:
        errors.append("missing_signoff")

    if metrics["character_count"] < 100:
        errors.append("too_short")

    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    idx = text.lower().find("dear ")
    if idx > 0:
        text = text[idx:]
    return text.strip()
