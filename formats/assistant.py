import re
import random as _random
from formats.shared import (
    ALLOWED_NAMES, story_endings,
    normalize_quotes, base_validate,
)

FORMAT_NAME = "assistant"

SYSTEM_PROMPT = (
    "You write simple conversations where one person uses tools to help another. "
    "Use only very basic words that a young child would understand. "
    "Mark each person's speech with <person1> and <person2> tags.\n\n"

    "The tool-using person has tools listed in a <tools> tag at the start of their first turn. "
    "When they use a tool, write <call> tool_name </call> or <call> tool_name: argument </call>. "
    "The tool result appears in <result> ... </result>. Then the person keeps talking.\n\n"

    "You must simulate the tool results yourself. Make them short and realistic.\n\n"

    "Example 1 — assistant checking weather:\n\n"
    "<person1> What is the weather like today? "
    "<person2> <tools> weather, time, remember, recall </tools> "
    "Let me check! "
    "<call> weather </call> "
    "<result> Sunny, 72 degrees. </result> "
    "It is sunny and 72 degrees right now! "
    "<person1> Nice! Can you remember that for me? "
    "<person2> Sure! "
    "<call> remember: weather is sunny and 72 degrees </call> "
    "<result> Stored. </result> "
    "I saved that for you.\n\n"

    "Example 2 — assistant doing math:\n\n"
    "<person1> I bought three apples for 2 dollars each. How much is that? "
    "<person2> <tools> calculate, time, search </tools> "
    "Let me figure that out. "
    "<call> calculate: 3 times 2 </call> "
    "<result> 6 </result> "
    "That is 6 dollars total. "
    "<person1> Thanks!\n\n"

    "Example 3 — game with exploration:\n\n"
    "<person1> I want to look around. "
    "<person2> <tools> look, open, pick_up, move, inventory </tools> "
    "<call> look </call> "
    "<result> A small room. There is a red door and a key on the floor. </result> "
    "You are in a small room. There is a red door. I see a key on the floor. "
    "<person1> Pick up the key! "
    "<person2> <call> pick_up: key </call> "
    "<result> You picked up the key. </result> "
    "Got it! You now have the key. "
    "<person1> Now open the door. "
    "<person2> <call> open: red door </call> "
    "<result> The red door opens. You see a sunny garden. </result> "
    "The door is open! There is a sunny garden on the other side.\n\n"

    "Example 4 — smart home:\n\n"
    "<person1> It is too dark in here. "
    "<person2> <tools> lights, music, temperature, timer </tools> "
    "I can fix that! "
    "<call> lights: on </call> "
    "<result> Lights are now on. </result> "
    "The lights are on now. Is that better? "
    "<person1> Yes! Can you also play some music? "
    "<person2> Sure! "
    "<call> music: play something happy </call> "
    "<result> Now playing: happy songs. </result> "
    "Music is playing now!\n\n"

    "Example 5 — refusing when a tool is not available:\n\n"
    "<person1> Can you check the weather? "
    "<person2> <tools> calculate, timer, remember </tools> "
    "I am sorry, I do not have a weather tool. I can not check the weather. "
    "But I can help you with math, set a timer, or remember things for you. "
    "<person1> Oh, okay. Then can you remember to bring an umbrella? "
    "<person2> Sure! "
    "<call> remember: bring an umbrella </call> "
    "<result> Stored. </result> "
    "I will remember that for you!\n\n"

    "Example 6 — game refusal:\n\n"
    "<person1> Can I fly over the wall? "
    "<person2> <tools> look, move, pick_up, open </tools> "
    "I am sorry, you can not fly. You do not have that power. "
    "But you can look around for another way, or try to open something. "
    "<person1> Okay, let me look around then. "
    "<person2> <call> look </call> "
    "<result> There is a small gate in the wall. It is closed. </result> "
    "I see a small gate in the wall! Do you want to try to open it?"
)

ALL_TOOLS = {
    "weather": "Returns the weather (e.g. Sunny, 72 degrees)",
    "time": "Returns the current time (e.g. 3:30 in the afternoon)",
    "date": "Returns today's date (e.g. March 5)",
    "remember": "Stores something to remember. Returns: Stored",
    "recall": "Gets something that was stored before. Returns the stored info",
    "calculate": "Does simple math. Returns the answer",
    "search": "Looks up a simple fact. Returns a short answer",
    "send_message": "Sends a message to someone. Returns: Sent",
    "timer": "Sets a timer or reminder. Returns: Timer set",
    "lights": "Turns lights on or off. Returns: Lights on/off",
    "music": "Plays or stops music. Returns what is playing",
    "temperature": "Sets the room temperature. Returns: Set to [X] degrees",
    "look": "Looks around a place. Returns what you see",
    "open": "Opens something like a door or box. Returns what happens",
    "pick_up": "Picks up an item. Returns: Picked up [item]",
    "inventory": "Lists what items you have. Returns a list",
    "move": "Moves to a new place. Returns where you are now",
    "talk": "Talks to a character. Returns what they say",
    "use": "Uses an item on something. Returns what happens",
    "list_add": "Adds something to a list. Returns: Added",
    "list_show": "Shows what is on a list. Returns the list",
}

