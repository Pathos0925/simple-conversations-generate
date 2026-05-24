LANGUAGE = "en"

END_STRING = "END_CONVERSATION."

letter_frequencies = {
    'A': 11.7, 'B': 4.4, 'C': 5.2, 'D': 3.2, 'E': 2.8,
    'F': 4.0, 'G': 1.6, 'H': 4.2, 'I': 7.3, 'J': 0.51,
    'K': 0.86, 'L': 2.4, 'M': 3.8, 'N': 2.3, 'O': 7.6,
    'P': 4.3, 'Q': 0.22, 'R': 2.8, 'S': 6.7, 'T': 16.0,
    'U': 1.2, 'V': 0.82, 'W': 5.5, 'X': 0.045, 'Y': 0.76,
    'Z': 0.045
}

CONVERSATION_MODES = [
    ("storytelling", 0.25),
    ("dialogue", 0.75),
]

topics = [
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
    # History (only the biggest events)
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
]

topic_categories = {
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
    "meeting for the first time": "introductions",
    "two people meeting for the first time": "introductions",
    "introducing yourself to a new neighbor": "introductions",
    "meeting someone at work": "introductions",
    "making friends with a stranger": "introductions",
}

tones = [
    # Positive (~70%)
    "friendly", "curious", "excited", "calm", "playful",
    "helpful", "silly", "patient", "cheerful",
    "thoughtful", "encouraging", "gentle", "funny",
    # Neutral (~20%)
    "matter-of-fact", "quiet", "cautious", "tired",
    # Negative (~10%)
    "frustrated", "tense", "bittersweet", "argumentative", "angry",
]

grammars = [
    "present tense", "past tense", "future tense",
    "yes-no questions", "wh-questions", "imperative mood",
    "comparative forms", "superlative forms", "indirect speech",
    "relative clauses", "conditional mood",
]

# Specific subjects to anchor conversations and prevent repetition.
# A random subject is injected into the prompt to force variety.
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

word_types = ["a noun", "an adjective", "an adverb", "a preposition"]

ALLOWED_NAMES = [
    "Mia", "Alex", "Jean", "Samuel", "Lily", "Leo", "Jose", "Kim",
    "Alice", "Lena", "Rita", "Emmanuel", "Anne", "Peter", "Maria", "Luis",
    "Tom", "Sara", "Jack", "Nina", "Paul", "Rosa", "Ben", "Ella",
    "Max", "Jade", "Omar", "Clara", "Ivan", "Nora", "Adam", "Ruth",
]

NAMES_PER_CONVERSATION = 4

MIN_CHARS = 1024
MAX_CHARS = 2048
MAX_TOKENS = 4096

# Weighted endings: ~70% happy, ~20% neutral, ~10% negative
story_endings = [
    ("happy", 0.60),
    ("neutral", 0.30),
    ("sad", 0.10),
]

# SimpleStories English story parameters — used for storytelling mode only.
# Sourced from text_data.py English subsets.
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
    "Loss", "Grief", "Anger", "Death", "Failure",
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
