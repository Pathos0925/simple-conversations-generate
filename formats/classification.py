import re
import random as _random
from formats.shared import ALLOWED_NAMES, OUTPUT_CONSTRAINT, normalize_quotes, base_validate

FORMAT_NAME = "classification"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person gives a list of things and the "
    "other person sorts them into groups. Mark each person's speech with <person1> "
    "and <person2> tags. Use only very simple, common words that a young child would "
    "understand. Keep sentences short. No fancy words, no complex ideas. "
    "The sorter should explain why each thing goes in its group."
)

TOPICS = [
    # Animals
    "sorting animals by where they live",
    "sorting animals by what they eat",
    "sorting animals by how they move",
    "sorting animals by size",
    "grouping animals into pets and wild animals",
    "sorting animals by how many legs they have",
    "grouping animals that swim, fly, or walk",
    "sorting baby animals and adult animals",
    # Food
    "sorting foods by color",
    "sorting foods into fruits and vegetables",
    "grouping foods by meal: breakfast, lunch, or dinner",
    "sorting foods into hot and cold",
    "grouping foods that are sweet, salty, or sour",
    "sorting foods by where they come from: farm, ocean, or garden",
    "grouping foods you cook and foods you eat raw",
    "sorting drinks and solid foods",
    # Objects
    "sorting tools by what they do",
    "grouping things by what they are made of",
    "sorting objects by shape",
    "grouping things that are heavy and things that are light",
    "sorting things you find inside and things you find outside",
    "grouping things that use electricity and things that do not",
    "sorting toys by type",
    "grouping things by color",
    # Clothes
    "sorting clothes by season",
    "grouping clothes by where you wear them on your body",
    "sorting clothes into formal and casual",
    "grouping things you wear when it rains",
    "sorting shoes, hats, and shirts",
    # Nature
    "sorting plants by where they grow",
    "grouping things into living and not living",
    "sorting rocks by size and color",
    "grouping weather types: hot, cold, wet, dry",
    "sorting flowers by color",
    "grouping things that grow and things that do not",
    # People and jobs
    "sorting jobs by where people work",
    "grouping jobs into indoor and outdoor",
    "sorting helpers in a town: doctor, teacher, farmer, builder",
    "grouping jobs by what tools they use",
    # Language
    "sorting words into nouns and verbs",
    "grouping words by their first letter",
    "sorting words into long and short",
    "grouping words that rhyme",
    "sorting words into happy words and sad words",
    "grouping words by how many syllables they have",
    # Vehicles
    "sorting vehicles by where they go: land, water, or air",
    "grouping vehicles by how many wheels they have",
    "sorting vehicles into fast and slow",
    "grouping vehicles that carry people and vehicles that carry things",
    # Time and activities
    "sorting activities by time of day: morning, afternoon, or night",
    "grouping activities into work and play",
    "sorting activities by season",
    "grouping things you do alone and things you do with others",
    # Sounds and senses
    "sorting sounds into loud and quiet",
    "grouping things by how they feel: soft, hard, smooth, rough",
    "sorting things by how they smell: nice, bad, or no smell",
    "grouping things by taste",
    # Mixed
    "sorting a mixed list of animals, foods, and objects",
    "grouping things that belong in a kitchen, a garden, or a bedroom",
    "sorting things that are round, flat, or long",
    "grouping things a child uses at school",
    "sorting things you can carry and things you cannot",
    "grouping things that float and things that sink",
    "sorting things that make noise and things that are quiet",
    "grouping things by how old they are: new or old",
    "sorting things a farmer needs",
    "grouping things you need for a picnic",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if "animal" in t or "pet" in t or "legs" in t or "baby animal" in t:
        TOPIC_CATEGORIES[t] = "animals"
    elif "food" in t or "fruit" in t or "vegetable" in t or "meal" in t or "drink" in t or "eat" in t or "cook" in t:
        TOPIC_CATEGORIES[t] = "food"
    elif "tool" in t or "object" in t or "shape" in t or "heavy" in t or "electricity" in t or "toy" in t or "made of" in t:
        TOPIC_CATEGORIES[t] = "objects"
    elif "cloth" in t or "shoe" in t or "hat" in t or "shirt" in t or "wear" in t or "rain" in t.lower() and "season" not in t:
        TOPIC_CATEGORIES[t] = "clothes"
    elif "plant" in t or "living" in t or "rock" in t or "weather" in t or "flower" in t or "grow" in t:
        TOPIC_CATEGORIES[t] = "nature"
    elif "job" in t or "helper" in t or "work" in t.split():
        TOPIC_CATEGORIES[t] = "jobs"
    elif "word" in t or "noun" in t or "verb" in t or "letter" in t or "rhyme" in t or "syllable" in t:
        TOPIC_CATEGORIES[t] = "language"
    elif "vehicle" in t or "wheel" in t:
        TOPIC_CATEGORIES[t] = "vehicles"
    elif "time" in t or "activit" in t or "season" in t or "morning" in t:
        TOPIC_CATEGORIES[t] = "activities"
    elif "sound" in t or "feel" in t or "smell" in t or "taste" in t:
        TOPIC_CATEGORIES[t] = "senses"
    else:
        TOPIC_CATEGORIES[t] = "mixed"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "num_items": 5 + (k % 6),
        "num_groups": 2 + (k % 3),
    }


def create_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))
    num_items = params.get("num_items", 6)
    num_groups = params.get("num_groups", 3)

    starter = params.get("starter", 1)
    other = 2 if starter == 1 else 1

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    intro_instruction = ""
    if params.get("introduce_names"):
        intro_instruction = (
            "\n- Both people should introduce themselves by name at the start"
        )

    starter_letter_instruction = ""
    if params.get("initial_letter"):
        starter_letter_instruction = (
            f"\n- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
        )

    user_prompt = (
        f"Write a conversation about {params['topic']}. "
        f"Person {starter} gives a list of about {num_items} items. "
        f"Person {other} sorts them into {num_groups} groups and explains why each item "
        f"belongs in its group. The conversation must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} gives the list of items to sort\n"
        f"- Person {other} sorts them into {num_groups} groups\n"
        f"- Person {other} explains why each item goes in its group\n"
        f"- Person {starter} can ask questions or suggest changes\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names, pick from: {names_str}"
        f"{starter_letter_instruction}"
        f"{grammar_instruction}"
        f"{intro_instruction}"
        f"{OUTPUT_CONSTRAINT}\n\n"
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
