
from collections import namedtuple

from datetime import datetime
import boto3

ec2 = boto3.client('ec2')

email_client = boto3.client('ses')

dynamodb_client = boto3.client('dynamodb')

TABLE_NAME = "test"

HOUR_LIMIT = 6

TAGS_TO_SEARCH = ["Name", "Environment"]


def send_email(email_address, body, head):
    '''Sends mail to the given email address with given body and subject line'''
    body_html = f"""<html>
    <head></head>
    <body>
      <h2>Your EC2 instance is missing a tag</h2>
      <br/>
      <p>{body}</p> 
    </body>
    </html>
                """

    email_message = {
        'Body': {
            'Html': {
                'Charset': 'utf-8',
                'Data': body_html,
            },
        },
        'Subject': {
            'Charset': 'utf-8',
            'Data': head,
        },
    }
    ses_response = email_client.send_email(
    Destination={
        'ToAddresses': ['zainkhan1june@gmail.com'],
    },
    Message=email_message,
    Source="zainkhanjune@gmail.com",
    )
    print(ses_response)
    print("sending email to ", email_address)



def discontinue_instance(instance_id):
    '''To stop the ec2 instance for a given list of instance id's'''
    if(len(instance_id) == 0):
        return
    ec2.stop_instances(InstanceIds=instance_id)



def create_table():
    '''Method to create table if the table does not exists already'''
    try:
        dynamodb_client.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'InstanceId',
                    'AttributeType': 'S',
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'InstanceId',
                    'KeyType': 'HASH',
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5,
            },
            TableName= TABLE_NAME,
        )
    except dynamodb_client.exceptions.ResourceInUseException as ex:
        print("Table already exists" , ex)


def get_instance_status():
    '''Method to get the status instance for each ec2 instance'''
    all_instances = ec2.describe_instances()
    
    instances_status = []
    
    print(all_instances)

    
    
    Status = namedtuple("Status", "instance_id created_by missing_tags")
    for reservations in all_instances["Reservations"]:
        instances = reservations["Instances"]
        for instance in instances:
            if(instance["State"]["Name"] != "running"):
                continue
            instance_id = instance["InstanceId"]
            created_by = None
            missing_tags = set(TAGS_TO_SEARCH)
            for tags in instance["Tags"]:
                missing_tags.discard(tags["Key"])
                if(tags["Key"] == "created_by"):
                    created_by = tags["Value"]
            new_status = Status(instance_id, created_by, missing_tags)
            instances_status.append(new_status)
            
    return instances_status
    

def generate_body(text, missing_tags, instance_id):
    '''Generate body for email depending upon the tags missing'''
    missing_tags = list(missing_tags)
    return  f"Instances tags {','.join(missing_tags)}  are missing on the EC2 instance {instance_id}. {text} "
    



def remove_from_db(table_data):
    '''Method to delete data in bulk from the database hence optimising the remove query'''
    items = {TABLE_NAME:[ {'DeleteRequest': { 'Key': {'InstanceId': { 'S': instance_id } } }} for instance_id in table_data ]}
    print(table_data, " to be removed")
    dynamodb_client.batch_write_item(RequestItems=items)
    

def add_to_db(table_data):
    '''Method to add data in bulk to database to optimize the add query'''
    items = {TABLE_NAME:[ {'PutRequest': { 'Item': {'InstanceId': { 'S': instance_id },'LastUpdated': { 'S': update_time.isoformat() } } }} for instance_id, update_time in table_data ]}
    print(items)
    dynamodb_client.batch_write_item(RequestItems=items)


def lambda_handler(event, context):
    '''
    Main function to handle the incoming event request
    '''
    create_table()
    instances_status = get_instance_status()
    if(len(instances_status) == 0):
        return
    instances_id = {TABLE_NAME:{'Keys':[{'InstanceId':{'S':instance.instance_id}} for instance in instances_status]}}
    print(instances_id)
    response = dynamodb_client.batch_get_item(RequestItems=instances_id)
    instance_docs = response['Responses'][TABLE_NAME]
    print(instance_docs)
    in_db_instance = dict(
        (instance['InstanceId']['S'],
        instance['LastUpdated']['S']) for instance in instance_docs)
    to_be_removed = []
    to_be_added = []
    print(in_db_instance)

    print(in_db_instance)
    current_time = datetime.now()
    to_be_discontinued = []
    for status in instances_status:
        missing_tags = status.missing_tags
        created_by = status.created_by
        instance_id = status.instance_id
        if(len(missing_tags) != 0):
            if instance_id not in in_db_instance.keys():
                to_be_added.append((instance_id, current_time))
                body = generate_body(f"Please Update as soon as possible to avoid discontinuation. The Instance will be terminated automatically after {HOUR_LIMIT} hours",missing_tags, instance_id)
                send_email(created_by, body, "Alert EC2 Instance Missing Tag")
            else:
                time = in_db_instance[instance_id]
                emailed_time = datetime.fromisoformat(time)
                hour_elapsed = (current_time - emailed_time.replace(tzinfo=None)).total_seconds()//3600
                print(hour_elapsed)
                if(hour_elapsed >= HOUR_LIMIT):
                    to_be_removed.append(instance_id)
                    body = generate_body(f"Since Last {HOUR_LIMIT} hours have passed we are discontinuing your instance", missing_tags, instance_id)
                    to_be_discontinued.append(instance_id)
                    send_email(created_by, body, "EC2 instance discontinued")

    if(len(to_be_removed) > 0):
        remove_from_db(to_be_removed)
    if(len(to_be_added) > 0):
        add_to_db(to_be_added)

    discontinue_instance(to_be_discontinued)
            