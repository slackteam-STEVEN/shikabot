# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

def str_clean(string, rm_list):
    for tmp_str in rm_list: string = string.replace(tmp_str, "")
    return string

def str_clean_brank(string, rm_list):
    for tmp_str in rm_list: string = string.replace(tmp_str, " ")
    return string

def html_read(html):
    try:
        bsobj = BeautifulSoup(html)
        return bsobj
    except:
        print("error")

