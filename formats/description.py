import re
import random as _random
from formats.shared import ALLOWED_NAMES, normalize_quotes, base_validate

FORMAT_NAME = "description"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person asks about something and the "
    "other person describes and explains it. Mark each person's speech with "
    "<person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas."
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
    # Habitats and ecosystems
    "what a coral reef looks like under the water",
    "what a swamp is like",
    "what a meadow looks like in summer",
    "what a frozen lake looks like",
    "what the bottom of the ocean is like",
    "what a jungle looks like",
    "what a tundra is",
    "what an island looks like from a boat",
    # Machines and inventions
    "how a bicycle works",
    "what a windmill does",
    "how a water wheel works",
    "what a telescope does",
    "how a compass works",
    "what a lever is and how it helps",
    "how a pulley lifts heavy things",
    "what a thermometer measures",
    "how scissors cut things",
    "what a magnifying glass does",
    # Time and space
    "what a year is",
    "what an hour feels like",
    "how far away the stars are",
    "what the moon looks like up close",
    "what makes a day longer in summer",
    "what a calendar is for",
    "what an eclipse is",
    # Materials and substances
    "what wood is and where it comes from",
    "what glass is made of",
    "what metal feels like",
    "what rubber is",
    "what paper is made from",
    "what clay is and what you can do with it",
    "what cotton is",
    "what stone is like",
    # Human activities
    "what a market looks like on a busy day",
    "what a school looks like inside",
    "what a hospital is for",
    "what a library looks like",
    "what a train station looks like",
    "what a bakery smells like",
    "what a harbor looks like with all the boats",
    "what a playground looks like",
    # Sounds and senses
    "what thunder sounds like",
    "what silence feels like",
    "what the smell of rain is like",
    "what different colors feel like",
    "what a campfire sounds like at night",
    "what cold water feels like on your skin",
    "what the taste of honey is like",
    # Numbers and math concepts
    "what counting is",
    "what zero means",
    "what adding two things together means",
    "what a half of something is",
    "what a pattern is",
    "what measuring means",
    "what the biggest number you can think of is",
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
    rng = rng or _random
    return {
        "perspective": PERSPECTIVES[k % len(PERSPECTIVES)],
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
    }


def create_prompt(params):
    perspective = params.get("perspective", "matter-of-fact")
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))

    starter = params.get("starter", 1)
    other = 2 if starter == 1 else 1
    s_tag = f"<person{starter}>"
    o_tag = f"<person{other}>"

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    intro_instruction = ""
    if params.get("introduce_names"):
        intro_instruction = (
            "\n- Both people should introduce themselves by name at the start of the conversation"
        )

    user_prompt = (
        f"Write a conversation where Person {starter} asks Person {other} about "
        f"{params['topic']}. Person {other} describes and explains it in a "
        f"{perspective} way. The conversation must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {other} does most of the talking, describing and explaining\n"
        f"- Person {starter} asks questions, reacts with surprise or interest, or asks for more details\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names, pick from: {names_str}\n"
        f"- Start the conversation with {params['initial_word_type']} that begins with "
        f"the letter {params['initial_letter']}"
        f"{grammar_instruction}"
        f"{intro_instruction}\n\n"
        f"Format example:\n"
        f"{s_tag} Can you tell me about {params['topic']}? "
        f"{o_tag} Sure! Let me tell you...\n\n"
        f"Write the conversation now:"
    )

    return SYSTEM_PROMPT, user_prompt


def validate(text):
    errors = []

    p1_count = text.count("<person1>")
    p2_count = text.count("<person2>")

    if p1_count == 0:
        errors.append("missing_person1_tag")
    if p2_count == 0:
        errors.append("missing_person2_tag")
    if p1_count + p2_count < 3:
        errors.append("too_few_turns")

    metrics = base_validate(text)
    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
        "person1_turns": p1_count,
        "person2_turns": p2_count,
        "total_turns": p1_count + p2_count,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    text = re.sub(r"</person[12]>", "", text)
    first_tag = re.search(r"<person[12]>", text)
    if first_tag:
        text = text[first_tag.start():]
    return text.strip()
