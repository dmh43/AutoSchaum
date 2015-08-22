__author__ = 'Dany'


class ProcessDirector:
    """
    example usage:
    IDS = ["ID12345", "ID01234"]
    director = ProcessDirector()
    for id in IDS:
        director.construct(id)
    """
    def __init__(self):
        self.allClasses = []

    def construct(self, builderName, class_type):
        targetClass = getattr(class_type, builderName)
        instance = targetClass()
        self.allClasses.append(instance)

