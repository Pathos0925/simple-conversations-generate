import re
from formats.shared import normalize_quotes, base_validate

FORMAT_NAME = "diary"

SYSTEM_PROMPT = (
    "You write simple diary entries using only very basic words. "
    "Write in first person ('I') and mostly past tense ('Today I went...'). "
    "The entry should feel like a real person writing about their day. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas."
)

MOODS = [
    "happy", "sad", "thoughtful", "excited", "worried",
    "tired", "grateful", "angry", "calm", "confused",
    "proud", "lonely",
]

TOPICS = [
    # Daily events
    "a day at school",
    "a trip to the market",
    "cooking dinner for the family",
    "a walk in the park",
    "cleaning the house",
    "a busy morning",
    "a lazy afternoon",
    "a ride on a bus",
    "a visit to the doctor",
    "going to the library",
    "eating at a new place",
    "running errands all day",
    "staying home on a rainy day",
    # Social
    "meeting a new friend",
    "a fight with a friend",
    "a family dinner",
    "playing with friends outside",
    "saying goodbye to someone",
    "a visit from a relative",
    "helping a neighbor",
    "talking to a stranger",
    "a party with friends",
    "spending time alone",
    "working on a project with someone",
    # Adventures
    "getting lost in a new place",
    "finding something special on the ground",
    "a long walk to somewhere new",
    "exploring a part of town I never saw",
    "climbing a hill for the first time",
    "swimming in a lake",
    "riding a bike far from home",
    "seeing a wild animal up close",
    "going fishing for the first time",
    "picking fruit from a tree",
    # Feelings
    "a day when I felt lonely",
    "a day when everything went right",
    "a day when I felt really scared",
    "being proud of something I did",
    "feeling nervous about tomorrow",
    "missing someone who is far away",
    "feeling angry and not knowing why",
    "a day when I could not stop laughing",
    "feeling grateful for what I have",
    "worrying about something that might happen",
    # Nature
    "a beautiful sunset I saw",
    "the first snow of the year",
    "watching birds outside my window",
    "a windy afternoon",
    "a big storm that came at night",
    "planting something in the garden",
    "finding a flower growing in a crack",
    "sitting by a river and thinking",
    # Milestones
    "my first day at a new school",
    "learning to ride a bike",
    "growing something in my garden for the first time",
    "finishing a hard task I started long ago",
    "the day I learned to cook something",
    "reading a whole book by myself",
    "teaching someone something I know",
    "the day I got my own room",
    # Problems
    "something important that broke",
    "losing something I care about",
    "making a big mistake",
    "a hard day at work",
    "a plan that did not work out",
    "spilling something and making a mess",
    "forgetting something important",
    "getting in trouble for something I did",
    # Animals
    "finding a lost animal",
    "taking care of a sick pet",
    "seeing an animal I never saw before",
    "feeding the birds in the yard",
    "the day we got a new pet",
    "saying goodbye to a pet",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["school", "market", "dinner", "walk", "clean", "morning",
                             "afternoon", "bus", "doctor", "library", "eating",
                             "errands", "staying home", "rainy day"]):
        TOPIC_CATEGORIES[t] = "daily"
    elif any(w in t for w in ["friend", "family", "goodbye", "relative", "neighbor",
                               "stranger", "party", "alone", "project with"]):
        TOPIC_CATEGORIES[t] = "social"
    elif any(w in t for w in ["lost", "finding", "walk to", "exploring", "climbing",
                               "swimming", "riding", "fishing", "picking"]):
        TOPIC_CATEGORIES[t] = "adventure"
    elif any(w in t for w in ["felt", "proud", "nervous", "missing", "angry",
                               "laughing", "grateful", "worrying", "scared",
                               "everything went"]):
        TOPIC_CATEGORIES[t] = "feelings"
    elif any(w in t for w in ["sunset", "snow", "birds", "wind", "storm",
                               "planting", "flower", "river"]):
        TOPIC_CATEGORIES[t] = "nature"
    elif any(w in t for w in ["first day", "learning", "growing", "finishing",
                               "learned", "reading", "teaching", "got my own"]):
        TOPIC_CATEGORIES[t] = "milestones"
    elif any(w in t for w in ["broke", "losing", "mistake", "hard day",
                               "did not work", "spilling", "forgetting", "trouble"]):
        TOPIC_CATEGORIES[t] = "problems"
    elif any(w in t for w in ["animal", "pet", "birds in the yard"]):
        TOPIC_CATEGORIES[t] = "animals"
    else:
        TOPIC_CATEGORIES[t] = "general"


def get_extra_params(k, rng=None):
    return {
        "mood": MOODS[k % len(MOODS)],
    }


def create_prompt(params):
    mood = params.get("mood", "thoughtful")

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    ending_instruction = ""
    ending = params.get("story_ending", "")
    if ending == "sad":
        ending_instruction = "\n- The entry should end on a sad or difficult note"
    elif ending == "neutral":
        ending_instruction = "\n- The entry should end in a matter-of-fact way, not everything needs to be resolved"

    user_prompt = (
        f"Write a simple diary entry about {params['topic']}. "
        f"The entry must mention {params['subject']}. "
        f"The writer is feeling {mood}. "
        f"The entry should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Write in first person ('I')\n"
        f"- Use mostly past tense ('I went', 'I saw', 'I felt')\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- Start the entry with {params['initial_word_type']} that begins with "
        f"the letter {params['initial_letter']}"
        f"{grammar_instruction}"
        f"{ending_instruction}\n\n"
        f"Write the diary entry now:"
    )

    return SYSTEM_PROMPT, user_prompt


def validate(text):
    errors = []
    metrics = base_validate(text)

    i_count = len(re.findall(r"\bI\b", text))
    if i_count < 3:
        errors.append("too_few_first_person_markers")
    if metrics["character_count"] < 100:
        errors.append("too_short")

    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
        "first_person_count": i_count,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    text = re.sub(r"^(Dear Diary[,:]?\s*\n?)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^#*\s*My Diary\s*\n?", "", text, flags=re.IGNORECASE)
    return text.strip()
