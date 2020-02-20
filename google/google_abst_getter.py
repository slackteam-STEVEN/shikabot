# -*- coding: utf-8 -*-

import os
import time
from urllib.request import urlopen
from selenium import webdriver
from db import Dynamo
from boto3.dynamodb.conditions import Attr, Key
from common import *

SECONDS  = 20
AREA     = "machine-intelligence"
HOME_URL = "https://research.google"
ML_URL   = f"pubs/?area={AREA}"

SECONDS_PHANTOMJS = 15


PI_RM_LIST = ["\n"]
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


def html_read_phantomjs(url, local_mode):
    if local_mode:
        executable_path="phantomjs"
    else:
        executable_path="./phantomjs"
    
    driver = webdriver.PhantomJS(service_log_path=os.path.devnull, executable_path=executable_path)
    driver.get(url)
    time.sleep(SECONDS_PHANTOMJS)
    return html_read(driver.page_source.encode('utf-8'))
    

def get_paper_contents(bsobj, title, area):
    # 著者の文字列を取得
    authors = bsobj.findAll("div",{"class":"hero__wrapper"})[0].findAll("ul")[0].text.split("\n")
    authors = ",".join([author for author in authors if author!=""])
    
    # 出版情報を取得
    publication_info = bsobj.findAll("div",{"class":"hero__wrapper"})[0].findAll("div",{"class":"venue"})[0].text
    publication_info = str_clean(publication_info, PI_RM_LIST)
    
    # pdfのurlを取得
    pdf_url_list = bsobj.findAll("section",{"class":"copy copy-- links has-grey-background"})[0].findAll("a",{"class":"button button--light"})
    if len(pdf_url_list)>0:
        pdf_url = pdf_url_list[0].get('href')
        
        if "https:" not in pdf_url: pdf_url = f"{HOME_URL}{pdf_url}"
            
    else:
        pdf_url = "-"
    
    # アブストの文字列を取得
    abstract = bsobj.findAll("section",{"class":"copy copy--side"})[0].findAll("div",{"class":"content__body"})[0].text    
    abstract = str_clean_brank(abstract, ABST_RM_LIST)
    
    # ドキュメント初期化
    document = {}
    
    # ドキュメントへ格納
    document["series"]           = area
    document["title"]            = title
    document["pdf_url"]          = pdf_url
    document["auther"]           = authors
    document["publication_info"] = publication_info
    document["abstract"]         = abstract
    document["affiliation"]      = "google"
    
    # 出力
    return document


def dict2str(doc):
    result = f"タイトル: {doc['title']}\n"
    result += f"著者: {doc['auther']}\n"
    result += f"所属: {doc['affiliation']}\n"
    result += f"出版情報: {doc['publication_info']}\n"
    result += f"Abstract:\n{doc['abstract']}\n"
    result += f"全文pdfのURL: {doc['pdf_url']}\n"
    return result


def get_abst(insert_db, table_name, local_mode):
    # DBに入れる場合DBに接続
    if insert_db: 
        dynamo = Dynamo(table_name=table_name, key_schema=KEY_SCHEMA, 
                        attribute_definitions=ATTRIBUTE_DEFINITIONS, 
                        provisioned_throughput=PROVISIONED_THROUGHPUT, local_mode=local_mode)
        
        # db上のテーブルタイトル一覧取得
        exist_titles = [dic["title"] for dic in dynamo.scan(filter_expression=Attr("title").ne("xxx"))]

    
    # スクレイピング実行(指定時間ストップ)
    bsobj = html_read_phantomjs(f"{HOME_URL}/{ML_URL}", local_mode)
    time.sleep(SECONDS)
    
    # htmlからタグdtのみ取り出す
    paper_info_list = bsobj.findAll("a",{"class":"card__link ng-scope"})
    
    for i in range(len(paper_info_list)):
        # タイトル取得
        tmp_title = paper_info_list[i].text
        
        # 同タイトルの論文がDB上にあるか確認
        if insert_db: 
            is_exist = (tmp_title in exist_titles)
            
        else:
            is_exist = False
        
        # 同タイトルの論文がなかった場合,ドキュメントをDBへ保存し発言
        if is_exist == False:
            # htmlからタグ[a]のみ取り出す
            a_list = paper_info_list[i].findAll("a")
            
            # アブストとpdfのURL取得
            abs_url = f"{HOME_URL}{paper_info_list[i].get('href')}"
            
            # スクレイピング実行(指定時間ストップ)
            bsobj = html_read(urlopen(abs_url))
            
            # 論文内容を取得
            document = get_paper_contents(bsobj, tmp_title, AREA)
            
            # DBに入れる場合
            if insert_db: dynamo.put_items([document])

            break
            
    # 出力
    return dict2str(document)
      
