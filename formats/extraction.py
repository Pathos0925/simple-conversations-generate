import re
import random as _random
from formats.shared import ALLOWED_NAMES, OUTPUT_CONSTRAINT, normalize_quotes, base_validate

FORMAT_NAME = "extraction"

NAMES_PER_CONVERSATION = 4

EXTRACT_TYPES = ["names", "places", "numbers", "items", "tasks", "dates", "feelings"]

SYSTEM_PROMPT = (
    "You write simple conversations where one person reads a short passage and the "
    "other person pulls out specific information from it. "
    "Mark each person's speech with <person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas. "
    "The extractor should list each piece of information they found."
)

TOPICS = [
    # Shopping and errands
    "a short note about a shopping trip",
    "a list of things someone bought at the market",
    "a note about errands to run today",
    "a message about what to buy for dinner",
    "a note about picking up things from different shops",
    "a short story about going to the store",
    "a message about what ran out at home",
    "a note about returning something to a shop",
    # Meetings and plans
    "a message about a meeting time and place",
    "a note about when and where to meet a friend",
    "a message about a doctor visit",
    "a note about a school meeting for parents",
    "a message changing the time of a plan",
    "a note about who is coming to a party and when",
    "a message about a work meeting on a certain day",
    # Family and home
    "a story about a family dinner",
    "a note about who lives in a house",
    "a story about a family trip to the park",
    "a note about what each person in the family likes",
    "a message about a family gathering",
    "a story about visiting grandparents",
    "a note about birthdays in the family",
    # Packing and travel
    "a note about what to pack for a trip",
    "a list of things needed for camping",
    "a note about what to bring to school",
    "a message about packing clothes for different weather",
    "a note about what to take on a boat ride",
    "a list of things to bring to a picnic",
    "a note about supplies for a project",
    # Letters and messages
    "a letter about a birthday",
    "a short letter from a friend in another town",
    "a thank-you note listing what was given",
    "a note from a teacher about homework",
    "a message from a neighbor about a lost pet",
    "a note left on the kitchen table",
    "a message about picking someone up at a certain time",
    # Daily events
    "a short story about what happened at school today",
    "a passage about a child's morning routine",
    "a story about a day at the beach",
    "a passage about what someone did last weekend",
    "a story about helping a neighbor",
    "a passage about a rainy day spent inside",
    "a story about a visit to a farm",
    # Recipes and instructions
    "a simple recipe with ingredients listed",
    "a note about how to take care of a plant",
    "instructions for a simple game with the rules",
    "a recipe for soup with three ingredients",
    "a note about feeding the animals and when",
    "instructions for cleaning a room step by step",
    # Nature and observations
    "a passage about animals seen on a walk",
    "a note about the weather for the past three days",
    "a passage about what grows in the garden",
    "a story about birds spotted near the house",
    "a note about the fish in the pond",
    "a passage about flowers blooming in spring",
    # Work and chores
    "a note about chores that need to be done today",
    "a message about tasks to finish before the weekend",
    "a note about who does which job at home",
    "a list of repairs that need to be made",
    "a message about what was done at work today",
    "a note about things to fix around the house",
    # Mixed information
    "a passage that mentions three people and two places",
    "a short story with dates, names, and places",
    "a passage with numbers, items, and a location",
    "a note with names, a time, and a list of things to bring",
    "a passage about a trip that mentions who went, where, and when",
    "a short message with a task, a deadline, and a person responsible",
    "a story that includes feelings, places, and times",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["shopping", "bought", "errand", "buy", "shop", "store",
                             "ran out", "returning"]):
        TOPIC_CATEGORIES[t] = "shopping"
    elif any(w in t for w in ["meeting", "meet a friend", "doctor", "school meeting",
                               "time of a plan", "party and when", "work meeting"]):
        TOPIC_CATEGORIES[t] = "meetings"
    elif any(w in t for w in ["family", "lives in", "grandparent", "birthday"]):
        TOPIC_CATEGORIES[t] = "family"
    elif any(w in t for w in ["pack", "camping", "bring to", "supplies", "boat ride",
                               "picnic"]):
        TOPIC_CATEGORIES[t] = "packing"
    elif any(w in t for w in ["letter", "thank-you", "teacher about", "neighbor about",
                               "kitchen table", "picking someone"]):
        TOPIC_CATEGORIES[t] = "messages"
    elif any(w in t for w in ["school today", "morning routine", "beach", "weekend",
                               "helping a neighbor", "rainy day", "visit to a farm"]):
        TOPIC_CATEGORIES[t] = "daily"
    elif any(w in t for w in ["recipe", "care of a plant", "instructions", "feeding",
                               "cleaning a room"]):
        TOPIC_CATEGORIES[t] = "instructions"
    elif any(w in t for w in ["animals seen", "weather", "garden", "birds", "pond",
                               "flowers"]):
        TOPIC_CATEGORIES[t] = "nature"
    elif any(w in t for w in ["chores", "tasks", "job at home", "repairs", "work today",
                               "fix around"]):
        TOPIC_CATEGORIES[t] = "work"
    else:
        TOPIC_CATEGORIES[t] = "mixed"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "extract_type": EXTRACT_TYPES[k % len(EXTRACT_TYPES)],
    }


def create_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))
    extract_type = params.get("extract_type", "names")

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
        f"Write a conversation where Person {starter} reads a short passage about "
        f"{params['topic']}. Person {other} pulls out all the {extract_type} from the "
        f"passage and lists them. The passage must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} reads a passage of at least 4 sentences\n"
        f"- Person {other} lists all the {extract_type} found in the passage\n"
        f"- Person {starter} can ask Person {other} to find other things too\n"
        f"- Person {other} should only list things that are actually in the passage\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names in the passage, pick from: {names_str}"
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
