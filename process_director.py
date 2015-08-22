__author__ = 'Dany'


class ProcessDirector:
    """
    example usage:
    IDS = ["ID12345", "ID01234"]
    director = ProcessDirector()
    for id in IDS:
        director.construct(id, idClass)
    """
    def __init__(self):
        self.allClasses = []

    def construct(self, buildername, class_type):
        targetclass = getattr(class_type, buildername)
        instance = targetclass()
        self.allClasses.append(instance)
        return instance

