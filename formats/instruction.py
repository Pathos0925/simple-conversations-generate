import re
import random as _random
from formats.shared import ALLOWED_NAMES, normalize_quotes, base_validate

FORMAT_NAME = "instruction"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person teaches another how to do something, "
    "step by step. Mark each person's speech with <person1> and <person2> tags. "
    "Use only very basic words that a young child would understand. "
    "The teacher should use words like 'First', 'Then', 'Next', 'After that', 'Finally' "
    "to mark steps. The learner asks questions and reacts. "
    "Keep sentences short. No fancy words, no complex ideas."
)

TOPICS = [
    # Cooking
    "how to make a sandwich",
    "how to boil an egg",
    "how to make soup",
    "how to bake a simple cake",
    "how to cook rice",
    "how to make tea",
    "how to make a salad",
    "how to fry an egg",
    "how to make toast",
    "how to make lemonade",
    "how to wash fruit before eating",
    "how to peel a potato",
    "how to make oatmeal",
    "how to pack a lunch",
    # Building / Crafts
    "how to build a birdhouse",
    "how to make a paper airplane",
    "how to tie a knot",
    "how to fold a paper boat",
    "how to make a kite",
    "how to build a tower with blocks",
    "how to make a card for someone",
    "how to draw a simple picture",
    "how to make a mask from paper",
    "how to sew a button",
    "how to make a necklace from beads",
    "how to weave a simple basket",
    # Gardening
    "how to plant a seed",
    "how to water a garden",
    "how to grow tomatoes",
    "how to make a flower bed",
    "how to pull weeds",
    "how to plant a tree",
    "how to grow herbs in a pot",
    "how to make compost",
    # Repairs / Fixing
    "how to fix a flat tire on a bike",
    "how to patch a hole in clothes",
    "how to fix a leaky faucet",
    "how to sharpen a knife",
    "how to fix a squeaky door",
    "how to glue something that broke",
    # Personal care
    "how to brush your teeth properly",
    "how to wash your hands",
    "how to take care of a small cut",
    "how to pack a bag for a trip",
    "how to tie your shoes",
    "how to braid hair",
    "how to clean your glasses",
    # Outdoor
    "how to set up a tent",
    "how to build a campfire",
    "how to read a simple map",
    "how to fish with a rod",
    "how to find your way using the sun",
    "how to build a shelter from branches",
    "how to cross a stream safely",
    "how to spot animal tracks",
    # Animals
    "how to feed a baby bird",
    "how to take care of a puppy",
    "how to clean a fish tank",
    "how to groom a horse",
    "how to build a home for a hamster",
    "how to train a dog to sit",
    # Household
    "how to clean a room",
    "how to do laundry",
    "how to set a table",
    "how to organize a drawer",
    "how to wash dishes by hand",
    "how to sweep a floor",
    "how to make a bed",
    "how to fold clothes",
    "how to hang a picture on a wall",
    "how to change a light bulb",
    # Food preparation
    "how to peel an orange",
    "how to make butter from cream",
    "how to dry herbs for cooking",
    "how to make jam from berries",
    "how to roast vegetables",
    "how to make fresh pasta",
    "how to churn butter",
    "how to slice bread evenly",
    "how to store food so it stays fresh",
    "how to pickle cucumbers",
    # Construction and tools
    "how to measure and cut a piece of wood",
    "how to use a hammer and nail",
    "how to dig a hole for a fence post",
    "how to paint a wall",
    "how to build a simple shelf",
    "how to sand a rough surface smooth",
    "how to use a saw safely",
    "how to mix cement",
    # Nature and survival
    "how to purify water in the wild",
    "how to start a fire without matches",
    "how to find edible plants",
    "how to build a snow shelter",
    "how to signal for help if you are lost",
    "how to follow a trail in the forest",
    "how to stay dry in the rain without a roof",
    "how to collect rainwater",
    # Crafts and creativity
    "how to make a candle from wax",
    "how to carve a simple shape from soap",
    "how to make a wreath from branches",
    "how to press flowers in a book",
    "how to make paint from berries",
    "how to build a puppet from a sock",
    "how to make a drum from a can",
    "how to stitch two pieces of cloth together",
    "how to make a bookmark",
    "how to wrap a gift with paper",
    # Life skills
    "how to write a simple letter",
    "how to count change at a store",
    "how to read a clock",
    "how to plan a simple meal",
    "how to sort laundry by color",
    "how to carry something heavy safely",
    "how to introduce yourself to someone new",
    "how to ask for directions",
    "how to set an alarm to wake up on time",
    "how to take care of a cut on your finger",
    # Animals and farming
    "how to milk a cow",
    "how to collect eggs from a chicken coop",
    "how to build a simple bird feeder",
    "how to train a cat to come when called",
    "how to set up an ant farm",
    "how to brush a dog",
    "how to hatch eggs in an incubator",
    "how to catch a fish and release it",
    # Around the house
    "how to unclog a drain",
    "how to remove a stain from clothing",
    "how to sharpen a pencil with a knife",
    "how to replace a button on a shirt",
    "how to oil a squeaky hinge",
    "how to stop a door from slamming",
    "how to fix a hole in a sock",
]

