class Option:
    def __init__(self, questionID: int, ID: int, option: str):
        self.questionID = questionID
        self.ID = ID
        self.option = option


class Question:
    def __init__(self, questionID: int, question: str, options: list[Option]):
        self.questionID = questionID
        self.question = question
        self.options = options
