import random as _random
from formats.shared import (
    ALLOWED_NAMES, story_endings,
    normalize_quotes, base_validate,
)

FORMAT_NAME = "story"

SYSTEM_PROMPT = (
    "You write short, simple stories using only very basic words. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas. "
    "Not every story needs a happy ending. Sometimes things are sad, "
    "unresolved, or just ordinary. Reflect real life."
)

TOPICS = [
    "talking animals", "fantasy worlds", "time travel",
    "a deadline or time limit", "space exploration", "mystical creatures",
    "underwater adventures", "dinosaurs", "pirates", "superheroes",
    "fairy tales", "outer space", "hidden treasures", "magical lands",
    "enchanted forests", "secret societies", "robots and technology",
    "sports", "school life", "holidays", "cultural traditions",
    "magical objects", "lost civilizations", "subterranean worlds",
    "bygone eras", "invisibility", "giant creatures", "miniature worlds",
    "alien encounters", "haunted places", "shape-shifting",
    "island adventures", "unusual vehicles", "undercover missions",
    "dream worlds", "virtual worlds", "riddles", "sibling rivalry",
    "treasure hunts", "snowy adventures", "seasonal changes",
    "mysterious maps", "royal kingdoms", "living objects", "gardens",
    "lost cities", "the arts", "the sky",
    # Additional grounded topics for variety
    "a child who moved to a new town",
    "a farmer and a difficult season",
    "two friends who had a fight",
    "a family meal that went wrong",
    "a long walk home",
    "a day at the market",
    "a broken toy",
    "a promise that was hard to keep",
    "the oldest tree in town",
    "a letter that arrived too late",
    "a rainy day with nothing to do",
    "a gift that changed everything",
    "a night when the power went out",
    "a dog that ran away and came back",
    "a secret place only one person knew about",
    "a boat trip on a quiet river",
    "a cold morning before sunrise",
    "an old house with a strange room",
]

TOPIC_CATEGORIES = {
    "talking animals": "fantasy",
    "fantasy worlds": "fantasy",
    "time travel": "fantasy",
    "a deadline or time limit": "adventure",
    "space exploration": "adventure",
    "mystical creatures": "fantasy",
    "underwater adventures": "adventure",
    "dinosaurs": "adventure",
    "pirates": "adventure",
    "superheroes": "fantasy",
    "fairy tales": "fantasy",
    "outer space": "adventure",
    "hidden treasures": "adventure",
    "magical lands": "fantasy",
    "enchanted forests": "fantasy",
    "secret societies": "adventure",
    "robots and technology": "technology",
    "sports": "daily life",
    "school life": "daily life",
    "holidays": "daily life",
    "cultural traditions": "daily life",
    "magical objects": "fantasy",
    "lost civilizations": "adventure",
    "subterranean worlds": "adventure",
    "bygone eras": "history",
    "invisibility": "fantasy",
    "giant creatures": "fantasy",
    "miniature worlds": "fantasy",
    "alien encounters": "fantasy",
    "haunted places": "fantasy",
    "shape-shifting": "fantasy",
    "island adventures": "adventure",
    "unusual vehicles": "adventure",
    "undercover missions": "adventure",
    "dream worlds": "fantasy",
    "virtual worlds": "technology",
    "riddles": "adventure",
    "sibling rivalry": "daily life",
    "treasure hunts": "adventure",
    "snowy adventures": "adventure",
    "seasonal changes": "nature",
    "mysterious maps": "adventure",
    "royal kingdoms": "fantasy",
    "living objects": "fantasy",
    "gardens": "nature",
    "lost cities": "adventure",
    "the arts": "daily life",
    "the sky": "nature",
    "a child who moved to a new town": "grounded",
    "a farmer and a difficult season": "grounded",
    "two friends who had a fight": "grounded",
    "a family meal that went wrong": "grounded",
    "a long walk home": "grounded",
    "a day at the market": "grounded",
    "a broken toy": "grounded",
    "a promise that was hard to keep": "grounded",
    "the oldest tree in town": "grounded",
    "a letter that arrived too late": "grounded",
    "a rainy day with nothing to do": "grounded",
    "a gift that changed everything": "grounded",
    "a night when the power went out": "grounded",
    "a dog that ran away and came back": "grounded",
    "a secret place only one person knew about": "grounded",
    "a boat trip on a quiet river": "grounded",
    "a cold morning before sunrise": "grounded",
    "an old house with a strange room": "grounded",
}

