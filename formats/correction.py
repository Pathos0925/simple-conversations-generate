import re
import random as _random
from formats.shared import ALLOWED_NAMES, OUTPUT_CONSTRAINT, normalize_quotes, base_validate

FORMAT_NAME = "correction"

NAMES_PER_CONVERSATION = 4

ERROR_TYPES = ["spelling", "grammar", "wrong fact", "punctuation", "word choice"]

SYSTEM_PROMPT = (
    "You write simple conversations where one person says something with an error "
    "and the other person spots the error and explains the correction. "
    "Mark each person's speech with <person1> and <person2> tags. "
    "Use only very simple, common words that a young child would understand. "
    "Keep sentences short. No fancy words, no complex ideas. "
    "The corrector should be kind and explain what was wrong and what is right."
)

TOPICS = [
    # Spelling errors
    "a sentence with a spelling mistake about a cat",
    "a sentence with a misspelled color word",
    "a sentence with a misspelled animal name",
    "a sentence with a misspelled food word",
    "a sentence about the weather with a spelling error",
    "a sentence with a misspelled day of the week",
    "a sentence about school with a spelling mistake",
    "a short note with two spelling mistakes",
    "a sentence about a friend with a misspelled name",
    "a sentence with a misspelled number word",
    "a list of things with one word spelled wrong",
    "a sentence about a trip with a spelling error",
    # Grammar errors
    "a sentence with the wrong verb tense",
    "a sentence where the subject and verb do not agree",
    "a sentence with a missing word",
    "a sentence that uses 'me' instead of 'I'",
    "a sentence with a double negative",
    "a sentence where 'their' and 'there' are mixed up",
    "a sentence with the wrong plural form",
    "a sentence that uses 'good' instead of 'well'",
    "a sentence with a wrong pronoun",
    "a sentence with an extra word that does not belong",
    "a sentence where 'a' and 'an' are used wrong",
    "a sentence with two verbs where only one is needed",
    # Wrong facts
    "a sentence with a wrong animal fact",
    "a sentence that says the sun is cold",
    "a sentence that says fish live on land",
    "a sentence with a wrong color for something",
    "a sentence that says the moon makes its own light",
    "a sentence about how many legs a spider has that is wrong",
    "a sentence that says water flows uphill",
    "a sentence that says birds have four legs",
    "a sentence about the biggest animal that is wrong",
    "a sentence with the wrong number of days in a week",
    "a sentence that says ice is hot",
    "a sentence about where the sun rises that is wrong",
    "a sentence that says trees grow down into the sky",
    "a sentence about what season comes after summer that is wrong",
    # Punctuation errors
    "a sentence with a missing period",
    "a question without a question mark",
    "a sentence with a comma in the wrong place",
    "two sentences that are joined without a period",
    "a sentence that starts without a capital letter",
    "a name that is not capitalized",
    "a sentence with too many exclamation marks",
    "a sentence with an apostrophe in the wrong place",
    "a list without commas between the items",
    "a sentence where a period should be a question mark",
    # Word choice errors
    "a sentence that uses the wrong word for something you eat with",
    "a sentence that says 'borrow' when it should say 'lend'",
    "a sentence that confuses 'hear' and 'listen'",
    "a sentence that uses 'big' when 'tall' is the right word",
    "a sentence that confuses 'bring' and 'take'",
    "a sentence that says 'learn' when it should say 'teach'",
    "a sentence that uses the wrong animal sound",
    "a sentence that confuses 'see' and 'look'",
    "a sentence that uses 'come' when it should say 'go'",
    "a sentence that confuses 'say' and 'tell'",
    "a sentence that uses the wrong body part word",
    "a sentence where 'make' should be 'do'",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if "spelling" in t or "misspell" in t or "spelled wrong" in t:
        TOPIC_CATEGORIES[t] = "spelling"
    elif "verb" in t or "subject" in t or "missing word" in t or "pronoun" in t or \
         "plural" in t or "double negative" in t or "their" in t or "extra word" in t or \
         "'a' and" in t or "two verbs" in t or "'me'" in t or "'good'" in t:
        TOPIC_CATEGORIES[t] = "grammar"
    elif "wrong" in t and ("fact" in t or "color" in t or "animal" in t or "sun" in t or
         "fish" in t or "moon" in t or "spider" in t or "water" in t or "bird" in t or
         "biggest" in t or "days" in t or "ice" in t or "rises" in t or "trees" in t or
         "season" in t or "legs" in t):
        TOPIC_CATEGORIES[t] = "wrong fact"
    elif "period" in t or "question mark" in t or "comma" in t or "capital" in t or \
         "exclamation" in t or "apostrophe" in t or "joined" in t:
        TOPIC_CATEGORIES[t] = "punctuation"
    else:
        TOPIC_CATEGORIES[t] = "word choice"


def get_extra_params(k, rng=None):
    rng = rng or _random
    return {
        "starter": 1 + (k % 2),
        "names": rng.sample(ALLOWED_NAMES, NAMES_PER_CONVERSATION),
        "error_type": ERROR_TYPES[k % len(ERROR_TYPES)],
    }


def create_prompt(params):
    names_str = ", ".join(params.get("names", ALLOWED_NAMES[:NAMES_PER_CONVERSATION]))
    error_type = params.get("error_type", "spelling")

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
        f"Write a conversation about {params['topic']}. "
        f"Person {starter} says something that has a {error_type} error. "
        f"Person {other} notices the error and kindly explains what is wrong "
        f"and says the correct version. The conversation must mention {params['subject']}. "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Rules:\n"
        f"- Use ONLY <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {starter} should say at least 2 things with {error_type} errors\n"
        f"- Person {other} should explain each error clearly and give the correct version\n"
        f"- Person {starter} should try the correction and sometimes make another mistake\n"
        f"- Person {other} should be encouraging, not mean\n"
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
