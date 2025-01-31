import sys

sys.path.append("../../")


class ConceptNode:
    def __init__(self, s, p, o, desc):
        # self.concept = None
        self.subject = s
        self.predicate = p
        self.object = o
        self.description = desc

    def spo_summary(self):
        return (self.subject, self.predicate, self.object)


# def add_event(self,created_time,):
#     # node_count = len()
#     node_type = "event"
#     # node_type_count = len()
#     node = ConceptNode(node_type,
#                        self.subject,
#                        self.predicate,
#                        self.object,
#                        self.description)
