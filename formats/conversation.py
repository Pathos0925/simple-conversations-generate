import random as _random
from formats.shared import (
    ALLOWED_NAMES, SIMPLICITY_RULES, story_endings,
    normalize_quotes, base_validate,
)
import re

FORMAT_NAME = "conversation"

SYSTEM_PROMPT = (
    "You write simple conversations between two people using only very basic words. "
    "Mark each person's speech with <person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas. "
    "Not every conversation needs a happy ending. Sometimes things are sad, "
    "unresolved, or just ordinary. Reflect real life."
)

NAMES_PER_CONVERSATION = 4

CONVERSATION_MODES = [
    ("storytelling", 0.25),
    ("dialogue", 0.75),
]

TOPICS = [
    # Math
    "adding and subtracting small numbers",
    "counting and numbers",
    "simple shapes",
    "comparing sizes and amounts",
    "multiplying small numbers",
    "splitting things into equal parts",
    # Science
    "why the sky is blue and weather",
    "animals and what they eat",
    "plants and how they grow",
    "the sun, moon, and stars",
    "how magnets work",
    "why things float or sink",
    "how sound travels",
    "what makes ice melt",
    # History
    "the moon landing",
    "dinosaurs lived long ago",
    "famous explorers and discoveries",
    "the building of the pyramids",
    "the first airplane flight",
    # Fiction / Storytelling
    "a story about a lost pet",
    "a story about a magical adventure",
    "a story about making a new friend",
    "a story about a brave child",
    "a story about a long journey",
    "a story about a hidden treasure",
    "a story about someone who got lost",
    # Casual / Daily Life
    "favorite foods",
    "the weather today",
    "playing outside",
    "going to school",
    "family and home",
    "bedtime and morning",
    "helping around the house",
    "pets and animals at home",
    "cooking a meal",
    "fixing something that broke",
    "waiting for something",
    "getting lost and finding the way back",
    # Work and Adult Life
    "going to work",
    "building or making something",
    "growing food in a garden",
    "selling things at a market",
    "a long day of hard work",
    "learning a new skill",
    "saving money for something",
    # Technology
    "how computers work",
    "sending a message to someone far away",
    "how a phone works",
    "what the internet is",
    # Feelings and Social
    "being kind to others",
    "feeling happy or sad",
    "sharing and taking turns",
    "saying sorry and making up",
    "being proud of something you did",
    "feeling nervous about something new",
    "missing someone who is far away",
    # Imagination and Play
    "pretending to be something",
    "a fun trip or vacation",
    "a funny thing that happened",
    "what it would be like to fly",
    "if animals could talk",
    # Grounded / Realistic
    "losing a game or contest",
    "a pet that died",
    "moving away from friends",
    "being left out",
    "making a mistake",
    "something that broke and cannot be fixed",
    "not getting what you wanted",
    "a disagreement between two people",
    "being tired but having to keep going",
    "being angry",
    "arguments",
    # Nature and Seasons
    "a very hot day",
    "a cold winter night",
    "watching a sunset",
    "a big storm",
    "the first day of spring",
    # Practical Knowledge
    "how to stay safe near water",
    "why sleep is important",
    "how to take care of a pet",
    "what to do when you are sick",
    "how to find your way if you are lost",
    # Introductions
    "two people meeting for the first time",
    "introducing yourself to a new neighbor",
    "meeting someone at work",
    "making friends with a stranger",
    # Language and grammar
    "explaining what a noun is with examples",
    "explaining what a verb is with examples",
    "explaining what an adjective is",
    "explaining how to use prepositions",
    "explaining what a pronoun is",
    "explaining the difference between past and present tense",
    "explaining what a sentence needs to be complete",
    "explaining what rhyming words are",
    "explaining what vowels and consonants are",
    "explaining what a plural means and how to make one",
    "explaining what a question word is",
    "explaining what an adverb does in a sentence",
]

