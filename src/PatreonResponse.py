class PatreonResponse:
    def __init__(self, username, mail, reward_tier, created_at, declined=False):
        self.username = username
        self.mail = mail
        self.reward_tier = reward_tier
        self.created_at = created_at
        self.declined = declined

    def is_valid(self):
        return self.declined == False and self.reward_tier > 0