themes = [
    "Friendship", "Courage", "Contradiction", "Coming of age", "Kindness",
    "Amnesia", "Adventure", "Imagination", "Family", "Perseverance",
    "Curiosity", "Honesty", "Romance", "Teamwork", "Responsibility",
    "Strategy", "Magic", "Discovery", "Betrayal", "Deception",
    "Generosity", "Creativity", "Self-Acceptance", "Helping Others",
    "Hardship", "Agency", "Power", "Revenge", "Independence",
    "Problem-Solving", "Resourcefulness", "Long-Term Thinking", "Optimism",
    "Humor", "Love", "The Five Senses", "Tradition", "Innovation",
    "Hope", "Dreams", "Belonging", "Travel", "Overcoming", "Trust",
    "Morality", "Happiness", "Consciousness", "Failure", "Conflict",
    "Cooperation", "Growth", "Loss", "Celebration", "Transformation",
    "Scheming", "Challenge", "Planning", "Wonder", "Surprises",
    "Conscience", "Intelligence", "Logic", "Resilience",
    "Grief", "Anger", "Death",
]

styles = [
    "whimsical", "playful", "epic", "fairy tale-like", "modern",
    "classic", "lyric", "mythological", "lighthearted", "adventurous",
    "heartwarming", "humorous", "mystical", "action-packed", "fable-like",
    "surreal", "philosophical", "melancholic", "noir", "romantic",
    "tragic", "minimalist", "suspenseful",
]

features = [
    "dialogue", "in medias res", "a moral lesson",
    "absence indicating a presence", "a story told through letters",
    "a twist ending", "an unreliable narrator", "foreshadowing", "irony",
    "inner monologue", "symbolism", "a MacGuffin", "a non-linear timeline",
    "a reverse timeline", "circular narrative structure", "a flashback",
    "a nested structure", "a story within a story", "a Red Herring",
    "multiple perspectives", "Checkhov's gun", "the fourth wall",
    "a cliffhanger", "an anti-hero", "juxtaposition", "climactic structure",
]

personas = [
    "an explorer archetype", "a rebellious author", "a powerful leader",
    "a wise, old person who wants to teach the young", "an innocent author",
    "a moralistic teacher", "a hopeless romantic",
    "a hurt, ill-intentioned person", "an academic", "a jester archetype",
    "a poet", "a philosopher", "a mother", "a father", "someone curious",
    "someone evil", "someone who wants to prove a point", "a child",
    "a pedant", "the everyman", "the oppressed", "a cruel person",
    "someone who loves order and structure",
]


def get_extra_params(k, rng=None):
    rng = rng or _random

    ending = rng.choices(
        [e[0] for e in story_endings],
        weights=[e[1] for e in story_endings],
        k=1,
    )[0]

    return {
        "theme": themes[k % len(themes)],
        "style": styles[k % len(styles)],
        "feature": features[k % len(features)],
        "persona": personas[k % len(personas)] if k % 3 == 0 else "",
        "story_ending": ending,
        "num_paragraphs": 1 + (k % 7),
    }


def create_prompt(params):
    names_str = ", ".join(ALLOWED_NAMES[:16])

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f" The most important thing is to write an engaging easy story, "
            f"but where it makes sense, demonstrate the use of {params['grammar']}."
        )

    persona_instruction = ""
    if params.get("persona"):
        persona_instruction = f" Write from the perspective of {params['persona']}."

    ending = params.get("story_ending", "happy")
    ending_instruction = ""
    if ending == "sad":
        ending_instruction = " The story should end on a sad or difficult note, without forcing a happy resolution."
    elif ending == "neutral":
        ending_instruction = " The story should end in a matter-of-fact or unresolved way."

    num_paragraphs = params.get("num_paragraphs", 3)

    user_prompt = (
        f"Write a short story ({num_paragraphs} paragraph{'s' if num_paragraphs > 1 else ''}) "
        f"using very basic words. The story should be about {params.get('theme', 'Friendship')}, "
        f"include {params['topic']}, be {params.get('style', 'simple')} in its writing style, "
        f"and ideally feature {params.get('feature', 'dialogue')}. "
        f"The story must involve {params['subject']}. "
        f"The story should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long."
        f"{grammar_instruction}{persona_instruction}{ending_instruction}\n\n"
        f"Rules:\n"
        f"- Use only very simple, common words that a young child would understand\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If you need to use names, pick from: {names_str}\n"
        f"- Start the story with {params['initial_word_type']} that begins with "
        f"the letter {params['initial_letter']}\n\n"
        f"Write the story now:"
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
    for marker in ["THE END.", "THE END", "End.", "---"]:
        if text.rstrip().endswith(marker):
            text = text.rstrip()[:-len(marker)]
    return text.strip()
