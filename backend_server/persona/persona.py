from persona.memory_modules.direct_memory import *


class Persona:
    def __init__(self, name, saved_path):
        self.name = name

        direct_memory_path = f"{saved_path}/direct_memory.json"
        self.direct_mem = DirectMemory(direct_memory_path)
