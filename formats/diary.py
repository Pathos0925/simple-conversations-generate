import re
import random as _random
from formats.shared import ALLOWED_NAMES, normalize_quotes, base_validate

FORMAT_NAME = "diary"

NAMES_PER_CONVERSATION = 4

SYSTEM_PROMPT = (
    "You write simple conversations where one person tells another about their day, "
    "like sharing a diary entry. Mark each person's speech with <person1> and <person2> tags. "
    "The storyteller uses first person ('I') and mostly past tense ('Today I went...'). "
    "The listener asks questions and reacts. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas."
)

MOODS = [
    "happy", "sad", "thoughtful", "excited", "worried",
    "tired", "grateful", "angry", "calm", "confused",
    "proud", "lonely",
]

TOPICS = [
    # Daily events
    "a day at school",
    "a trip to the market",
    "cooking dinner for the family",
    "a walk in the park",
    "cleaning the house",
    "a busy morning",
    "a lazy afternoon",
    "a ride on a bus",
    "a visit to the doctor",
    "going to the library",
    "eating at a new place",
    "running errands all day",
    "staying home on a rainy day",
    # Social
    "meeting a new friend",
    "a fight with a friend",
    "a family dinner",
    "playing with friends outside",
    "saying goodbye to someone",
    "a visit from a relative",
    "helping a neighbor",
    "talking to a stranger",
    "a party with friends",
    "spending time alone",
    "working on a project with someone",
    # Adventures
    "getting lost in a new place",
    "finding something special on the ground",
    "a long walk to somewhere new",
    "exploring a part of town I never saw",
    "climbing a hill for the first time",
    "swimming in a lake",
    "riding a bike far from home",
    "seeing a wild animal up close",
    "going fishing for the first time",
    "picking fruit from a tree",
    # Feelings
    "a day when I felt lonely",
    "a day when everything went right",
    "a day when I felt really scared",
    "being proud of something I did",
    "feeling nervous about tomorrow",
    "missing someone who is far away",
    "feeling angry and not knowing why",
    "a day when I could not stop laughing",
    "feeling grateful for what I have",
    "worrying about something that might happen",
    # Nature
    "a beautiful sunset I saw",
    "the first snow of the year",
    "watching birds outside my window",
    "a windy afternoon",
    "a big storm that came at night",
    "planting something in the garden",
    "finding a flower growing in a crack",
    "sitting by a river and thinking",
    # Milestones
    "my first day at a new school",
    "learning to ride a bike",
    "growing something in my garden for the first time",
    "finishing a hard task I started long ago",
    "the day I learned to cook something",
    "reading a whole book by myself",
    "teaching someone something I know",
    "the day I got my own room",
    # Problems
    "something important that broke",
    "losing something I care about",
    "making a big mistake",
    "a hard day at work",
    "a plan that did not work out",
    "spilling something and making a mess",
    "forgetting something important",
    "getting in trouble for something I did",
    # Animals
    "finding a lost animal",
    "taking care of a sick pet",
    "seeing an animal I never saw before",
    "feeding the birds in the yard",
    "the day we got a new pet",
    "saying goodbye to a pet",
    # Work and responsibility
    "a hard day at a new job",
    "helping someone carry something heavy",
    "being put in charge of something for the first time",
    "finishing a job that took many days",
    "getting paid for work you did",
    "making a delivery in bad weather",
    "teaching someone how to do your job",
    # Food and cooking
    "trying to bake a cake for the first time",
    "burning dinner and having to start over",
    "eating the best meal I ever had",
    "going to a market and buying too much",
    "picking berries and eating them on the way home",
    "making soup from whatever was in the kitchen",
    "sharing food with someone who had none",
    # Weather and seasons
    "the hottest day I can remember",
    "getting caught in the rain with no cover",
    "waking up to find everything covered in snow",
    "a day so foggy I could not see the road",
    "the wind that blew the roof off the shed",
    "a perfect cool morning in autumn",
    "watching the ice melt on the pond in spring",
    # Discovery and curiosity
    "finding an old box full of letters",
    "hearing a sound I could not explain",
    "discovering a path I never noticed before",
    "finding an animal hiding in the garden",
    "seeing a shooting star for the first time",
    "reading something that changed how I think",
    "noticing something new about a place I see every day",
    # Relationships
    "a long talk with someone I trust",
    "realizing someone was not a true friend",
    "doing something nice for someone without telling them",
    "getting into an argument and wishing I had not",
    "meeting someone who reminded me of someone else",
    "laughing so hard with a friend that I cried",
    "sitting in silence with someone and feeling okay",
    # Body and health
    "the day I was too sick to get out of bed",
    "exercising until my legs were tired",
    "not being able to sleep all night",
    "feeling better after being sick for a week",
    "hurting my hand and having to do everything differently",
    "falling down and getting a bruise",
    # Home and chores
    "cleaning the whole house by myself",
    "fixing something that has been broken for weeks",
    "rearranging my room and liking it better",
    "losing my keys and looking everywhere",
    "washing all the clothes and hanging them to dry",
    "painting a wall a new color",
    # Travel and new places
    "riding a bus to a town I never visited",
    "sleeping away from home for the first time",
    "getting lost in a city I do not know",
    "crossing a bridge that was very high up",
    "arriving somewhere after a very long trip",
    "seeing the ocean for the first time",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["school", "market", "dinner", "walk", "clean", "morning",
                             "afternoon", "bus", "doctor", "library", "eating",
                             "errands", "staying home", "rainy day"]):
        TOPIC_CATEGORIES[t] = "daily"
    elif any(w in t for w in ["friend", "family", "goodbye", "relative", "neighbor",
                               "stranger", "party", "alone", "project with"]):
        TOPIC_CATEGORIES[t] = "social"
    elif any(w in t for w in ["lost", "finding", "walk to", "exploring", "climbing",
                               "swimming", "riding", "fishing", "picking"]):
        TOPIC_CATEGORIES[t] = "adventure"
    elif any(w in t for w in ["felt", "proud", "nervous", "missing", "angry",
                               "laughing", "grateful", "worrying", "scared",
                               "everything went"]):
        TOPIC_CATEGORIES[t] = "feelings"
    elif any(w in t for w in ["sunset", "snow", "birds", "wind", "storm",
                               "planting", "flower", "river"]):
        TOPIC_CATEGORIES[t] = "nature"
    elif any(w in t for w in ["first day", "learning", "growing", "finishing",
                               "learned", "reading", "teaching", "got my own"]):
        TOPIC_CATEGORIES[t] = "milestones"
    elif any(w in t for w in ["broke", "losing", "mistake", "hard day",
                               "did not work", "spilling", "forgetting", "trouble"]):
        TOPIC_CATEGORIES[t] = "problems"
    elif any(w in t for w in ["animal", "pet", "birds in the yard"]):
        TOPIC_CATEGORIES[t] = "animals"
    else:
        TOPIC_CATEGORIES[t] = "general"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "mood": MOODS[k % len(MOODS)],
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
    }