TOPIC_CATEGORIES = {t: t.split("how to ")[1].split()[0] if "how to " in t else "general" for t in TOPICS}
_CATEGORY_MAP = {
    "make": "cooking/crafts", "boil": "cooking", "bake": "cooking", "cook": "cooking",
    "fry": "cooking", "wash": "cleaning", "peel": "cooking", "pack": "practical",
    "build": "building", "tie": "practical", "fold": "crafts", "draw": "crafts",
    "sew": "crafts", "weave": "crafts", "plant": "gardening", "water": "gardening",
    "grow": "gardening", "pull": "gardening", "fix": "repairs", "patch": "repairs",
    "sharpen": "repairs", "glue": "repairs", "brush": "personal care",
    "take": "practical", "braid": "personal care", "clean": "cleaning",
    "set": "practical", "read": "outdoor", "fish": "outdoor", "find": "outdoor",
    "spot": "outdoor", "feed": "animals", "groom": "animals", "train": "animals",
    "do": "household", "organize": "household", "sweep": "household",
    "hang": "household", "change": "household", "cross": "outdoor",
}
TOPIC_CATEGORIES = {}
for t in TOPICS:
    after = t.replace("how to ", "")
    first_word = after.split()[0]
    TOPIC_CATEGORIES[t] = _CATEGORY_MAP.get(first_word, "practical")

STEP_MARKERS = re.compile(
    r"\b(first|then|next|after that|finally|step \d|second|third|fourth|fifth|last|now|to start)\b",
    re.IGNORECASE,
)


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "num_steps": 3 + (k % 6),
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
    }


def create_prompt(params):
    num_steps = params.get("num_steps", 5)
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

    user_prompt = (
        f"Write a conversation where Person {starter} asks Person {other} to teach them "
        f"{params['topic']}. Person {other} explains it step by step. "
        f"The instructions must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {other} teaches using about {num_steps} steps\n"
        f"- Person {other} should use step markers like 'First', 'Then', 'Next', 'After that', 'Finally'\n"
        f"- Person {starter} asks questions, reacts, or confirms they understand\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names, pick from: {names_str}"
        f"{starter_letter_instruction}"
        f"{grammar_instruction}"
        f"{intro_instruction}\n\n"
        f"Format example:\n"
        f"{s_tag} Can you teach me {params['topic']}? {o_tag} Sure! First, you need to...\n\n"
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

    step_matches = STEP_MARKERS.findall(text)
    step_count = len(step_matches)

    if step_count < 2:
        errors.append("too_few_steps")

    metrics = base_validate(text)
    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
        "person1_turns": p1_count,
        "person2_turns": p2_count,
        "total_turns": p1_count + p2_count,
        "step_count": step_count,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    text = re.sub(r"</person[12]>", "", text)
    first_tag = re.search(r"<person[12]>", text)
    if first_tag:
        text = text[first_tag.start():]
    return text.strip()
