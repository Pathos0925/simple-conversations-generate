import re
import random as _random
from formats.shared import (
    ALLOWED_NAMES, story_endings,
    normalize_quotes, base_validate,
)

FORMAT_NAME = "summary"

SYSTEM_PROMPT = (
    "You write a short, simple story and then a summary of that story. "
    "Use only very basic words that a young child would understand. "
    "Mark each person's speech with <person1> and <person2> tags.\n\n"

    "Person 1 tells a short story. Person 2 gives a summary of the story "
    "in a few short sentences. The summary should capture the main idea "
    "and the most important things that happened.\n\n"

    "Keep sentences short. No fancy words, no complex ideas.\n\n"

    "Example:\n\n"
    "<person1> Let me tell you a story. There was a little dog named Max. "
    "Max lived on a farm with a kind old man. Every day, Max would run "
    "around the fields and chase the birds. One day, a big storm came. "
    "The wind was very strong and the rain was very heavy. Max was scared. "
    "He hid under the bed and would not come out. The old man sat next to "
    "the bed and talked to Max in a soft voice. He said it was okay and "
    "that the storm would pass. After a long time, the storm stopped. "
    "Max came out and the sun was shining again. Max ran outside and "
    "played in the puddles. He was not scared anymore. "
    "<person2> This story is about a dog named Max who lives on a farm. "
    "A big storm comes and Max is scared, so he hides under the bed. "
    "The old man helps him feel safe. When the storm is over, Max goes "
    "outside and plays again. The story is about being brave and having "
    "someone to help you when you are scared."
)

NAMES_PER_CONVERSATION = 4

