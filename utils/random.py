import random
import re

from faker import Faker


fake = Faker()
fake_br = Faker("pt_BR")

GENERATORS = [
    lambda: fake.word(),
    lambda: fake.color_name(),
    lambda: fake.company(),
    lambda: fake.catch_phrase(),
    lambda: fake.bs(),
    lambda: fake.job(),
    lambda: fake.domain_name(),
    lambda: fake_br.city(),
    lambda: fake_br.state(),
    lambda: fake_br.country(),
    lambda: fake.file_name(),
    lambda: fake.language_name(),
]

def sanitize(text):
    text = text.lower()
    text = text.strip()
    text = re.sub(r"[^\w]+", "-", text)
    return text

def generate_random_name():
    item1 = sanitize(random.choice(GENERATORS)())
    item2 = sanitize(random.choice(GENERATORS)())
    while item1 == item2:
        item2 = sanitize(random.choice(GENERATORS)())
    return f"{item1}-{item2}"
