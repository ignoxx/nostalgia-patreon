import configparser
from datetime import datetime, timedelta
from pprint import pprint
from time import sleep

import patreon

from src.PatreonResponse import PatreonResponse

FILE_OUTPUT = "patrons.ini"  # path "C:/Users/admin/AppData/Local/SL2_server0/server_data/patrons.ini"
UPDATE_FREQUENCY = 30  # every 30 seconds


class Patreon:
    def __init__(self, access_token):
        self.api_client = patreon.API(access_token)
        self.campaign_response = self.api_client.fetch_campaign()
        self.campaign_id = self.campaign_response.data()[0].id()
        print("campaign id: " + self.campaign_id)
        self.last_refresh = datetime.now()
        self.patrons = []

    def loop(self):
        while True:
            self.update_patrons_ini()
            print(
                f"Fetched! Next refresh in {UPDATE_FREQUENCY} seconds ({datetime.now() + timedelta(seconds=UPDATE_FREQUENCY)})"
            )
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

    def update_patrons_ini(self):
        patreons = self.get_all_active_patrons()
        # first read current config
        config = configparser.ConfigParser()
        result = config.read(FILE_OUTPUT)

        if not result:
            # we didn't found an existing ini, lets create a new one
            config.add_section("TIERS")
            config.add_section("CREATED_AT")
            config.add_section("STATS")
            config.add_section("DECLINED")

            for patron in patreons:
                if not patron.is_valid():
                    config.set("DECLINED", patron.mail, str(patron.reward_tier))
                else:
                    config.set("TIERS", patron.mail, str(patron.reward_tier))
                config.set("CREATED_AT", patron.mail, str(patron.created_at))

            config.set("STATS", "amount", str(len(patreons)))
        else:
            # found existing one, lets update it
            # check if sections exists
            if not config.has_section("TIERS"):
                config.add_section("TIERS")

            if not config.has_section("CREATED_AT"):
                config.add_section("CREATED_AT")

            if not config.has_section("STATS"):
                config.add_section("STATS")

            if not config.has_section("DECLINED"):
                config.add_section("DECLINED")

            # update patrons in case they increased the tier
            for patron in patreons:
                # check if patron is available in both sections, if yes update him
                # if config.has_option("TIERS", patron.mail) and config.has_option("DECLINED", patron.mail):

                # check
                if (
                    config.has_option("TIERS", patron.mail)
                    and config.get("TIERS", patron.mail) == patron.reward_tier
                    and not patron.declined
                ):
                    continue
                else:
                    if not patron.is_valid():
                        config.set("DECLINED", patron.mail, str(patron.reward_tier))
                        if config.has_option("TIERS", patron.mail):
                            config.remove_option("TIERS", patron.mail)
                    else:
                        config.set("TIERS", patron.mail, str(patron.reward_tier))
                        if config.has_option("DECLINED", patron.mail):
                            config.remove_option("DECLINED", patron.mail)

                    config.set("CREATED_AT", patron.mail, str(patron.created_at))

            config.set("STATS", "amount", str(len(config.options("TIERS"))))

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
                )
                cursor = self.api_client.extract_cursor(pledges_response)
                all_pledges += pledges_response.data()
                if not cursor:
                    break

            # fetch all patreons
            patreon_list = []
            for pledge in all_pledges:

                declined = pledge.attribute("declined_since") != None
                reward_tier = pledge.relationship("reward").attribute("amount_cents")
                created_at = pledge.attribute("created_at")
                mail = pledge.relationship("patron").attribute("email")
                full_name = pledge.relationship("patron").attribute("full_name")
                username = mail.split("@")[0]

                patreon_list.append(
                    PatreonResponse(
                        username=username,
                        mail=mail,
                        reward_tier=reward_tier,
                        created_at=created_at,
                        declined=declined,
                    )
                )

            return patreon_list

        except Exception as e:
            return []
