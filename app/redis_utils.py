import redis
import hashlib

from app_logger import logger

r = redis.Redis(host='localhost', port=6379, db=0)


def hash_key(input_text, source_lang, target_lang):
    key = input_text + ":" + source_lang + ":" + target_lang
    hash_object = hashlib.sha512(key.lower().encode())
    hex_dig_key = hash_object.hexdigest()
    return hex_dig_key


def set_translated_text(input_text, source_lang, target_lang, output_text):
    redis_key = hash_key(input_text, source_lang, target_lang)
    logger.debug("Caching the message in redis")
    r.set(redis_key, output_text)

    # UNO REVERSE
    redis_key = hash_key(output_text, target_lang, source_lang)
    r.set(redis_key, input_text)


def get_translated_text(input_text, source_lang, target_lang):
    redis_key = hash_key(input_text, source_lang, target_lang)
    value = r.get(redis_key)
    if value:
        logger.debug("Found the message in redis cache")
        return value.decode()
    return None

# Main block

# input_text = "Hello"
# source_lang = "en"
# target_lang = "fr"
# output_text = "Bonjour"
# keyRedis = setMethod(input_text,source_lang,target_lang,output_text)
# print(keyRedis)

# valueRedis= getMethod(input_text,source_lang,target_lang)

# if valueRedis :
#    print(valueRedis)
# else :
#    print("key not found")
