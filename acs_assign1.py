import boto3
import os
from dotenv import load_dotenv
from datetime import datetime

#load the .env file
load_dotenv() 

#retrieving the constants on .env
KEY_NAME = os.environ['AWS_KEY_NAME']
SECURITY_GROUP_ID = os.environ['AWS_SECURITY_GROUP_ID']

#user data script
user_data_script = """#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd

TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/instance-id)
PRIVATE_IP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/local-ipv4)
AVAILABILITY_ZONE=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
AMI_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/ami-id)
SECURITY_GROUPS=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/security-groups)



echo '<h1>EC2 Instance Metadata Display João Victor Godoy da Silva</h1>' >> /var/www/html/index.html
echo '<h2><strong>Instance ID:</strong> '$INSTANCE_ID'</h2>' >> /var/www/html/index.html
echo '<h2><strong>Private IP:</strong> '$PRIVATE_IP'</h2>' >> /var/www/html/index.html
echo '<h2><strong>Availability Zone:</strong> '$AVAILABILITY_ZONE'</h2>' >> /var/www/html/index.html
echo '<h2><strong>Security Groups:</strong> '$SECURITY_GROUPS'</h2>' >> /var/www/html/index.html
echo '<h2><strong>AMI ID:</strong> '$AMI_ID'</h2>' >> /var/www/html/index.html
"""
#initialize EC2 connections
ec2_resource = boto3.resource('ec2', region_name='us-east-1')
ec2_client = boto3.client('ec2', region_name='us-east-1')

#create instance
new_instances = ec2_resource.create_instances(
    ImageId='ami-04752fceda1274920',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.nano',
    KeyName= KEY_NAME,
    SecurityGroupIds=[SECURITY_GROUP_ID],
    UserData=user_data_script,
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

instance = new_instances[0]
instance.wait_until_running()
instance.reload()
print("instance is running")

#usign client to ensure that the status of the instance is ok
#print(ec2_client.waiter_names) command that is used to see the list of avaible waiters names
waiter = ec2_client.get_waiter('instance_status_ok')
waiter.wait(InstanceIds=[instance.id])
print(f"\nAccess your website at: http://{instance.public_ip_address}")

#creating AMI
initials = "JV"
timestamp = datetime.now().strftime("%Y-%m-%d%f") #datetime library was used to get the milesseconds
ami_name = initials+"-"+timestamp

image = instance.create_image(
    Name=ami_name,
    Description=f"AMI - timestamp: {timestamp}"
)

print("Image created, waiting for it get available")

waiter_image = ec2_client.get_waiter('image_available')
waiter_image.wait(ImageIds=[image.id])
print(f"\nAMI created: {ami_name} ({image.id})")