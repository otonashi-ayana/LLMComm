class Place:
    def __init__(self, name):
        self.name = name
        self.members = []
        self.shared_memory = []

    def add_member(self, member):
        """添加成员到场所"""
        self.members.append(member)
        print(f"{member.name} 来到了 {self.name}。")

    def remove_member(self, member):
        """从场所移除成员"""
        if member in self.members:
            self.members.remove(member)
            print(f"{member.name} 离开了 {self.name}。")
