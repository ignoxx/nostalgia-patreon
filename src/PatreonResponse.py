class PatreonResponse:
    def __init__(self, username, mail, reward_tier, created_at):
        self.username = username
        self.mail = mail
        self.reward_tier = reward_tier
        self.created_at = created_at