TOOL_NAMES = list(ALL_TOOLS.keys())

CATEGORY_TOOLS = {
    "weather": ["weather", "time", "date", "remember"],
    "memory": ["remember", "recall", "time", "search"],
    "math": ["calculate", "remember", "time"],
    "smart_home": ["lights", "music", "temperature", "timer"],
    "game_explore": ["look", "open", "pick_up", "inventory", "move"],
    "game_social": ["look", "talk", "move", "inventory"],
    "game_items": ["pick_up", "use", "inventory", "look", "open"],
    "organization": ["list_add", "list_show", "remember", "recall", "timer"],
    "communication": ["send_message", "search", "time", "remember"],
    "search": ["search", "calculate", "time", "date"],
}

NUM_DISTRACTORS = 2

TOPICS = [
    # Weather & time
    "checking the weather before going outside",
    "checking if it will rain today",
    "checking the weather to plan a trip",
    "asking what time it is",
    "checking today's date",
    "checking the weather and remembering it",
    "asking about the weather to decide what to wear",

    # Memory
    "asking to remember a phone number",
    "asking to remember a name",
    "asking to recall a number that was stored before",
    "asking to remember what to buy at the store",
    "asking to remember a birthday",
    "storing a secret word and recalling it later",
    "remembering where something was left",
    "remembering a recipe and recalling it later",

    # Math
    "asking to add two numbers",
    "asking how much change to expect from a purchase",
    "asking to split a bill between friends",
    "asking how many days until an event",
    "asking to multiply small numbers",
    "figuring out how many items are needed",
    "counting the total cost of several things",

    # Smart home
    "asking to turn on the lights",
    "asking to change the room temperature",
    "asking to play some music",
    "asking to turn off the lights at bedtime",
    "setting a timer for cooking",
    "asking to play a specific kind of music",
    "making the room warmer on a cold day",
    "turning off music and dimming lights",
    "setting a timer and turning on lights",

    # Game — exploration
    "exploring a dark cave",
    "entering an old house for the first time",
    "looking around a forest clearing",
    "finding a locked door and searching for the key",
    "reaching a river and finding a way across",
    "discovering a hidden room behind a wall",
    "exploring a garden with many paths",
    "entering a tower and climbing the stairs",
    "walking into a village for the first time",
    "finding a treasure chest in a cave",

    # Game — items
    "picking up a sword from the ground",
    "using a key to open a locked box",
    "checking what items are in your bag",
    "finding a map and using it",
    "giving a gift to a character in the game",
    "using a rope to cross a gap",
    "finding food and eating it",
    "picking up a lantern to light the way",

    # Game — social
    "talking to a wise old man in a village",
    "asking a guard to let you pass",
    "meeting a lost child and helping them",
    "trading items with a merchant",
    "talking to an animal that can speak",
    "asking a farmer for directions",
    "meeting a friend at the village gate",

    # Organization
    "making a shopping list",
    "checking what is on the to-do list",
    "adding a task to a to-do list",
    "making a list of things to pack for a trip",
    "setting a reminder to water the plants",
    "making a list of birthday gifts to buy",
    "checking a list and removing finished tasks",

    # Communication
    "sending a message to a friend",
    "looking up a fact and telling someone",
    "checking the time before sending a message",
    "searching for someone's birthday and sending a message",
    "sending a thank-you message",
    "searching for a word and sending its meaning",

    # Search / info
    "looking up how far away the moon is",
    "looking up what the biggest animal is",
    "searching for when a holiday is",
    "looking up how many legs a spider has",
    "searching for what a word means",
    "looking up the name of a planet",

    # Weather — extended
    "checking if it is safe to go outside in a storm",
    "checking the weather in a different city",
    "asking what the weather will be like tomorrow",
    "checking if it is too cold to go swimming",

    # Memory — extended
    "asking to remember a list of three things",
    "storing a friend's address and recalling it later",
    "asking to remember a joke someone told",
    "storing a password and getting it back later",
    "remembering what day the meeting is on",
    "recalling the name of a song you heard",

    # Math — extended
    "asking how much paint is needed for a wall",
    "asking how much fabric to buy for a project",
    "asking how many cups of flour for a recipe",
    "dividing a pizza fairly between people",
    "calculating how far it is to walk somewhere",
    "figuring out how long until dinner is ready",

    # Smart home — extended
    "asking to set the lights to dim",
    "setting a morning alarm",
    "asking to lock all the doors before bed",
    "adjusting the temperature because it is too hot",
    "playing a bedtime song for a child",
    "turning off everything before leaving the house",
    "setting a timer to check on the oven",

    # Game — exploration extended
    "finding a bridge over a deep valley",
    "entering a castle for the first time",
    "walking through a field of tall grass",
    "discovering a waterfall behind some rocks",
    "finding stairs going down into the ground",
    "reaching the top of a mountain",
    "exploring a shipwreck on the beach",
    "entering a dark tunnel",
    "finding a campsite someone left behind",
    "discovering a door hidden behind vines",

    # Game — items extended
    "finding a bottle with a note inside",
    "using a shield to block something",
    "combining two items to make something new",
    "finding armor in an old chest",
    "using a bucket to carry water",
    "finding a fishing rod near a stream",
    "picking up coins scattered on the floor",

    # Game — social extended
    "asking a shopkeeper about a rare item",
    "helping a villager fix their broken cart",
    "listening to a traveler tell a strange story",
    "convincing a bridge keeper to let you pass",
    "meeting a person who is lost and scared",
    "trading food with a hungry stranger",
    "asking a child where the hidden path is",

    # Organization — extended
    "planning a meal for the week",
    "making a packing list for a camping trip",
    "organizing a list of chores by room",
    "setting reminders for watering different plants",
    "keeping track of books you want to read",

    # Communication — extended
    "writing a message to say happy birthday",
    "sending a message to cancel plans",
    "looking up a phone number and calling someone",
    "searching for directions and sending them to a friend",
    "writing a thank-you note to a teacher",

    # Multi-step scenarios
    "checking the weather, then setting a reminder to bring a coat",
    "looking up a recipe, then making a shopping list",
    "checking the time, then sending a message that you will be late",
    "looking up a fact for homework, then remembering it for later",
    "searching for a word, then using it in a sentence",
]