TOPIC_CATEGORIES = {
    "adding and subtracting small numbers": "math",
    "counting and numbers": "math",
    "simple shapes": "math",
    "comparing sizes and amounts": "math",
    "multiplying small numbers": "math",
    "splitting things into equal parts": "math",
    "why the sky is blue and weather": "science",
    "animals and what they eat": "science",
    "plants and how they grow": "science",
    "the sun, moon, and stars": "science",
    "how magnets work": "science",
    "why things float or sink": "science",
    "how sound travels": "science",
    "what makes ice melt": "science",
    "the moon landing": "history",
    "dinosaurs lived long ago": "history",
    "famous explorers and discoveries": "history",
    "the building of the pyramids": "history",
    "the first airplane flight": "history",
    "a story about a lost pet": "fiction",
    "a story about a magical adventure": "fiction",
    "a story about making a new friend": "fiction",
    "a story about a brave child": "fiction",
    "a story about a long journey": "fiction",
    "a story about a hidden treasure": "fiction",
    "a story about someone who got lost": "fiction",
    "favorite foods": "casual",
    "the weather today": "casual",
    "playing outside": "casual",
    "going to school": "casual",
    "family and home": "casual",
    "bedtime and morning": "casual",
    "helping around the house": "casual",
    "pets and animals at home": "casual",
    "cooking a meal": "casual",
    "fixing something that broke": "casual",
    "waiting for something": "casual",
    "getting lost and finding the way back": "casual",
    "going to work": "work",
    "building or making something": "work",
    "growing food in a garden": "work",
    "selling things at a market": "work",
    "a long day of hard work": "work",
    "learning a new skill": "work",
    "saving money for something": "work",
    "how computers work": "technology",
    "sending a message to someone far away": "technology",
    "how a phone works": "technology",
    "what the internet is": "technology",
    "being kind to others": "social",
    "feeling happy or sad": "social",
    "sharing and taking turns": "social",
    "saying sorry and making up": "social",
    "being proud of something you did": "social",
    "feeling nervous about something new": "social",
    "missing someone who is far away": "social",
    "pretending to be something": "imagination",
    "a fun trip or vacation": "imagination",
    "a funny thing that happened": "imagination",
    "what it would be like to fly": "imagination",
    "if animals could talk": "imagination",
    "losing a game or contest": "grounded",
    "a pet that died": "grounded",
    "moving away from friends": "grounded",
    "being left out": "grounded",
    "making a mistake": "grounded",
    "something that broke and cannot be fixed": "grounded",
    "not getting what you wanted": "grounded",
    "a disagreement between two people": "grounded",
    "being tired but having to keep going": "grounded",
    "being angry": "grounded",
    "arguments": "grounded",
    "a very hot day": "nature",
    "a cold winter night": "nature",
    "watching a sunset": "nature",
    "a big storm": "nature",
    "the first day of spring": "nature",
    "how to stay safe near water": "practical",
    "why sleep is important": "practical",
    "how to take care of a pet": "practical",
    "what to do when you are sick": "practical",
    "how to find your way if you are lost": "practical",
    "two people meeting for the first time": "introductions",
    "introducing yourself to a new neighbor": "introductions",
    "meeting someone at work": "introductions",
    "making friends with a stranger": "introductions",
    "explaining what a noun is with examples": "language",
    "explaining what a verb is with examples": "language",
    "explaining what an adjective is": "language",
    "explaining how to use prepositions": "language",
    "explaining what a pronoun is": "language",
    "explaining the difference between past and present tense": "language",
    "explaining what a sentence needs to be complete": "language",
    "explaining what rhyming words are": "language",
    "explaining what vowels and consonants are": "language",
    "explaining what a plural means and how to make one": "language",
    "explaining what a question word is": "language",
    "explaining what an adverb does in a sentence": "language",
}

