import re
import random as _random
from formats.shared import ALLOWED_NAMES, normalize_quotes, base_validate

FORMAT_NAME = "letter"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person reads or dictates a letter "
    "and the other person helps or reacts. Mark each person's speech with "
    "<person1> and <person2> tags. "
    "The letter part should start with 'Dear [Name],' and end with a sign-off. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas."
)

RELATIONSHIPS = [
    "friend", "family", "neighbor", "pen pal", "classmate",
    "coworker", "old friend",
]

TOPICS = [
    # News sharing
    "telling about a new pet",
    "telling about a trip",
    "telling about school",
    "telling about a new baby in the family",
    "telling about a new job",
    "telling about moving to a new house",
    "telling about learning something new",
    "telling about growing a garden",
    "telling about a funny thing that happened",
    "telling about a big storm",
    "telling about a holiday",
    "telling about a birthday party",
    "telling about meeting someone new",
    "telling about finishing a hard task",
    # Requests
    "asking for help with something",
    "asking someone to visit",
    "asking to borrow something",
    "asking for a recipe",
    "asking for advice about a problem",
    "asking someone to write back",
    # Feelings
    "saying you miss someone",
    "saying thank you for a gift",
    "saying sorry for something",
    "sharing good news",
    "sharing sad news",
    "telling someone you are proud of them",
    "telling someone you think about them",
    "saying goodbye before a long trip",
    # Events and invitations
    "inviting someone to a party",
    "inviting someone to visit your town",
    "inviting someone to help with a project",
    "telling about a wedding",
    "telling about a concert or show",
    # Advice
    "giving advice about a problem",
    "giving advice about being sad",
    "warning someone about bad weather",
    "suggesting a book or game",
    "telling someone how to take care of a plant",
    # Pen pal / Distance
    "introducing yourself to a pen pal",
    "telling a pen pal about your town",
    "telling a pen pal about your family",
    "telling a pen pal about your favorite things",
    "describing your daily routine to someone far away",
    "telling someone far away about the seasons where you live",
    # Memories
    "remembering a fun time together",
    "talking about when you were young",
    "sharing a memory of someone who is gone",
    "remembering a trip you took together",
    # Updates
    "telling about how the garden is doing",
    "telling about how the kids are doing",
    "telling about how work is going",
    "telling about what the weather has been like",
    "telling about a book you just read",
    "telling about a meal you cooked",
    "telling about fixing something at home",
    "telling about a walk you took",
    # Apologies and conflicts
    "writing to make up after a fight",
    "explaining why you have not written in a long time",
    "saying sorry for missing a birthday",
    "asking for forgiveness",
    # Gratitude
    "thanking someone for their help",
    "thanking someone for being a good friend",
    "thanking a teacher",
    "thanking a neighbor for their kindness",
    # Daily life updates
    "telling about a new hobby",
    "telling about something funny the dog did",
    "telling about a hard day at school",
    "telling about a long walk you took",
    "telling about a book you liked",
    "telling about the first time you cooked alone",
    "telling about a dream you had last night",
    "telling about finding something old in the attic",
    "telling about your new neighbor",
    "telling about learning to swim",
    # Seasonal and holiday
    "telling about what you did for the holiday",
    "telling about how cold the winter has been",
    "telling about picking apples in the fall",
    "telling about the flowers blooming in spring",
    "telling about a summer day at the lake",
    "telling about a snowstorm",
    "telling about decorating the house for a holiday",
    # Worries and concerns
    "worrying about a sick family member",
    "telling about being afraid of something",
    "asking what to do about a problem at work",
    "telling about feeling stuck in life",
    "asking for help because you feel alone",
    "telling about a big decision you need to make",
    "telling about something you regret",
    # Celebrations and milestones
    "telling about passing a test",
    "telling about a baby learning to walk",
    "sharing news about getting married",
    "telling about finishing building something",
    "celebrating a year at a new job",
    "telling about a child's first word",
    # Plans and dreams
    "telling about a trip you want to take",
    "asking someone to come visit you",
    "planning a surprise for someone",
    "telling about a goal you set for yourself",
    "asking what someone thinks about an idea",
    "dreaming about what life will be like later",
    # Nature and observations
    "describing what the sky looked like last night",
    "telling about a bird that visits your window every day",
    "telling about a big tree that fell in a storm",
    "telling about how the river near your house looks in spring",
    "describing the sunset you saw yesterday",
    # Food and sharing
    "sending a recipe you want to share",
    "telling about a meal you made that went wrong",
    "asking for a recipe from home",
    "telling about a new food you tried",
    # Work and school
    "telling about a new teacher at school",
    "telling about learning something hard at work",
    "telling about a project you are working on",
    "asking advice about a problem with a coworker",
    "telling about your first day at a new place",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if t.startswith("telling about"):
        TOPIC_CATEGORIES[t] = "news"
    elif t.startswith("asking"):
        TOPIC_CATEGORIES[t] = "request"
    elif t.startswith("saying") or "miss" in t or "proud" in t or "think about" in t:
        TOPIC_CATEGORIES[t] = "feelings"
    elif t.startswith("inviting") or "wedding" in t or "concert" in t:
        TOPIC_CATEGORIES[t] = "events"
    elif t.startswith("giving advice") or t.startswith("warning") or t.startswith("suggesting"):
        TOPIC_CATEGORIES[t] = "advice"
    elif "pen pal" in t or "far away" in t or "routine" in t:
        TOPIC_CATEGORIES[t] = "pen pal"
    elif "remember" in t or "memory" in t or "when you were" in t:
        TOPIC_CATEGORIES[t] = "memories"
    elif "thank" in t:
        TOPIC_CATEGORIES[t] = "gratitude"
    elif "sorry" in t or "fight" in t or "forgive" in t or "not written" in t or "missing" in t:
        TOPIC_CATEGORIES[t] = "apology"
    else:
        TOPIC_CATEGORIES[t] = "general"


def get_extra_params(k, rng=None):
    rng = rng or _random
    names = rng.sample(ALLOWED_NAMES, 2)
    return {
        "sender_name": names[0],
        "recipient_name": names[1],
        "relationship": RELATIONSHIPS[k % len(RELATIONSHIPS)],
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
    }


def create_prompt(params):
    sender = params.get("sender_name", "Mia")
    recipient = params.get("recipient_name", "Leo")
    relationship = params.get("relationship", "friend")

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
            f"\n- Start the conversation with {params['initial_word_type']} "
            f"that begins with the letter {params['initial_letter']}"
        )

    ending_instruction = ""
    ending = params.get("story_ending", "")
    if ending == "sad":
        ending_instruction = "\n- The letter should have a sad or difficult tone, without forcing a happy ending"
    elif ending == "neutral":
        ending_instruction = "\n- The letter should feel ordinary and matter-of-fact"

    starter = params.get("starter", 1)
    other = 2 if starter == 1 else 1
    s_tag = f"<person{starter}>"
    o_tag = f"<person{other}>"
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))

    user_prompt = (
        f"Write a conversation where Person {starter} wants to write a letter to "
        f"{recipient} (a {relationship}) about {params['topic']}. "
        f"Person {other} helps them write it or listens as they read it aloud. "
        f"The letter is from {sender} to {recipient}. "
        f"The letter must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- The letter content should include 'Dear {recipient},' and a sign-off like "
        f"'Your {relationship}, {sender}' or 'Love, {sender}'\n"
        f"- Person {starter} reads or dictates the letter. Person {other} suggests "
        f"changes, reacts, or asks questions\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using other names, pick from: {names_str}"
        f"{starter_letter_instruction}"
        f"{grammar_instruction}"
        f"{intro_instruction}"
        f"{ending_instruction}\n\n"
        f"Format example:\n"
        f"{s_tag} I want to write a letter to {recipient}. Can you help? "
        f"{o_tag} Sure! What do you want to say? "
        f"{s_tag} Dear {recipient}, ...\n\n"
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

    has_dear = bool(re.search(r"\bdear\b", text, re.IGNORECASE))
    if not has_dear:
        errors.append("missing_greeting")

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
