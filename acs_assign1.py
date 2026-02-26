import boto3
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv() 

#retrieving the constants on .env
KEY_NAME = os.environ['AWS_KEY_NAME']
SECURITY_GROUP_ID = os.environ['AWS_SECURITY_GROUP_ID']

ec2_resource = boto3.resource('ec2', region_name='us-east-1')


new_instances = ec2_resource.create_instances(
    ImageId='ami-04752fceda1274920',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.nano',
    KeyName= KEY_NAME,
    SecurityGroupIds=[SECURITY_GROUP_ID],
    Placement={
        'AvailabilityZone': 'us-east-1b'},
    TagSpecifications=[{
        'ResourceType': 'instance',  
        'Tags': [                     
            {
                'Key': 'Name',        
                'Value': 'TestName' 
            },
            {
                'Key': 'Test',
                'Value': 'se apareceu, a tag ta funcionando'    
            }
        ]
    }]
    )

