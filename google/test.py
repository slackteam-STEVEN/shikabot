# -*- coding: utf-8 -*-

import os
import time
from slacker import Slacker
import google_abst_getter

API_TOKEN   = "XXX"
TABLE_NAME  = "paper_contents"
LOCAL_MODE  = True

CHANNEL     = "state-of-the-art"
INSERT_DB   = True

def lambda_handler(event, context):
    os.environ["OPENSSL_CONF"]="hoge"
    contents = google_abst_getter.get_abst(insert_db=INSERT_DB, table_name=TABLE_NAME, local_mode=LOCAL_MODE)
    slack = Slacker(API_TOKEN)
    slack.chat.post_message(CHANNEL, "こんばんは!", as_user=True)
    time.sleep(5)
    slack.chat.post_message(CHANNEL, f"\nほいよ、これ今夜のgoogle最新機械学習論文ね↓\n\n{contents}", as_user=True)


if __name__ == '__main__':
    lambda_handler(None, None)
    
# insert_db=INSERT_DB
# table_name=TABLE_NAME
# local_mode=LOCAL_MODE
