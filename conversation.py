class ConversationManager:
    def __init__(self):
        self.history:    list = []
        self.turn_count: int  = 0

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if role == "user":          # ユーザーの送信回数でカウント
            self.turn_count += 1

    def is_feedback_time(self) -> bool:
        return self.turn_count >= 3

    def reset(self) -> None:
        self.history    = []
        self.turn_count = 0

    def get_history(self) -> list:
        return self.history
