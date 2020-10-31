import configparser
from datetime import datetime
from time import sleep

import patreon

from src.PatreonResponse import PatreonResponse

FILE_OUTPUT = "patrons.ini"  # path
UPDATE_FREQUENCY = 30 * 60  # every 30 minutes


class Patreon:
    def __init__(self, access_token):
        self.api_client = patreon.API(access_token)
        self.campaign_response = self.api_client.fetch_campaign()
        self.campaign_id = self.campaign_response.data()[0].id()
        self.last_refresh = datetime.now()
        self.patrons = []

    def loop(self):
        while True:
            self.write_ini()
            sleep(UPDATE_FREQUENCY)

    def get_all_active_patrons(self):
        if (
            not self.patrons
            or (datetime.now() - self.last_refresh).seconds > UPDATE_FREQUENCY
        ):
            self.patrons = self.get_patreons()

        return self.patrons

    def refresh_patrons(self):
        self.patrons = self.get_patreons()
        self.last_refresh = datetime.now()

    def write_ini(self):
        patrons = self.get_all_active_patrons()

        if not patrons:
            return

        section = "EMAIL"

        config = configparser.ConfigParser()
        config.add_section(section)
        for p in patrons:
            config.set(section, p.mail, str(p.reward_tier))

        config.add_section("STATS")
        config.set("STATS", "amount", str(len(patrons)))

        with open(FILE_OUTPUT, "w") as configfile:
            config.write(configfile)

    def get_patreons(self):
        try:
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
                    reward_tier = pledge.relationship("reward").attribute(
                        "amount_cents"
                    )

                mail = pledge.relationship("patron").attribute("email")
                username = mail.split("@")[0]

                # collect only valid patrons
                if not declined and reward_tier > 0:
                    patreon_list.append(
                        PatreonResponse(
                            username=username, mail=mail, reward_tier=reward_tier
                        )
                    )

            return patreon_list

        except Exception as e:
            return []
