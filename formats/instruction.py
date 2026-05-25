import re
from formats.shared import normalize_quotes, base_validate

FORMAT_NAME = "instruction"

SYSTEM_PROMPT = (
    "You write simple step-by-step instructions using only very basic words. "
    "Write clear, practical instructions that a young child could follow. "
    "Use words like 'First', 'Then', 'Next', 'After that', 'Finally' to mark steps. "
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
    return {
        "num_steps": 3 + (k % 6),
    }


def create_prompt(params):
    num_steps = params.get("num_steps", 5)

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    user_prompt = (
        f"Write simple step-by-step instructions for {params['topic']}. "
        f"The instructions must mention {params['subject']}. "
        f"The text should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Write about {num_steps} steps\n"
        f"- Use step markers like 'First', 'Then', 'Next', 'After that', 'Finally'\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- Explain each step clearly so a child could follow\n"
        f"- Start the instructions with {params['initial_word_type']} that begins with "
        f"the letter {params['initial_letter']}"
        f"{grammar_instruction}\n\n"
        f"Write the instructions now:"
    )

    return SYSTEM_PROMPT, user_prompt


def validate(text):
    errors = []
    metrics = base_validate(text)

    step_matches = STEP_MARKERS.findall(text)
    step_count = len(step_matches)

    if step_count < 2:
        errors.append("too_few_steps")
    if metrics["character_count"] < 100:
        errors.append("too_short")

    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
        "step_count": step_count,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    return text.strip()
