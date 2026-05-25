from formats.shared import normalize_quotes, base_validate

FORMAT_NAME = "description"

SYSTEM_PROMPT = (
    "You write simple descriptions of things, places, and ideas using only very basic words. "
    "Describe what something looks like, how it works, or what it does. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas. "
    "Do not write a story or a conversation. Just describe."
)

PERSPECTIVES = [
    "scientific", "poetic", "matter-of-fact", "curious", "detailed",
]

TOPICS = [
    # Animals
    "what a cat is like",
    "what a dog is like",
    "what an elephant looks like",
    "what a whale is",
    "how a butterfly lives",
    "what a spider does",
    "how an eagle flies",
    "what a frog does all day",
    "what a bear does in winter",
    "how a bee makes honey",
    "what a fish looks like under water",
    "what an owl does at night",
    "how a horse runs",
    "what a rabbit looks like",
    "how ants work together",
    # Places
    "what a forest looks like",
    "what a desert is",
    "what a mountain looks like",
    "what the ocean is like",
    "what a river looks like",
    "what a farm is",
    "what a village is like",
    "what a city looks like",
    "what a cave is like inside",
    "what a garden looks like",
    "what a pond looks like",
    "what a beach is like",
    # Weather and sky
    "what a thunderstorm is like",
    "what a rainbow looks like",
    "what snowfall looks like",
    "what fog is",
    "what a windy day feels like",
    "what a sunny morning is like",
    "what clouds look like",
    "what a rainy day is like",
    # Objects
    "what a clock does",
    "what a bridge is for",
    "what a candle is",
    "what a mirror does",
    "what a wheel is for",
    "what a bell sounds like",
    "what a ship looks like",
    "what a tent is",
    "what a lamp does",
    "what a ladder is for",
    # Concepts
    "what the seasons are",
    "what day and night are",
    "how rain forms",
    "what shadows are",
    "how fire works",
    "what makes things cold",
    "why the sky changes color",
    "what gravity does",
    "what the wind is",
    "how ice turns to water",
    # Food and nature
    "what an apple tree looks like",
    "what bread is made of",
    "what honey is",
    "what salt is",
    "what a sunflower looks like",
    "what a mushroom is",
    "what a pine tree looks like",
    "what a pumpkin is",
    # Body and senses
    "what the human hand can do",
    "how eyes work",
    "why we need sleep",
    "what bones do",
    "how ears hear sound",
    "what skin does",
    "how the nose smells things",
    # Language and grammar
    "what a noun is",
    "what a verb is",
    "what an adjective is",
    "what an adverb is",
    "what a preposition is",
    "what a pronoun is",
    "what a sentence is",
    "what a question is",
    "what past tense means",
    "what future tense means",
    "what a plural is",
    "what a vowel and a consonant are",
    "what a syllable is",
    "what rhyming words are",
    "what the subject of a sentence is",
    "what a comma is for",
    "what a period does in a sentence",
    "what an exclamation mark means",
    "what a conjunction is",
    "what the difference between a noun and a verb is",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(l in t for l in ["noun", "verb", "adjective", "adverb", "preposition",
                               "pronoun", "sentence", "question", "tense", "plural",
                               "vowel", "consonant", "syllable", "rhym", "subject of",
                               "comma", "period", "exclamation", "conjunction"]):
        TOPIC_CATEGORIES[t] = "language"
    elif any(a in t for a in ["cat", "dog", "elephant", "whale", "butterfly", "spider",
                             "eagle", "frog", "bear", "bee", "fish", "owl", "horse",
                             "rabbit", "ant"]):
        TOPIC_CATEGORIES[t] = "animals"
    elif any(p in t for p in ["forest", "desert", "mountain", "ocean", "river", "farm",
                               "village", "city", "cave", "garden", "pond", "beach"]):
        TOPIC_CATEGORIES[t] = "places"
    elif any(w in t for w in ["storm", "rainbow", "snow", "fog", "wind", "sun",
                               "cloud", "rain"]):
        TOPIC_CATEGORIES[t] = "weather"
    elif any(o in t for o in ["clock", "bridge", "candle", "mirror", "wheel", "bell",
                               "ship", "tent", "lamp", "ladder"]):
        TOPIC_CATEGORIES[t] = "objects"
    elif any(c in t for c in ["season", "day and night", "rain forms", "shadow",
                               "fire", "cold", "sky changes", "gravity", "wind is",
                               "ice turns"]):
        TOPIC_CATEGORIES[t] = "concepts"
    elif any(f in t for f in ["apple", "bread", "honey", "salt", "sunflower",
                               "mushroom", "pine", "pumpkin"]):
        TOPIC_CATEGORIES[t] = "nature"
    elif any(b in t for b in ["hand", "eyes", "sleep", "bones", "ears", "skin", "nose"]):
        TOPIC_CATEGORIES[t] = "body"
    else:
        TOPIC_CATEGORIES[t] = "general"


def get_extra_params(k, rng=None):
    return {
        "perspective": PERSPECTIVES[k % len(PERSPECTIVES)],
    }


def create_prompt(params):
    perspective = params.get("perspective", "matter-of-fact")

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    user_prompt = (
        f"Write a simple description about {params['topic']}. "
        f"The description must mention {params['subject']}. "
        f"Write it in a {perspective} way. "
        f"The text should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Just describe. Do not write a story or a conversation\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- Start the description with {params['initial_word_type']} that begins with "
        f"the letter {params['initial_letter']}"
        f"{grammar_instruction}\n\n"
        f"Write the description now:"
    )

    return SYSTEM_PROMPT, user_prompt


def validate(text):
    errors = []
    metrics = base_validate(text)

    if metrics["character_count"] < 100:
        errors.append("too_short")
    if "<person1>" in text or "<person2>" in text:
        errors.append("contains_conversation_tags")

    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    return text.strip()
