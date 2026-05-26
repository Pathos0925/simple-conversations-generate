LANGUAGE = "en"

letter_frequencies = {
    'A': 11.7, 'B': 4.4, 'C': 5.2, 'D': 3.2, 'E': 2.8,
    'F': 4.0, 'G': 1.6, 'H': 4.2, 'I': 7.3, 'J': 0.51,
    'K': 0.86, 'L': 2.4, 'M': 3.8, 'N': 2.3, 'O': 7.6,
    'P': 4.3, 'Q': 0.22, 'R': 2.8, 'S': 6.7, 'T': 16.0,
    'U': 1.2, 'V': 0.82, 'W': 5.5, 'X': 0.045, 'Y': 0.76,
    'Z': 0.045,
}

word_types = ["a noun", "an adjective", "an adverb", "a preposition"]

subjects = [
    # Animals
    "a cat", "a dog", "a fish", "a bird", "a frog", "a rabbit", "a horse",
    "a cow", "a pig", "a duck", "a sheep", "a chicken", "a bear", "a fox",
    "a mouse", "a turtle", "a bee", "a spider", "a snake", "an ant",
    # Food
    "an apple", "bread", "milk", "rice", "soup", "eggs", "cheese",
    "a potato", "a carrot", "water", "corn", "a banana", "beans", "fish",
    "cake", "a cookie", "salt", "butter", "honey", "jam",
    # Objects
    "a ball", "a book", "a chair", "a cup", "a shoe", "a hat",
    "a box", "a key", "a rock", "a stick", "a rope", "a bell",
    "a candle", "a clock", "a bag", "a coin", "a blanket", "a map",
    "a basket", "a wheel",
    # Nature
    "a tree", "a river", "a hill", "the rain", "the wind", "snow",
    "a cloud", "a flower", "the sun", "the moon", "a lake", "a cave",
    "a field", "the ocean", "a garden", "a storm", "a puddle", "mud",
    "a leaf", "a stone",
    # Places
    "a house", "a barn", "a bridge", "a road", "a well", "a wall",
    "a gate", "a tower", "a farm", "a pond", "a market", "a hill",
    "a path", "a tent", "a roof", "a window", "a door", "a fence",
    "a shop", "a park",
    # People / Roles
    "a farmer", "a teacher", "a doctor", "a child", "a grandmother",
    "a brother", "a sister", "a friend", "a baby", "a king",
    "a queen", "a soldier", "a baker", "a sailor", "a builder",
    # Abstract / Simple concepts
    "a dream", "a secret", "a wish", "a plan", "a song",
    "a game", "a race", "a fight", "a gift", "a trick",
    "a mistake", "a promise", "a rule", "a lesson", "a number",
]

tones = [
    # Positive
    "friendly", "curious", "excited", "calm", "playful",
    "helpful", "silly", "patient", "cheerful",
    "thoughtful", "encouraging", "gentle", "funny",
    # Neutral
    "matter-of-fact", "quiet", "cautious", "tired",
    # Negative
    "frustrated", "tense", "bittersweet", "argumentative", "angry",
]

grammars = [
    "present tense", "past tense", "future tense", "progressive aspect",
    "perfect aspect", "passive voice", "conditional mood", "imperative mood",
    "indicative mood", "relative clauses", "prepositional phrases",
    "indirect speech", "exclamatory sentences", "comparative forms",
    "superlative forms", "subordinate clauses", "ellipsis", "anaphora",
    "cataphora", "wh-questions", "yes-no questions", "gerunds",
    "participle phrases", "inverted sentences", "non-finite clauses",
    "determiners", "quantifiers", "adjective order", "parallel structure",
    "discourse markers", "appositive phrases",
]

ALLOWED_NAMES = [
    "Mia", "Alex", "Jean", "Samuel", "Lily", "Leo", "Jose", "Kim",
    "Alice", "Lena", "Rita", "Emmanuel", "Anne", "Peter", "Maria", "Luis",
    "Tom", "Sara", "Jack", "Nina", "Paul", "Rosa", "Ben", "Ella",
    "Max", "Jade", "Omar", "Clara", "Ivan", "Nora", "Adam", "Ruth",
]

story_endings = [
    ("happy", 0.60),
    ("neutral", 0.30),
    ("sad", 0.10),
]

MIN_CHARS = 1024
MAX_CHARS = 2048
MAX_TOKENS = 4096

SIMPLICITY_RULES = (
    "- Use very basic, simple words only\n"
    "- Keep sentences short\n"
    "- No big or unusual words\n"
    "- Keep all explanations to one or two short sentences"
)

OUTPUT_CONSTRAINT = "\n- Return only the conversation. Do not add a title, explanation, or notes"

NAMES_INSTRUCTION = "If you need to use names, pick from: {names}"

SMART_QUOTE_TABLE = str.maketrans({
    "“": "\"",
    "”": "\"",
    "‘": "'",
    "’": "'",
    "—": "-",
    "…": "...",
})


def normalize_quotes(text):
    return text.translate(SMART_QUOTE_TABLE)


def base_validate(text):
    return {
        "character_count": len(text),
        "word_count": len(text.split()),
    }