TOPICS = [
    # Animal stories
    "a cat that got lost and found its way home",
    "a dog that learned a new trick",
    "a bird that could not fly",
    "a fish that wanted to see the land",
    "a rabbit that dug a very deep hole",
    "a mouse that lived in a big house",
    "a horse that ran faster than the wind",
    "a turtle that won a race",
    "a bear that could not sleep all winter",
    "a fox that tried to trick the other animals",
    "a duck that was different from the others",
    "a spider that built something beautiful",

    # Adventure stories
    "a child who found a hidden cave",
    "a girl who climbed the tallest tree",
    "a boy who built a boat and sailed away",
    "two friends who got lost in the woods",
    "a family that moved to a new town",
    "a child who found a treasure map",
    "a boy who walked a very long way to find water",
    "a girl who crossed a river to help a friend",
    "someone who explored an old empty house",
    "a child who followed a strange path",

    # Friendship and social
    "two children who became friends",
    "a child who shared their last piece of bread",
    "a person who helped a stranger on the road",
    "two people who had a fight and then made up",
    "a child who stood up for someone smaller",
    "a new kid at school who felt left out",
    "a friend who kept a promise even when it was hard",
    "someone who gave away their favorite toy",
    "a child who forgave someone who was mean to them",

    # Family stories
    "a mother who worked very hard for her children",
    "a father who told stories every night",
    "a grandmother who taught a child to cook",
    "a brother and sister who solved a problem together",
    "a family that planted a garden together",
    "a child who took care of a sick parent",
    "a grandparent who remembered the old days",

    # Problem and solution
    "a farmer whose crops would not grow",
    "a baker who ran out of flour",
    "a builder who had to fix a broken bridge",
    "a child who lost something important",
    "a town that had no water for a long time",
    "someone who broke something and had to fix it",
    "a person who was afraid of the dark",
    "a child who could not sleep at night",
    "someone who had to choose between two things",

    # Nature and weather
    "a village that survived a big storm",
    "the day the river flooded the town",
    "a flower that grew in a place with no sun",
    "a tree that was the oldest in the forest",
    "the first day of snow in a small village",
    "a garden that came back to life in spring",

    # Work and effort
    "a child who practiced until they could do it",
    "a person who saved money for something special",
    "someone who built a house with their own hands",
    "a person who learned to read when they were old",
    "a child who made a gift for someone they loved",
    "a person who walked a long way to get to work",

    # Sad and bittersweet
    "a child who had to say goodbye to a pet",
    "a person who moved far away from home",
    "a friend who went away and never came back",
    "a toy that was loved until it fell apart",
    "a tree that was cut down to build a house",
    "someone who waited for a letter that never came",

    # Magic and wonder
    "a child who found a magic stone",
    "a door that led to a strange new world",
    "a wishing well that granted one wish",
    "an old book that told a secret",
    "a mirror that showed a different place",
    "a seed that grew into something nobody expected",

    # Cleverness and wit
    "a small animal that tricked a much bigger one",
    "a child who solved a problem the adults could not",
    "a merchant who made a very clever trade",
    "a thief who stole something and then gave it back",
    "a farmer who outsmarted the weather",
    "a girl who found a way to carry water uphill",

    # Mistakes and learning
    "a boy who told a lie that got bigger and bigger",
    "a person who took the wrong road and found something better",
    "a baker who used the wrong ingredient and made something new",
    "a builder who built a house that fell down twice",
    "a child who broke a rule and learned why it was there",
    "a fisherman who threw back the biggest catch of his life",

    # Kindness and sacrifice
    "a stranger who gave their coat to someone cold",
    "a dog that walked a long way to find its owner",
    "a mother who stayed up all night for her sick child",
    "a child who gave their lunch to a hungry classmate",
    "a brother who did his sister's chores so she could rest",
    "a farmer who shared his harvest in a year when he had very little",

    # Fear and bravery
    "a boy who was afraid of water but had to cross a river",
    "a girl who walked into a dark forest alone",
    "a child who spoke up when no one else would",
    "a man who faced a wolf to protect his sheep",
    "a woman who sailed a boat in a terrible storm",
    "a person who stood at the edge of a cliff and jumped into the sea",

    # Loss and change
    "a town that flooded and had to start over",
    "a family that lost their home in a fire",
    "a man who came back to his village after many years",
    "a woman who sold everything to start a new life",
    "a child who grew up and came back to visit",
    "an old couple who planted a tree they would never sit under",
    "a teacher who retired and was forgotten, then remembered",

    # Unexpected outcomes
    "a race that the slowest runner won",
    "a storm that uncovered something buried long ago",
    "a mistake that led to the best day ever",
    "a broken bridge that saved a village from invaders",
    "a wrong turn that led to a hidden valley",
    "a dropped coin that rolled into the right hands",

    # Animals being animals
    "a hen that sat on a stone thinking it was an egg",
    "a pig that escaped and went on an adventure",
    "a cat and a bird that became unlikely friends",
    "a group of ants that moved a mountain of crumbs",
    "a donkey that refused to carry one more thing",
    "an old elephant that remembered where water was hidden",

    # Simple daily stories
    "a child's first time cooking dinner for the family",
    "a grandfather who fixed a clock that had been broken for years",
    "a woman who grew the biggest pumpkin anyone had seen",
    "a boy who delivered bread in the rain every morning",
    "a girl who collected stones and gave one to everyone she met",
    "a family that ate together every night no matter what",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(a in t for a in ["cat", "dog", "bird", "fish", "rabbit", "mouse",
                             "horse", "turtle", "bear", "fox", "duck", "spider"]):
        TOPIC_CATEGORIES[t] = "animals"
    elif any(w in t for w in ["cave", "climb", "boat", "sail", "lost", "treasure",
                               "explore", "walked a very long", "crossed a river",
                               "followed a strange"]):
        TOPIC_CATEGORIES[t] = "adventure"
    elif any(w in t for w in ["friend", "shared", "helped a stranger", "fight",
                               "stood up", "new kid", "promise", "gave away",
                               "forgave"]):
        TOPIC_CATEGORIES[t] = "friendship"
    elif any(w in t for w in ["mother", "father", "grandmother", "brother",
                               "sister", "family", "grandparent", "parent"]):
        TOPIC_CATEGORIES[t] = "family"
    elif any(w in t for w in ["farmer", "baker", "builder", "lost something",
                               "no water", "broke something", "afraid", "could not sleep",
                               "choose between"]):
        TOPIC_CATEGORIES[t] = "problem"
    elif any(w in t for w in ["storm", "flood", "flower", "tree", "snow",
                               "garden", "river"]):
        TOPIC_CATEGORIES[t] = "nature"
    elif any(w in t for w in ["practiced", "saved money", "built a house",
                               "learned to read", "made a gift", "walked a long way"]):
        TOPIC_CATEGORIES[t] = "effort"
    elif any(w in t for w in ["goodbye", "moved far", "went away", "fell apart",
                               "cut down", "waited for"]):
        TOPIC_CATEGORIES[t] = "sad"
    elif any(w in t for w in ["magic", "door that led", "wishing well", "old book",
                               "mirror that", "seed that grew"]):
        TOPIC_CATEGORIES[t] = "wonder"
    else:
        TOPIC_CATEGORIES[t] = "general"

themes = [
    "Friendship", "Courage", "Kindness", "Adventure", "Family",
    "Perseverance", "Curiosity", "Honesty", "Teamwork", "Responsibility",
    "Generosity", "Helping Others", "Hardship", "Independence",
    "Problem-Solving", "Humor", "Love", "Hope", "Dreams", "Trust",
    "Growth", "Loss", "Celebration", "Wonder", "Resilience",
    "Grief", "Anger", "Forgiveness",
]

styles = [
    "whimsical", "playful", "fairy tale-like", "modern",
    "lighthearted", "heartwarming", "humorous", "fable-like",
    "melancholic", "minimalist", "suspenseful", "gentle",
]


def get_extra_params(k, rng=None):
    rng = rng or _random

    ending = rng.choices(
        [e[0] for e in story_endings],
        weights=[e[1] for e in story_endings],
        k=1,
    )[0]

    return {
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "starter": 1 + (k % 2),
        "story_ending": ending,
        "theme": themes[k % len(themes)],
        "style": styles[k % len(styles)],
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
            "\n- Both people should introduce themselves by name at the start of the conversation"
        )

    starter_letter_instruction = ""
    if params.get("initial_letter"):
        starter_letter_instruction = (
            f"\n- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
        )

    ending = params.get("story_ending", "happy")
    ending_instruction = ""
    if ending == "sad":
        ending_instruction = "\n- The story should end on a sad or difficult note"
    elif ending == "neutral":
        ending_instruction = "\n- The story should end in an unresolved or matter-of-fact way"

    theme = params.get("theme", "Friendship")
    style = params.get("style", "simple")

    user_prompt = (
        f"Write a conversation where Person {starter} tells a short story about "
        f"{params['topic']}. The story should be about {theme} and told in a "
        f"{style} way. The story must involve {params['subject']}. "
        f"Then Person {other} gives a short summary of the story.\n\n"
        f"The full text should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} tells the full story first (at least 6 sentences)\n"
        f"- Person {other} then summarizes the story in 3 to 5 short sentences\n"
        f"- The summary should say what the story was about, what happened, and how it ended\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names in the story, pick from: {names_str}"
        f"{starter_letter_instruction}"
        f"{grammar_instruction}"
        f"{intro_instruction}"
        f"{ending_instruction}\n\n"
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
    if p1_count + p2_count < 2:
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
