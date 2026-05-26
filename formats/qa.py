import re
import random as _random
from formats.shared import ALLOWED_NAMES, OUTPUT_CONSTRAINT, normalize_quotes, base_validate

FORMAT_NAME = "qa"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person asks questions and another "
    "person answers them. Mark each person's speech with <person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep answers short and clear. No fancy words, no complex ideas. "
    "Sometimes the answerer is not sure and asks a question back before answering. "
    "Sometimes the answerer does not know and says so honestly."
)

TOPICS = [
    # Science and nature
    "why the sky is blue",
    "how birds fly",
    "why leaves change color",
    "where rain comes from",
    "how fish breathe under water",
    "why the moon changes shape",
    "what makes a rainbow",
    "why the wind blows",
    "how seeds grow into plants",
    "why ice melts",
    "what makes thunder",
    "how bees make honey",
    "why the sun is hot",
    "what stars are made of",
    "why some animals sleep all winter",
    "how spiders make webs",
    "why the ocean is salty",
    "what makes a volcano erupt",
    "why do flowers smell nice",
    "how clouds form",
    # Animals
    "what the biggest animal in the world is",
    "how many legs a spider has",
    "what animals eat grass",
    "why dogs wag their tails",
    "how fast a horse can run",
    "what a baby frog is called",
    "why cats purr",
    "how long elephants live",
    "what animals come out at night",
    "why birds sing in the morning",
    "what the smallest bird is",
    "how turtles carry their homes",
    "why some animals have stripes",
    "what animals live in the desert",
    "how ants find their way home",
    # Body and health
    "why we need to sleep",
    "what happens when you sneeze",
    "why we get hungry",
    "how bones help us move",
    "why we have two eyes",
    "what makes us feel cold",
    "why cuts bleed",
    "how the heart works",
    "why we dream",
    "what happens when we yawn",
    "why we feel thirsty",
    "how muscles get stronger",
    # Food
    "where bread comes from",
    "what is inside an egg",
    "why fruit is sweet",
    "how cheese is made",
    "where rice grows",
    "why we cook food",
    "what makes popcorn pop",
    "how sugar is made",
    "why some foods are spicy",
    "where chocolate comes from",
    # Geography and world
    "what the ocean looks like at the bottom",
    "why some places are hot and some are cold",
    "what a desert looks like",
    "how mountains are made",
    "why rivers flow to the ocean",
    "what an island is",
    "where snow comes from",
    "how deep the ocean is",
    "what a jungle looks like",
    "why some places have earthquakes",
    # Daily life
    "how a clock tells time",
    "why we use money",
    "how letters get from one place to another",
    "what a map is for",
    "how a phone sends your voice far away",
    "why we go to school",
    "what a hospital is for",
    "how a bridge holds up",
    "why we need rules",
    "how a lock and key work",
    # Math and numbers
    "what zero means",
    "why we count",
    "how to tell if a number is big or small",
    "what half of something means",
    "why we measure things",
    "what a pattern is",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["sky", "rain", "leaf", "moon", "rainbow", "wind", "seed",
                             "ice", "thunder", "sun", "star", "volcano", "flower",
                             "cloud", "ocean is salty"]):
        TOPIC_CATEGORIES[t] = "science"
    elif any(w in t for w in ["animal", "spider", "dog", "horse", "frog", "cat",
                               "elephant", "bird", "turtle", "ant", "bee", "fish",
                               "stripe"]):
        TOPIC_CATEGORIES[t] = "animals"
    elif any(w in t for w in ["sleep", "sneeze", "hungry", "bone", "eye", "cold",
                               "bleed", "heart", "dream", "yawn", "thirsty", "muscle"]):
        TOPIC_CATEGORIES[t] = "body"
    elif any(w in t for w in ["bread", "egg", "fruit", "cheese", "rice", "cook",
                               "popcorn", "sugar", "spicy", "chocolate"]):
        TOPIC_CATEGORIES[t] = "food"
    elif any(w in t for w in ["ocean", "desert", "mountain", "river", "island",
                               "snow", "jungle", "earthquake", "hot and"]):
        TOPIC_CATEGORIES[t] = "geography"
    elif any(w in t for w in ["clock", "money", "letter", "map", "phone", "school",
                               "hospital", "bridge", "rule", "lock"]):
        TOPIC_CATEGORIES[t] = "daily life"
    elif any(w in t for w in ["zero", "count", "number", "half", "measure", "pattern"]):
        TOPIC_CATEGORIES[t] = "math"
    else:
        TOPIC_CATEGORIES[t] = "general"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "include_dont_know": k % 5 == 0,
        "include_clarification": k % 4 == 0,
    }


def create_prompt(params):
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

    starter_letter_instruction = ""
    if params.get("initial_letter"):
        starter_letter_instruction = (
            f"\n- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
        )

    dont_know_instruction = ""
    if params.get("include_dont_know"):
        dont_know_instruction = (
            f"\n- At some point, Person {other} should not know the answer to a question "
            f"and should say something like 'I do not know' or 'I am not sure about that'"
        )

    clarification_instruction = ""
    if params.get("include_clarification"):
        clarification_instruction = (
            f"\n- At some point, Person {other} should ask a clarifying question before answering, "
            f"like 'Do you mean...' or 'Are you asking about...'"
        )

    user_prompt = (
        f"Write a conversation where Person {starter} asks questions about "
        f"{params['topic']}. Person {other} answers the questions. "
        f"The conversation must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} asks at least 3 different questions\n"
        f"- Person {other} gives clear, simple answers\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names, pick from: {names_str}"
        f"{starter_letter_instruction}"
        f"{grammar_instruction}"
        f"{intro_instruction}"
        f"{dont_know_instruction}"
        f"{clarification_instruction}"
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
