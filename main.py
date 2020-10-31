from src.Patreon import Patreon

ACCESS_TOKEN = None

# Read patreon.key
with open("patreon.key", "r") as key_file:
    ACCESS_TOKEN = key_file.readline()

if not ACCESS_TOKEN:
    assert False, "Invalid access token."


if __name__ == "__main__":
    Patreon(ACCESS_TOKEN).loop()