TOPIC_CATEGORIES = {}
for t in TOPICS:
    if any(w in t for w in ["weather", "rain", "wear"]):
        TOPIC_CATEGORIES[t] = "weather"
    elif any(w in t for w in ["time", "date"]):
        if "send" not in t:
            TOPIC_CATEGORIES[t] = "weather"
        else:
            TOPIC_CATEGORIES[t] = "communication"
    elif any(w in t for w in ["remember", "recall", "stored", "secret", "storing", "remembering"]):
        TOPIC_CATEGORIES[t] = "memory"
    elif any(w in t for w in ["add", "split", "multiply", "change", "cost", "count",
                               "how many", "how much", "figuring"]):
        TOPIC_CATEGORIES[t] = "math"
    elif any(w in t for w in ["lights", "temperature", "music", "timer for cooking",
                               "warmer", "dimming", "turning off", "bedtime"]):
        TOPIC_CATEGORIES[t] = "smart_home"
    elif any(w in t for w in ["explor", "cave", "house for the first", "forest",
                               "locked door", "river", "hidden room", "garden with",
                               "tower", "village for the first", "treasure chest"]):
        TOPIC_CATEGORIES[t] = "game_explore"
    elif any(w in t for w in ["picking up", "using a key", "checking what items",
                               "finding a map", "giving a gift", "using a rope",
                               "finding food", "lantern"]):
        TOPIC_CATEGORIES[t] = "game_items"
    elif any(w in t for w in ["talking to", "asking a guard", "meeting a",
                               "trading", "animal that can speak", "asking a farmer",
                               "friend at the"]):
        TOPIC_CATEGORIES[t] = "game_social"
    elif any(w in t for w in ["list", "reminder", "to-do", "pack"]):
        TOPIC_CATEGORIES[t] = "organization"
    elif any(w in t for w in ["sending", "message", "thank"]):
        TOPIC_CATEGORIES[t] = "communication"
    elif any(w in t for w in ["looking up", "searching", "search"]):
        TOPIC_CATEGORIES[t] = "search"
    else:
        TOPIC_CATEGORIES[t] = "memory"

NAMES_PER_CONVERSATION = 4

SCENARIO_TYPES = ["assistant", "assistant", "assistant", "game", "smart_home"]


def _pick_tools(category, k, rng):
    primary = CATEGORY_TOOLS.get(category, CATEGORY_TOOLS["memory"])
    other_tools = [t for t in TOOL_NAMES if t not in primary]
    distractors = rng.sample(other_tools, min(NUM_DISTRACTORS, len(other_tools)))
    tools = list(primary) + distractors
    rng.shuffle(tools)
    return tools


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
        "include_refusal": k % 3 == 0,
    }


