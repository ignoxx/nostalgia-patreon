import patreon

ACCESS_TOKEN = None


# Read patreon.key
with open("patreon.key", "r") as key_file:
    ACCESS_TOKEN = key_file.readline()

if not ACCESS_TOKEN:
    assert False, "Invalid access token."


class PatreonResponse:
    def __init__(self, username, status, mail):
        self.username = username
        self.mail = mail
        self.status = status


class Patreon:
    def __init__(self, access_token):
        self.api_client = patreon.API(access_token)
        self.campaign_response = self.api_client.fetch_campaign()
        self.campaign_id = self.campaign_response.data()[0].id()

    def get_patreons(self):
        all_pledges = []
        cursor = None

        # fetch all pledges
        while True:
            pledges_response = self.api_client.fetch_page_of_pledges(
                self.campaign_id,
                50,
                cursor=cursor,
                fields={
                    "pledge": [
                        "total_historical_amount_cents",
                        "declined_since",
                        "is_paused",
                        "currently_entitled_tiers",
                    ]
                },
            )
            cursor = self.api_client.extract_cursor(pledges_response)
            all_pledges += pledges_response.data()
            if not cursor:
                break

        # fetch all patreons
        patreon_list = []
        for pledge in all_pledges:
            declined = (
                pledge.attribute("declined_since")
                or pledge.attribute("is_paused") == "true"
            )
            reward_tier = 0

            if pledge.relationships()["reward"]["data"]:
                reward_tier = pledge.relationship("reward").attribute("amount_cents")

            mail = pledge.relationship("patron").attribute("email")
            username = mail.split("@")[0]

            if not declined and reward_tier >= 300:
                patreon_list.append(
                    PatreonResponse(
                        username=username,
                        mail=mail,
                        status="ACTIVE",
                    )
                )
            elif declined and reward_tier >= 300:
                patreon_list.append(
                    PatreonResponse(
                        username=username,
                        mail=mail,
                        status="INACTIVE",
                    )
                )
            elif reward_tier >= 300:
                patreon_list.append(
                    PatreonResponse(
                        username=username,
                        mail=mail,
                        status="EVALUATE",
                    )
                )

        patreon_list_sorted = sorted(
            patreon_list,
            key=lambda patreon: [
                patreon.status == "ACTIVE" or patreon.status == "EVALUATE"
            ],
            reverse=True,
        )

        return patreon_list_sorted


p = Patreon(ACCESS_TOKEN)
all_patrons = p.get_patreons()
for patron in all_patrons:
    print(patron.mail, "--", patron.status)
