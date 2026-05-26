import re
import random as _random
from formats.shared import ALLOWED_NAMES, OUTPUT_CONSTRAINT, normalize_quotes, base_validate

FORMAT_NAME = "comparison"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person asks to compare two things and "
    "the other person explains what is the same and what is different. "
    "Mark each person's speech with <person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas. "
    "Use simple pros and cons to explain each side."
)

TOPICS = [
    # Animals
    "comparing a cat and a dog",
    "comparing a fish and a bird",
    "comparing an ant and an elephant",
    "comparing a horse and a cow",
    "comparing a frog and a turtle",
    "comparing a bee and a butterfly",
    "comparing a pet and a wild animal",
    "comparing a chicken and a duck",
    # Seasons and weather
    "comparing summer and winter",
    "comparing spring and autumn",
    "comparing a sunny day and a rainy day",
    "comparing a hot day and a cold day",
    "comparing snow and rain",
    "comparing day and night",
    # Food
    "comparing an apple and a banana",
    "comparing bread and rice",
    "comparing milk and juice",
    "comparing a cooked meal and a raw meal",
    "comparing sweet food and salty food",
    "comparing soup and salad",
    "comparing cake and fruit",
    "comparing water and tea",
    # Objects and tools
    "comparing a book and a movie",
    "comparing a candle and a lamp",
    "comparing a hammer and a screwdriver",
    "comparing a cup and a bowl",
    "comparing a pen and a pencil",
    "comparing a clock and a sundial",
    "comparing a knife and scissors",
    # Places
    "comparing a city and a village",
    "comparing a mountain and a valley",
    "comparing a forest and a desert",
    "comparing a lake and a river",
    "comparing a house and a tent",
    "comparing a farm and a factory",
    "comparing the beach and the woods",
    "comparing a school and a library",
    # Transportation
    "comparing a bike and a car",
    "comparing a boat and an airplane",
    "comparing walking and running",
    "comparing a bus and a train",
    "comparing riding a horse and driving a car",
    # Materials
    "comparing wood and stone",
    "comparing glass and metal",
    "comparing paper and cloth",
    "comparing sand and dirt",
    "comparing wool and cotton",
    # Activities
    "comparing reading and drawing",
    "comparing playing inside and playing outside",
    "comparing working alone and working in a team",
    "comparing cooking and cleaning",
    "comparing swimming and running",
    "comparing singing and dancing",
    "comparing building with blocks and drawing a picture",
    # People and roles
    "comparing a teacher and a student",
    "comparing a child and an adult",
    "comparing a farmer and a baker",
    "comparing a doctor and a builder",
    "comparing being a leader and being a helper",
    # Time
    "comparing morning and evening",
    "comparing a weekday and a weekend",
    "comparing being early and being late",
    "comparing doing things fast and doing things slow",
    # Abstract
    "comparing being brave and being careful",
    "comparing being alone and being with friends",
    "comparing giving and receiving",
    "comparing making something and buying something",
    "comparing old things and new things",
    "comparing a plan and a surprise",
    "comparing learning from a book and learning by doing",
    "comparing remembering and forgetting",
    "comparing telling the truth and telling a lie",
    "comparing helping and watching",
    "comparing saving and spending",
    "comparing being patient and being in a hurry",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["cat", "dog", "fish", "bird", "ant", "elephant", "horse",
                             "cow", "frog", "turtle", "bee", "butterfly", "pet", "chicken", "duck"]):
        TOPIC_CATEGORIES[t] = "animals"
    elif any(w in t for w in ["summer", "winter", "spring", "autumn", "sunny", "rainy",
                               "hot", "cold", "snow", "rain", "day and night"]):
        TOPIC_CATEGORIES[t] = "seasons"
    elif any(w in t for w in ["apple", "banana", "bread", "rice", "milk", "juice",
                               "cooked", "sweet", "salty", "soup", "salad", "cake",
                               "fruit", "water", "tea"]):
        TOPIC_CATEGORIES[t] = "food"
    elif any(w in t for w in ["book", "candle", "lamp", "hammer", "cup", "bowl",
                               "pen", "pencil", "clock", "knife", "scissors"]):
        TOPIC_CATEGORIES[t] = "objects"
    elif any(w in t for w in ["city", "village", "mountain", "valley", "forest",
                               "desert", "lake", "river", "house", "tent", "farm",
                               "factory", "beach", "school", "library"]):
        TOPIC_CATEGORIES[t] = "places"
    elif any(w in t for w in ["bike", "car", "boat", "airplane", "walking", "running",
                               "bus", "train", "horse"]):
        TOPIC_CATEGORIES[t] = "transportation"
    elif any(w in t for w in ["wood", "stone", "glass", "metal", "paper", "cloth",
                               "sand", "dirt", "wool", "cotton"]):
        TOPIC_CATEGORIES[t] = "materials"
    elif any(w in t for w in ["reading", "drawing", "playing", "working", "cooking",
                               "cleaning", "swimming", "singing", "dancing", "building"]):
        TOPIC_CATEGORIES[t] = "activities"
    elif any(w in t for w in ["teacher", "student", "child", "adult", "farmer",
                               "baker", "doctor", "builder", "leader", "helper"]):
        TOPIC_CATEGORIES[t] = "people"
    elif any(w in t for w in ["morning", "evening", "weekday", "weekend", "early", "late", "fast", "slow"]):
        TOPIC_CATEGORIES[t] = "time"
    else:
        TOPIC_CATEGORIES[t] = "abstract"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
    }


def create_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))

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
        f"Write a conversation where Person {starter} asks Person {other} about "
        f"{params['topic']}. Person {other} explains what is the same and what is "
        f"different, using simple pros and cons. "
        f"The conversation must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {other} should explain at least 2 ways they are the same\n"
        f"- Person {other} should explain at least 2 ways they are different\n"
        f"- Person {other} should mention at least one good thing and one bad thing about each\n"
        f"- Person {starter} can ask follow-up questions\n"
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
