import uuid
import boto3
from utils import utility
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any


class Dynamo:
    def __init__(self, region_name: str):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.client = boto3.client('dynamodb', region_name=region_name)

    def create_table(self,
                     table_name: str,
                     key_schema: List[Dict[str, str]],
                     attribute_definitions: List[Dict[str, str]],
                     provisioned_throughput: Optional[Dict[str, int]] = None) -> bool:
        try:
            if not provisioned_throughput:
                provisioned_throughput = {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }

            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                ProvisionedThroughput=provisioned_throughput
            )
            table.wait_until_exists()
            return True
        except ClientError as e:
            print(f"Error creating table: {e}")
            return False

    def list_tables(self) -> List[str]:
        try:
            return self.client.list_tables()['TableNames']
        except ClientError as e:
            print(f"Error listing tables: {e}")
            return []

    def describe_table(self, table_name: str) -> Dict:
        try:
            return self.client.describe_table(TableName=table_name)
        except ClientError as e:
            print(f"Error describing table: {e}")
            return {}

    def table_exists(self, table_name: str) -> bool:
        try:
            self.client.describe_table(TableName=table_name)
            return True
        except ClientError:
            return False

    def delete_table(self, table_name: str) -> bool:
        try:
            table = self.dynamodb.Table(table_name)
            table.delete()
            table.wait_until_not_exists()
            return True
        except ClientError as e:
            print(f"Error deleting table: {e}")
            return False

    def add_item(self, table_name: str, partition_key: str, item: Dict[str, Any], auto_id: bool = True) -> str:
        try:
            table = self.dynamodb.Table(table_name)
            if auto_id and 'id' not in item:
                item[partition_key] = str(uuid.uuid4())

            item['created_at'] = utility.get_formatted_timestamp()
            table.put_item(Item=item)
            return item.get('id', '')
        except ClientError as e:
            print(f"Error adding item: {e}")
            return ""

    def get_item(self, table_name: str, key: Dict[str, Any]) -> Dict:
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item', {})
        except ClientError as e:
            print(f"Error getting item: {e}")
            return {}

    def update_item(self, table_name: str, key: Dict[str, Any], update_attrs: Dict[str, Any]) -> bool:
        try:
            table = self.dynamodb.Table(table_name)

            update_expr_parts = []
            expr_attr_values = {}
            expr_attr_names = {}

            for attr_name, value in update_attrs.items():
                attr_parts = attr_name.split('.')
                update_name = '#' + '_'.join(attr_parts)
                expr_attr_names[update_name] = attr_parts[-1]

                value_key = ':' + '_'.join(attr_parts)
                update_expr_parts.append(f"{update_name} = {value_key}")
                expr_attr_values[value_key] = value

            update_expr_parts.append('#updated_at = :updated_at')
            expr_attr_names['#updated_at'] = 'updated_at'
            expr_attr_values[':updated_at'] = utility.get_formatted_timestamp()

            update_expression = 'SET ' + ', '.join(update_expr_parts)

            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expr_attr_values,
                ExpressionAttributeNames=expr_attr_names
            )
            return True
        except ClientError as e:
            print(f"Error updating item: {e}")
            return False

    def delete_item(self, table_name: str, key: Dict[str, Any]) -> bool:
        try:
            table = self.dynamodb.Table(table_name)
            table.delete_item(Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting item: {e}")
            return False

    def query_items(self,
                    table_name: str,
                    key_condition_expression: str,
                    expression_values: Dict[str, Any],
                    index_name: Optional[str] = None,
                    filter_expression: Optional[str] = None,
                    limit: Optional[int] = None) -> List[Dict]:
        """
        Query items from the table

        Args:
            table_name: Name of the table
            key_condition_expression: KeyConditionExpression for the query
            expression_values: Dictionary of expression values
            index_name: Optional secondary index name
            filter_expression: Optional filter expression
            limit: Optional limit for results
        """
        try:
            table = self.dynamodb.Table(table_name)
            params = {
                'KeyConditionExpression': key_condition_expression,
                'ExpressionAttributeValues': expression_values
            }

            if index_name:
                params['IndexName'] = index_name
            if filter_expression:
                params['FilterExpression'] = filter_expression
            if limit:
                params['Limit'] = limit

            response = table.query(**params)
            return response.get('Items', [])
        except ClientError as e:
            print(f"Error querying items: {e}")
            return []

    def scan_items(self,
                   table_name: str,
                   filter_expression: Optional[str] = None,
                   expression_values: Optional[Dict[str, Any]] = None,
                   limit: Optional[int] = None) -> List[Dict]:
        """
        Scan items from the table

        Args:
            table_name: Name of the table
            filter_expression: Optional filter expression
            expression_values: Optional dictionary of expression values
            limit: Optional limit for results
        """
        try:
            table = self.dynamodb.Table(table_name)
            params = {}

            if filter_expression:
                params['FilterExpression'] = filter_expression
            if expression_values:
                params['ExpressionAttributeValues'] = expression_values
            if limit:
                params['Limit'] = limit

            response = table.scan(**params)
            return response.get('Items', [])
        except ClientError as e:
            print(f"Error scanning items: {e}")
            return []