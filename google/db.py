# -*- coding: utf-8 -*-

import boto3

# DynamoDB
class Dynamo(object):
    def __init__(self, table_name, key_schema=None, attribute_definitions=None, 
                 provisioned_throughput=None, local_mode=False):
        
        # 接続
        if local_mode:
            self.resource = boto3.resource(
                "dynamodb",
                region_name = "ap-northeast-1.",
                endpoint_url = "http://localhost:8000",
                aws_access_key_id = "ACCESS_ID",
                aws_secret_access_key = "ACCESS_KEY"
            )
        else:
            self.resource = boto3.resource("dynamodb")
        
        # テーブル接続
        if self._exists_table(table_name)==False: 
            # テーブル作成
            self.table = self.resource.create_table(
                TableName = table_name,
                KeySchema = key_schema,
                AttributeDefinitions = attribute_definitions,
                ProvisionedThroughput = provisioned_throughput
            )
        else:
            self.table = self.resource.Table(name=table_name)
    
    # リージョンの違うテーブルは存在確認できないかも...
    def _exists_table(self, table_name):
        return self.resource.Table(name=table_name) in self.resource.tables.all()
    
    def show_tables(self):
        for table in self.resource.tables.all(): print(table)
    
    def delete_table(self, table_name):
        self.resource.Table(name=table_name).delete()
    
    def put_items(self, item_list):
        with self.table.batch_writer() as batch:
            for item in item_list: batch.put_item(Item=item)
    
    def scan(self, filter_expression):
        result = self.table.scan(FilterExpression=filter_expression)
        return result["Items"]
    
    def query(self, key_condition_expression):
        result = self.table.query(KeyConditionExpression=key_condition_expression)
        return result["Items"]
        
