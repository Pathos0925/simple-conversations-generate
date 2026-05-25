import re
import random as _random
from formats.shared import (
    ALLOWED_NAMES, story_endings,
    normalize_quotes, base_validate,
)

FORMAT_NAME = "story"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person tells a story to another. "
    "Mark each person's speech with <person1> and <person2> tags. "
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
    # Everyday drama
    "a shopkeeper who gave away too much",
    "a teacher on her first day of school",
    "a child who lied and then felt bad",
    "a stranger who helped and then disappeared",
    "a woman who planted one seed every day",
    "a man who lost his voice for a week",
    "a neighbor who never came outside",
    "the day the well in the village ran dry",
    "a meal that brought two enemies together",
    "a coin that kept changing hands",
    "a road that nobody wanted to walk on",
    "the sound that came from under the floor",
    "a window that looked out on a different world each day",
    # Journeys and quests
    "a messenger who had to cross a desert",
    "a child who followed a cat to a strange place",
    "a ship that sailed into a fog and came back changed",
    "a group of children who built a raft",
    "a girl who climbed a mountain to find the truth",
    "a boy who swam to the bottom of a lake",
    "two travelers who took different paths",
    "a wagon that carried a secret cargo",
    # Animals with character
    "a crow that collected shiny things",
    "a wolf that was afraid of the dark",
    "a fish that jumped out of the water every morning",
    "a goat that escaped from every fence",
    "an old cat that remembered everything",
    "a hen that refused to lay eggs",
    "a dog that guarded an empty house",
    "a swarm of bees that moved to a new home",
    # Consequences and choices
    "a wish that went wrong",
    "a trade that seemed fair but was not",
    "a warning that nobody listened to",
    "a door that should not have been opened",
    "a fire that someone started by accident",
    "a bridge that could only be crossed once",
    "a promise made to a dying friend",
    "the last tree in a town that cut them all down",
    # Mysteries and secrets
    "a map that led to the wrong place",
    "a song that only one person could hear",
    "a shadow that moved on its own",
    "a painting that changed overnight",
    "footprints that appeared in the snow with no one around",
    "a locked room with a light inside",
    "a name carved into a very old tree",
    "a clock that started ticking backward",
    # Community and belonging
    "a festival that almost did not happen",
    "a new law that made everyone angry",
    "the building of a school in a small village",
    "a flood that made neighbors work together",
    "a stranger who joined a small town",
    "the oldest person in the village telling their story",
    "a market day when everything went wrong",
    "a wall that divided two parts of a town",
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
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
    }


def create_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))

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

    persona_instruction = ""
    if params.get("persona"):
        persona_instruction = f"\n- Tell the story from the perspective of {params['persona']}"

    ending = params.get("story_ending", "happy")
    ending_instruction = ""
    if ending == "sad":
        ending_instruction = "\n- The story should end on a sad or difficult note, without forcing a happy resolution"
    elif ending == "neutral":
        ending_instruction = "\n- The story should end in a matter-of-fact or unresolved way"

    starter = params.get("starter", 1)
    other = 2 if starter == 1 else 1
    s_tag = f"<person{starter}>"
    o_tag = f"<person{other}>"

    user_prompt = (
        f"Write a conversation where Person {starter} tells a story to Person {other}. "
        f"The story should be about {params.get('theme', 'Friendship')}, "
        f"include {params['topic']}, be {params.get('style', 'simple')} in its writing style, "
        f"and ideally feature {params.get('feature', 'dialogue')}. "
        f"The story must involve {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} is the storyteller. Person {other} listens and sometimes asks questions or reacts\n"
        f"- Person {other} should speak much less than Person {starter}\n"
        f"- Use only very simple, common words that a young child would understand\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names in the story, pick from: {names_str}\n"
        f"- Start the conversation with {params['initial_word_type']} that begins with "
        f"the letter {params['initial_letter']}"
        f"{grammar_instruction}"
        f"{intro_instruction}"
        f"{persona_instruction}"
        f"{ending_instruction}\n\n"
        f"Format example:\n"
        f"{s_tag} Do you want to hear a story? {o_tag} Yes please! "
        f"{s_tag} Once there was a little cat who lived near a big tree...\n\n"
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
