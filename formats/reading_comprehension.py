import re
import random as _random
from formats.shared import ALLOWED_NAMES, OUTPUT_CONSTRAINT, normalize_quotes, base_validate

FORMAT_NAME = "reading_comprehension"

NAMES_PER_CONVERSATION = 4

QUESTION_TYPES = ["who", "what", "where", "when", "why", "how"]

SYSTEM_PROMPT = (
    "You write simple conversations where one person tells a short passage and the "
    "other person asks questions about it. Mark each person's speech with <person1> "
    "and <person2> tags. Use only very simple, common words that a young child would "
    "understand. Keep sentences short. No fancy words, no complex ideas. "
    "The questions should be about who, what, where, when, why, or how. "
    "Answers should come only from the passage."
)

TOPICS = [
    # Daily life passages
    "a trip to the market",
    "a day at the farm",
    "a morning at school",
    "cooking breakfast for the family",
    "cleaning the house before guests arrive",
    "a visit to the doctor",
    "walking to work on a rainy day",
    "feeding the animals on a farm",
    "a busy day at a bakery",
    "packing for a trip",
    "fixing a broken fence",
    "a family eating dinner together",
    "washing clothes by the river",
    "a child doing homework",
    "shopping for fruit at a stand",
    # People and events
    "a girl who found a bird with a broken wing",
    "a boy who helped an old woman carry bags",
    "a teacher who brought a surprise to class",
    "two children who built a fort from boxes",
    "a father who taught his son to fish",
    "a woman who sold flowers at the market",
    "a man who fixed the town clock",
    "a grandmother who told a story at bedtime",
    "a child who got lost at a fair",
    "a farmer who woke up to find his cow missing",
    "a girl who wrote a letter to her friend",
    "a boy who found a coin on the road",
    "a family that moved to a new town",
    "a child who won a race at school",
    "a baker who made too many pies",
    # Nature passages
    "a rainy afternoon at a pond",
    "a walk through the forest in autumn",
    "a bird building a nest in a tree",
    "a storm that came in the night",
    "the first snow of winter",
    "a sunny day at the beach",
    "a garden in spring with new flowers",
    "a river that flooded after the rain",
    "animals getting ready for winter",
    "a sunset over the hills",
    "a cat chasing a butterfly in the yard",
    "a frog sitting on a lily pad",
    "bees buzzing around a field of flowers",
    "a squirrel hiding nuts for winter",
    # Work and tasks
    "a builder putting up a wall",
    "a sailor on a small boat",
    "a shepherd watching sheep on a hill",
    "a potter making a bowl from clay",
    "a miller grinding wheat into flour",
    "a fisherman pulling in a net",
    "a weaver making cloth on a loom",
    "a woodcutter chopping trees",
    "a cook preparing a feast",
    "a farmer planting seeds in rows",
    # Adventures and problems
    "a dog that ran away from home",
    "a key that unlocked the wrong door",
    "a map that led to a dead end",
    "a bridge that broke while crossing",
    "a boat that got stuck on the rocks",
    "a child who climbed too high in a tree",
    "a horse that would not cross the stream",
    "a kite that flew away in the wind",
    "a well that ran dry in the summer",
    "a fire that started in the kitchen",
    # Short stories to comprehend
    "a child who shared her lunch with a stranger",
    "a man who planted a tree every year",
    "a woman who walked to town to sell eggs",
    "a boy who saved a fish from a puddle",
    "a girl who learned to swim in the lake",
    "an old man who sat in the same chair every day",
    "a cat that brought home a gift for its owner",
    "a child who tried to catch the moon in a bucket",
    "a horse that knew the way home without a rider",
    "a mother who sang the same song every night",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["market", "farm", "school", "cooking", "cleaning",
                             "doctor", "walking to work", "bakery", "packing",
                             "fence", "dinner", "washing", "homework", "shopping"]):
        TOPIC_CATEGORIES[t] = "daily life"
    elif any(w in t for w in ["girl who", "boy who", "teacher", "children who",
                               "father", "woman who", "man who", "grandmother",
                               "child who", "farmer who", "family", "baker"]):
        TOPIC_CATEGORIES[t] = "people"
    elif any(w in t for w in ["rain", "forest", "bird", "storm", "snow", "beach",
                               "garden", "river", "sunset", "cat", "frog", "bee",
                               "squirrel", "pond", "butterfly"]):
        TOPIC_CATEGORIES[t] = "nature"
    elif any(w in t for w in ["builder", "sailor", "shepherd", "potter", "miller",
                               "fisherman", "weaver", "woodcutter", "cook", "planting"]):
        TOPIC_CATEGORIES[t] = "work"
    elif any(w in t for w in ["ran away", "key", "map", "bridge", "boat", "climbed",
                               "horse that", "kite", "well", "fire"]):
        TOPIC_CATEGORIES[t] = "adventure"
    else:
        TOPIC_CATEGORIES[t] = "stories"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "question_focus": QUESTION_TYPES[k % len(QUESTION_TYPES)],
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
        f"Write a conversation where Person {starter} tells a short passage about "
        f"{params['topic']}. The passage must mention {params['subject']}. "
        f"Then Person {other} asks questions about the passage and Person {starter} "
        f"answers them using only information from the passage. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} tells a short passage first (4 to 6 sentences)\n"
        f"- Person {other} then asks at least 3 questions about the passage\n"
        f"- Focus on {params.get('question_focus', 'what')} questions but mix in others too\n"
        f"- Person {starter} answers each question using only what was in the passage\n"
        f"- If the answer is not in the passage, Person {starter} should say so\n"
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
    if p1_count + p2_count < 4:
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
