import requests
import logging

logger = logging.getLogger(__name__)

ADSGRAM_BLOCK_ID = "48075"
ADSGRAM_TOKEN = "1db5e307dbeb48aea7ff2f130e11f7f1"
ADSGRAM_API = "https://api.adsgram.ai/advbot"


def get_ad(user_id, lang="en"):
    try:
        params = {
            "tgid": str(user_id),
            "blockid": ADSGRAM_BLOCK_ID,
            "token": ADSGRAM_TOKEN,
            "language": lang,
        }
        r = requests.get(ADSGRAM_API, params=params, timeout=15)
        if r.status_code != 200:
            logger.error("Adsgram HTTP " + str(r.status_code))
            return None
        data = r.json()
        if not data.get("ok"):
            return None
        return data.get("ad")
    except Exception as e:
        logger.error("Adsgram: " + str(e))
        return None
