import uuid


class DigitalHuman:
    def __init__(self, name, age, work, personality, background):
        self.id = str(uuid.uuid4())
        self.name = name
        self.age = age
        self.work = work
        self.personality = personality
        self.background = background
        self.place = None

    def __str__(self):
        return f"{self.name}，年龄：{self.age}，职业：{self.work}，性格：{self.personality}，背景故事：{self.background}"

    def join_place(self, place):
        if self.place:
            self.leave_place()
        self.place = place
        place.add_member(self)  # ?

    def leave_place(self):
        if self.place:
            self.place.remove_member(self)
            self.place = None