def create_prompt(params):
    mood = params.get("mood", "thoughtful")
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

    ending_instruction = ""
    ending = params.get("story_ending", "")
    if ending == "sad":
        ending_instruction = "\n- The conversation should end on a sad or difficult note"
    elif ending == "neutral":
        ending_instruction = "\n- The conversation should end in a matter-of-fact way, not everything needs to be resolved"

    user_prompt = (
        f"Write a conversation where Person {starter} tells Person {other} about their day. "
        f"Person {starter} talks about {params['topic']}. "
        f"The storyteller is feeling {mood}. "
        f"The conversation must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} does most of the talking, sharing what happened like a diary entry\n"
        f"- Person {starter} should use first person ('I') and mostly past tense ('I went', 'I saw')\n"
        f"- Person {other} listens, asks questions, and reacts\n"
        f"- Use very basic, simple words only\n"
        f"- Keep sentences short. No big or unusual words\n"
        f"- If using names, pick from: {names_str}\n"
        f"- Start the conversation with {params['initial_word_type']} that begins with "
        f"the letter {params['initial_letter']}"
        f"{grammar_instruction}"
        f"{intro_instruction}"
        f"{ending_instruction}\n\n"
        f"Format example:\n"
        f"{s_tag} You will not believe what happened today. "
        f"{o_tag} What happened? Tell me! "
        f"{s_tag} I went to the park and...\n\n"
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

    i_count = len(re.findall(r"\bI\b", text))
    if i_count < 3:
        errors.append("too_few_first_person_markers")

    metrics = base_validate(text)
    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
        "person1_turns": p1_count,
        "person2_turns": p2_count,
        "total_turns": p1_count + p2_count,
        "first_person_count": i_count,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    text = re.sub(r"</person[12]>", "", text)
    first_tag = re.search(r"<person[12]>", text)
    if first_tag:
        text = text[first_tag.start():]
    return text.strip()