story_themes = [
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

story_styles = [
    "whimsical", "playful", "epic", "fairy tale-like", "modern",
    "classic", "lyric", "mythological", "lighthearted", "adventurous",
    "heartwarming", "humorous", "mystical", "action-packed", "fable-like",
    "surreal", "philosophical", "melancholic", "noir", "romantic",
    "tragic", "minimalist", "suspenseful",
]

story_features = [
    "dialogue", "in medias res", "a moral lesson",
    "absence indicating a presence", "a story told through letters",
    "a twist ending", "an unreliable narrator", "foreshadowing", "irony",
    "inner monologue", "symbolism", "a MacGuffin", "a non-linear timeline",
    "a reverse timeline", "circular narrative structure", "a flashback",
    "a nested structure", "a story within a story", "a Red Herring",
    "multiple perspectives", "Checkhov's gun", "the fourth wall",
    "a cliffhanger", "an anti-hero", "juxtaposition", "climactic structure",
]

story_personas = [
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

    mode_labels = [m[0] for m in CONVERSATION_MODES]
    mode_weights = [m[1] for m in CONVERSATION_MODES]
    mode = rng.choices(mode_labels, weights=mode_weights, k=1)[0]

    ending = rng.choices(
        [e[0] for e in story_endings],
        weights=[e[1] for e in story_endings],
        k=1,
    )[0]

    params = {
        "mode": mode,
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "story_ending": ending,
    }

    if mode == "storytelling":
        params["story_theme"] = story_themes[k % len(story_themes)]
        params["story_style"] = story_styles[k % len(story_styles)]
        params["story_feature"] = story_features[k % len(story_features)]
        params["story_persona"] = story_personas[k % len(story_personas)] if k % 3 == 0 else ""

    return params


def create_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))

    grammar_instruction = ""
    if params.get("grammar"):
        grammar_instruction = (
            f"\n- Where it fits naturally, demonstrate the use of {params['grammar']}."
        )

    ending = params.get("story_ending", "happy")
    ending_instruction = ""
    if ending == "sad":
        ending_instruction = "\n- The conversation should end on a sad or difficult note, without forcing a happy resolution"
    elif ending == "neutral":
        ending_instruction = "\n- The conversation should end in a matter-of-fact or unresolved way, not everything needs to be wrapped up neatly"

    starter = params.get("starter", 1)
    other = 2 if starter == 1 else 1
    s_tag = f"<person{starter}>"
    o_tag = f"<person{other}>"

    if params.get("mode") == "storytelling":
        theme = params.get("story_theme", "")
        style = params.get("story_style", "")
        feature = params.get("story_feature", "")
        persona = params.get("story_persona", "")

        story_direction = f"The story should be about {theme}" if theme else ""
        if style:
            story_direction += f", told in a {style} way"
        story_direction += "."
        if feature:
            story_direction += f" Try to include {feature}."
        persona_instruction = ""
        if persona:
            persona_instruction = f"\n- Tell the story from the perspective of {persona}"

        user_prompt = (
            f"Write a conversation where one person tells a story to another person about "
            f"{params['topic']}. The story must involve {params['subject']}. "
            f"The conversation should be {params['tone']} in tone and "
            f"at least {params['min_chars']} characters long.\n\n"
            f"{story_direction}\n\n"
            f"Rules:\n"
            f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
            f"- Person {starter} is the storyteller. Person {other} listens and sometimes asks questions or reacts\n"
            f"- Person {other} should speak much less than Person {starter}\n"
            f"- The story should be simple enough for a young child to understand\n"
            f"- Use very basic, simple words only\n"
            f"- Keep all explanations to one or two short sentences\n"
            f"- No big or unusual words\n"
            f"- If using names in the story, pick from: {names_str}\n"
            f"- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
            f"{grammar_instruction}"
            f"{persona_instruction}"
            f"{ending_instruction}\n\n"
            f"Format example:\n"
            f"{s_tag} Want to hear a story? {o_tag} Yes please! {s_tag} Once there "
            f"was a little cat who lived near a big tree...\n\n"
            f"Write the conversation now:"
        )
    else:
        user_prompt = (
            f"Write a conversation between two people about {params['topic']}. "
            f"The conversation must involve {params['subject']}. "
            f"The conversation should be {params['tone']} in tone and at least "
            f"{params['min_chars']} characters long.\n\n"
            f"Rules:\n"
            f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
            f"- Person {starter} speaks first\n"
            f"- Use very basic, simple words only\n"
            f"- Keep all explanations to one or two short sentences\n"
            f"- No big or unusual words\n"
            f"- If using names, pick from: {names_str}\n"
            f"- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
            f"{grammar_instruction}"
            f"{ending_instruction}\n\n"
            f"Format example:\n"
            f"{s_tag} Hello! Do you want to talk about something? {o_tag} Sure! "
            f"What should we talk about?\n\n"
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
