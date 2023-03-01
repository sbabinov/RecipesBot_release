import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
QIWI_TOKEN = str(os.getenv("QIWI_TOKEN"))

admins = [
    1005532278,
]
