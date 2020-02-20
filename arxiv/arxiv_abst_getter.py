# -*- coding: utf-8 -*-

import time
from urllib.request import urlopen
from db import Dynamo
from boto3.dynamodb.conditions import Attr
from common import *

SECONDS  = 20
AREA     = "machine-learning"
HOME_URL = "https://arxiv.org"
ML_URL   = "list/cs.LG/recent"

TITLE_RM_LIST = ["Title:", "\n"]
AUTHERS_RM_LIST = ["Authors:", "\n"]
SUBMIT_DATE_RM_LIST = ["\n  \n  \n  \n    \n  \n  \n    \n    \n  \n\n  ", "(", ")", "Submitted on "] 
ABST_RM_LIST = ["Abstract:  ", "\n"]

# dynamo設定
KEY_SCHEMA = [
    {
        'AttributeName': 'series',
        'KeyType': 'HASH'
    },
    {
        'AttributeName': 'title',
        'KeyType': 'RANGE'
    },
]
ATTRIBUTE_DEFINITIONS  = [
    {
        'AttributeName': 'series',
        'AttributeType': 'S'
    },
    {
        'AttributeName': 'title',
        'AttributeType': 'S'
    }
]
PROVISIONED_THROUGHPUT = {
    'ReadCapacityUnits': 1,
    'WriteCapacityUnits': 1
}

def get_paper_contents(bsobj, title, pdf_url, area):
    # 著者の文字列を取得
    authors = bsobj.findAll("div",{"class":"authors"})[0].text
    authors = str_clean(authors, AUTHERS_RM_LIST)
    
    # 投稿日の文字列を取得
    submit_date = bsobj.findAll("div",{"class":"dateline"})[0].text
    submit_date = str_clean(submit_date, SUBMIT_DATE_RM_LIST)
    
    # アブストの文字列を取得
    abstract = bsobj.findAll("blockquote",{"class":"abstract mathjax"})[0].text
    abstract = str_clean_brank(abstract, ABST_RM_LIST)
    
    # ドキュメント初期化
    document = {}
    
    # ドキュメントへ格納
    document["series"]      = area
    document["title"]       = title
    document["pdf_url"]     = pdf_url
    document["auther"]      = authors
    document["submit_date"] = submit_date
    document["abstract"]    = abstract
    
    # 出力
    return document


def dict2str(doc):
    result = f"タイトル: {doc['title']}\n"
    result += f"著者: {doc['auther']}\n"
    result += f"論文投稿日: {doc['submit_date']}\n"
    result += f"Abstract:\n{doc['abstract']}\n"
    result += f"全文pdfのURL: {doc['pdf_url']}\n"
    return result


def get_abst(insert_db, table_name, aws):
    # DBに入れる場合DBに接続
    if insert_db: 
        dynamo = Dynamo(table_name=table_name, key_schema=KEY_SCHEMA, 
                        attribute_definitions=ATTRIBUTE_DEFINITIONS, 
                        provisioned_throughput=PROVISIONED_THROUGHPUT, aws=aws)
    
    # スクレイピング実行(指定時間ストップ)
    bsobj = html_read(urlopen(f"{HOME_URL}/{ML_URL}").read())
    time.sleep(SECONDS)
    
    # htmlからタグdtのみ取り出す
    paper_info_list = bsobj.findAll("dt")
    paper_title_list = bsobj.findAll("dd")
    
    for i in range(len(paper_title_list)):
        # タイトル取得
        tmp_title = paper_title_list[i].findAll("div",{"class":"list-title mathjax"})[0].text
        tmp_title = str_clean(tmp_title, TITLE_RM_LIST)
        tmp_title = tmp_title.strip(" ").replace("  ", " ")
        
        # 同タイトルの論文がDB上にあるか確認
        if insert_db: 
            is_exist = (len(dynamo.scan(filter_expression=Attr("title").eq(tmp_title))) > 0)
        else:
            is_exist = False
        
        # 同タイトルの論文がなかった場合,ドキュメントをDBへ保存し発言
        if is_exist == False:
            # htmlからタグ[a]のみ取り出す
            a_list = paper_info_list[i].findAll("a")
            
            # アブストとpdfのURL取得
            abs_url = f"{HOME_URL}{a_list[1].get('href')}"
            pdf_url = f"{HOME_URL}{a_list[2].get('href')}"
            
            # スクレイピング実行(指定時間ストップ)
            bsobj = html_read(urlopen(abs_url).read())
            
            # 論文内容を取得
            document = get_paper_contents(bsobj, tmp_title, pdf_url, AREA)
            
            # DBに入れる場合
            if insert_db: dynamo.put_items([document])
            
            break
            
    # 出力
    return dict2str(document)
      