def create_prompt(params):
    topic = params["topic"]
    category = TOPIC_CATEGORIES.get(topic, "memory")
    rng = _random.Random(hash(topic + params.get("subject", "")))
    available_tools = _pick_tools(category, 0, rng)

    tool_desc_lines = []
    for t in available_tools:
        desc = ALL_TOOLS.get(t, "")
        tool_desc_lines.append(f"  - {t}: {desc}")
    tool_desc = "\n".join(tool_desc_lines)

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

    starter_letter_instruction = ""
    if params.get("initial_letter"):
        starter_letter_instruction = (
            f"\n- Start the conversation with {params['initial_word_type']} that begins with "
            f"the letter {params['initial_letter']}"
        )

    starter = params.get("starter", 1)
    other = 2 if starter == 1 else 1

    is_game = category.startswith("game")

    if is_game:
        scenario_instruction = (
            f"Write a conversation where Person {starter} is playing a simple game or exploring a place. "
            f"Person {other} is the game helper who uses tools to show what happens. "
            f"The scenario is about {topic}. "
            f"The game world must involve {params['subject']}."
        )
    else:
        scenario_instruction = (
            f"Write a conversation where Person {other} is a helpful assistant who uses tools. "
            f"Person {starter} asks for help with {topic}. "
            f"The conversation must involve {params['subject']}."
        )

    ending = params.get("story_ending", "happy")
    ending_instruction = ""
    if ending == "sad":
        ending_instruction = "\n- The conversation should end on a sad or difficult note"
    elif ending == "neutral":
        ending_instruction = "\n- The conversation should end in a matter-of-fact way"

    refusal_instruction = ""
    if params.get("include_refusal"):
        refusal_instruction = (
            f"\n- At some point, Person {starter} should ask for something that Person {other}'s "
            f"tools CANNOT do. Person {other} should explain simply that they can not do that "
            f"because they do not have the right tool, and suggest what they can do instead"
        )

    user_prompt = (
        f"{scenario_instruction} "
        f"The conversation should be {params['tone']} in tone and "
        f"at least {params['min_chars']} characters long.\n\n"
        f"Available tools for Person {other}:\n{tool_desc}\n\n"
        f"Rules:\n"
        f"- Use <person1> and <person2> tags to mark who is speaking\n"
        f"- Person {other} must list their tools in <tools> ... </tools> at the start of their first turn\n"
        f"- Use <call> tool_name </call> to call a tool, or <call> tool_name: argument </call> if it needs input\n"
        f"- Write the tool result in <result> ... </result> right after each call\n"
        f"- Person {other} should use at least 2 different tools during the conversation\n"
        f"- Person {other} should only use tools from the <tools> list\n"
        f"- If Person {starter} asks for something that requires a tool Person {other} does not have, "
        f"Person {other} should say they can not do that and explain why\n"
        f"- Simulate realistic tool results yourself\n"
        f"- Keep tool results short (one or two sentences)\n"
        f"- Use very basic, simple words only\n"
        f"- No big or unusual words\n"
        f"- If using names, pick from: {names_str}"
        f"{starter_letter_instruction}"
        f"{grammar_instruction}"
        f"{intro_instruction}"
        f"{refusal_instruction}"
        f"{ending_instruction}\n\n"
        f"Write the conversation now:"
    )

    return SYSTEM_PROMPT, user_prompt


def validate(text):
    errors = []

    p1_count = text.count("<person1>")
    p2_count = text.count("<person2>")
    call_count = len(re.findall(r"<call>", text))
    result_count = len(re.findall(r"<result>", text))
    has_tools_tag = bool(re.search(r"<tools>", text))

    if p1_count == 0:
        errors.append("missing_person1_tag")
    if p2_count == 0:
        errors.append("missing_person2_tag")
    if p1_count + p2_count < 3:
        errors.append("too_few_turns")
    if call_count == 0:
        errors.append("no_tool_calls")
    if result_count == 0:
        errors.append("no_tool_results")
    if not has_tools_tag:
        errors.append("no_tools_declaration")

    metrics = base_validate(text)
    metrics.update({
        "valid": len(errors) == 0,
        "errors": errors,
        "person1_turns": p1_count,
        "person2_turns": p2_count,
        "total_turns": p1_count + p2_count,
        "tool_calls": call_count,
        "tool_results": result_count,
    })
    return metrics


def normalize(text):
    text = normalize_quotes(text)
    text = re.sub(r"</person[12]>", "", text)
    text = re.sub(r"</tools>", " </tools>", text)
    text = re.sub(r"<tools>\s*", "<tools> ", text)
    text = re.sub(r"\s*</tools>", " </tools>", text)
    text = re.sub(r"\s+", " ", text)

    first_tag = re.search(r"<person[12]>", text)
    if first_tag:
        text = text[first_tag.start():]

    return text.strip()
