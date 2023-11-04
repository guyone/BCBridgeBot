import random


class ComedyGenerator:
    def __init__(self):
        self.canadian_comedians = ["Jim Carrey", "Mike Myers", "Will Arnett"]
        self.type_of_joke = ['Ace Ventura', 'Austin Powers', 'Dumb and Dumber', 'Arrested Development', 'Brooklyn Nine-Nine', 'The Office']
        # Bridge-related prompts
        self.bridge_fact_prompts = [
            "Generate a 1 sentence random fact about a bridge in British Columbia.",
            "Generate a 1 sentence random fact about a bridge in the Okanagan.",
            "Generate a 1 sentence random fact about a bridge in Northern British Columbia.",
            "Generate a 1 sentence random fact about bridging gaps in British Columbia in a good way for society.",
            "Generate a 1 sentence random fact about the word 'bridge'.",
            "Tell in in a funny joking way that on July 18, 2022 AND 2023 there were incidents of a truck hitting an overpass.",
            "Tell in in a funny joking way that on June 8, 2022 there were 2 incidents of a truck hitting an overpass in the same day.",
        ]

        # BC-related prompts
        self.bc_related_prompts = [
            "Generate a 1 sentence unique fact about the geography of British Columbia.",
            "Generate a 1 sentence fact about how British Columbia contributes to Canada's economy.",
            "Generate a 1 sentence description of a famous historical event that took place in British Columbia.",
            "Generate a 1 sentence fun fact about British Columbia's wildlife.",
            "Generate a 1 sentence must-see tourist attraction in British Columbia.",
            "Generate a 1 sentence fact about a famous person from British Columbia.",
            "Generate a 1 sentence description of a popular food or dish that originated in British Columbia.",
            "Generate a 1 sentence tradition or festival celebrated in British Columbia.",
            "Generate a 1 sentence notable technological innovation that came from British Columbia.",
            "Generate a 1 sentence description of a famous landmark in British Columbia.",
            "Generate a 1 sentence interesting fact about British Columbia's indigenous culture.",
            "Generate a 1 sentence role of British Columbia in Canadian politics.",
            "Generate a 1 sentence funny anecdote or joke related to British Columbia.",
            "Generate a 1 sentence impact of British Columbia on Canadian arts and culture.",
            "Generate a 1 sentence surprising fact about British Columbia's climate.",
        ]

    def select_comedian(self):
        return random.choice(self.canadian_comedians)

    def select_joke_type(self):
        return random.choice(self.type_of_joke)