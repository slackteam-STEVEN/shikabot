# -*- coding: utf-8 -*-

import time
from slacker import Slacker
import arxiv_abst_getter

API_TOKEN   = "XXX"
TABLE_NAME  = "paper_contents"
AWS         = True

CHANNEL     = "state-of-the-art"
INSERT_DB   = True

def lambda_handler(event, context):
    contents = arxiv_abst_getter.get_abst(insert_db=INSERT_DB, table_name=TABLE_NAME, aws=AWS)
    slack = Slacker(API_TOKEN)
    slack.chat.post_message(CHANNEL, "こんにちは!", as_user=True)
    time.sleep(5)
    slack.chat.post_message(CHANNEL, f"\nほいよ、これ本日のarXiv最新機械学習論文ね↓\n\n{contents}", as_user=True)

