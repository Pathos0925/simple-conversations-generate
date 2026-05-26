import re
import random as _random
from formats.shared import ALLOWED_NAMES, OUTPUT_CONSTRAINT, normalize_quotes, base_validate

FORMAT_NAME = "planning"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person asks for help making a plan and "
    "the other person creates a plan with steps, rough times, and a backup option. "
    "Mark each person's speech with <person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas."
)

TOPICS = [
    # Events and parties
    "planning a birthday party",
    "planning a picnic in the park",
    "planning a small wedding",
    "planning a surprise for a friend",
    "planning a holiday dinner",
    "planning a school play",
    "planning a going-away party",
    "planning a neighborhood cleanup day",
    # Trips and travel
    "planning a trip to the lake",
    "planning a day at the beach",
    "planning a camping trip",
    "planning a visit to a relative far away",
    "planning a road trip with stops",
    "planning a hike up a mountain",
    "planning a boat trip on the river",
    "planning a trip to the city",
    # Home and projects
    "planning what to cook for dinner this week",
    "planning a garden for the spring",
    "planning a move to a new house",
    "planning how to fix a broken room",
    "planning how to build a shed",
    "planning how to paint the house",
    "planning how to organize a messy room",
    "planning how to rearrange the furniture",
    # School and learning
    "planning a school project",
    "planning a study schedule for a test",
    "planning a class trip",
    "planning what to learn this month",
    "planning a book report",
    "planning how to teach someone a skill",
    # Work and tasks
    "planning a busy day at work",
    "planning how to finish a big task",
    "planning a market stall for selling things",
    "planning how to save money for something",
    "planning a daily routine",
    "planning chores for the week",
    # Animals and nature
    "planning how to take care of a new pet",
    "planning a bird-watching trip",
    "planning how to grow vegetables",
    "planning how to help a hurt animal",
    "planning how to build a birdhouse",
    "planning what to plant in each season",
    # Social and community
    "planning a meeting with neighbors",
    "planning a gift for someone special",
    "planning how to help someone who is sick",
    "planning a day of fun for the children",
    "planning how to welcome a new neighbor",
    "planning how to raise money for a cause",
    # Practical and survival
    "planning what to pack for a long trip",
    "planning what to do in a power outage",
    "planning how to get ready for a big storm",
    "planning how to stay cool on a very hot day",
    "planning how to keep warm in winter",
    "planning what to do if you get lost",
    # Creative
    "planning how to write a short story",
    "planning how to make a costume",
    "planning how to put on a puppet show",
    "planning how to decorate a room",
    "planning how to make a photo album",
    "planning how to build something from old materials",
    # Morning to night
    "planning the perfect morning routine",
    "planning a full day off",
    "planning an evening with the family",
    "planning what to do on a rainy weekend",
    "planning a bedtime routine for a child",
    "planning a lazy Sunday",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["party", "picnic", "wedding", "surprise", "dinner",
                             "play", "going-away", "cleanup"]):
        TOPIC_CATEGORIES[t] = "events"
    elif any(w in t for w in ["trip", "beach", "camping", "visit", "road",
                               "hike", "boat", "city", "lake"]):
        TOPIC_CATEGORIES[t] = "travel"
    elif any(w in t for w in ["cook", "garden", "move", "fix", "build a shed",
                               "paint", "organize", "rearrange", "furniture"]):
        TOPIC_CATEGORIES[t] = "home"
    elif any(w in t for w in ["school", "study", "class trip", "learn", "book report", "teach"]):
        TOPIC_CATEGORIES[t] = "school"
    elif any(w in t for w in ["work", "task", "market", "save money", "routine", "chore"]):
        TOPIC_CATEGORIES[t] = "work"
    elif any(w in t for w in ["pet", "bird", "vegetable", "animal", "birdhouse", "plant"]):
        TOPIC_CATEGORIES[t] = "nature"
    elif any(w in t for w in ["neighbor", "gift", "sick", "children", "welcome", "raise money"]):
        TOPIC_CATEGORIES[t] = "community"
    elif any(w in t for w in ["pack", "power", "storm", "cool", "warm", "lost"]):
        TOPIC_CATEGORIES[t] = "practical"
    elif any(w in t for w in ["story", "costume", "puppet", "decorate", "album", "old materials"]):
        TOPIC_CATEGORIES[t] = "creative"
    else:
        TOPIC_CATEGORIES[t] = "daily"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "num_steps": 3 + (k % 4),
    }


def create_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))
    num_steps = params.get("num_steps", 4)

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
        f"Write a conversation where Person {starter} asks Person {other} for help with "
        f"{params['topic']}. Person {other} creates a simple plan. "
        f"The conversation must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {other} should make a plan with about {num_steps} steps\n"
        f"- Each step should say what to do and roughly when or how long\n"
        f"- Include at least one backup plan in case something goes wrong\n"
        f"- Person {starter} can ask questions or suggest changes to the plan\n"
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
