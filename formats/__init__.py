from formats import story, conversation, instruction, description, letter, diary, assistant, summary

FORMAT_MODULES = {
    "story": story,
    "conversation": conversation,
    "instruction": instruction,
    "description": description,
    "letter": letter,
    "diary": diary,
    "assistant": assistant,
    "summary": summary,
}

FORMAT_NAMES = list(FORMAT_MODULES.keys())
FORMAT_WEIGHTS = [1.0 / len(FORMAT_NAMES)] * len(FORMAT_NAMES)


def get_format(name):
    return FORMAT_MODULES[name]
