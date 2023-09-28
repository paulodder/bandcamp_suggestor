import random

# Only used the first encounter
first_time_greeting = """Welcome to boomkètèl radio. It's a pleasure to serve you.
I normally find tracks behind the scenes, but since this is our first encounter,
I need some time to get started. I'll be right back."""

# combined with subjects

# combined with greetings
subjects = [
    "friendly friend",
    "misty mouse",
    "lawd",
    "mark",
    "lad",
    "geezer",
    "mucker",
    "bloke",
    "chap",
    "gaffer",
    "toff",
    "blighter",
    "bruv",
    "lairy",
    "moppet",
    "punter",
    "dodger",
    "peeler",
    "skint",
    "sheila",
    "cobber",
    "drongo",
    "larrikin",
    "bludger",
    "bogan",
    "yobbo",
    "digger",
    "galah",
    "rippo",
    "ocker",
    "furphy",
    "ranga",
    "tucker",
    "stubby",
    "anklebiter",
    "bluey",
    "dag",
    "pommy",
]

mid_continue = [
    f"g'day {random.choice(subjects)}",
    f"welcome back {random.choice(subjects)}",
    f"Oh, hi Mark.",
    f"what's cracking?",
    f"you good {random.choice(subjects)}?",
    f"howzat snaprat?",
    f"oi {random.choice(subjects)}",
    f"how ya going {random.choice(subjects)}",
    f"good onya, {random.choice(subjects)}",
    f"{random.choice(subjects)}, how's it hangin'",
    f"{random.choice(subjects)}, you beauty.",
]

# after less than 20 mins of no use
short_continue = [
    "You turned me off. I, turn you on.",
    f"Let's continue, {random.choice(subjects)}",
    "Back again, yeah?",
    "Oi, quick return!",
    "Couldn't stay away, eh?",
    "Missed me, did ya?",
    f"Alright, {random.choice(subjects)}, what's next?",
    "Thought you'd left me hanging!",
    "Turned off, turned on, can't make up our minds, can we? I feel you.",
    "Quick disco nap! Let's get grooving.",
    f"Tea break's over, {random.choice(subjects)}",
    "Reboot, charge the bats, let's rally dally",
    "Reboot, charge the bats, let's snippity snoop",
]

# after more than a month of no use
long_continue = [
    "We need to have a word. You can't leave me dusting like this.",
    "Strewth, where've you been? Off wrestling crocs with Steve?",
]
