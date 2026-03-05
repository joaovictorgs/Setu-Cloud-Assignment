import boto3
import os
from dotenv import load_dotenv
from datetime import datetime
import subprocess
import random    
import string  
import json 

#load the .env file
load_dotenv() 

#retrieving the constants on .env
KEY_NAME = os.environ['AWS_KEY_NAME']
KEY_FILE = f"{KEY_NAME}.pem"
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
#initialize EC2 and S3 connections
ec2_resource = boto3.resource('ec2', region_name='us-east-1')
ec2_client = boto3.client('ec2', region_name='us-east-1')
s3_resource = boto3.resource('s3')
s3_client = boto3.client('s3')

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
print(f"\nec2 website instance status ok")

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

#running the subprocess to download the image

subprocess.run(["curl","-O","https://setuacsresources.s3-eu-west-1.amazonaws.com/setulogo.jpeg"])
#creating a bucket
random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
bucket_name = random_chars+"-jvsilva"  

try:
 s3_resource.create_bucket(Bucket=bucket_name)
 print ("\nbucket created")
except Exception as error:
 print (error)
 exit(1)
 
#managing acess and files to be put on a bucket to be turn into an static website
print("adding the image and the index.html to the bucket")
s3_resource.Object(bucket_name, 'setulogo.jpeg').put(
    Body=open('setulogo.jpeg', 'rb'), 
    ContentType='image/jpeg'
)

s3_client.delete_public_access_block(Bucket=bucket_name)

bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": f"arn:aws:s3:::{bucket_name}/*"
    }]
}
s3_resource.Bucket(bucket_name).Policy().put(Policy=json.dumps(bucket_policy))

html_content = f"""
    <h1>João Victor Godoy da Silva</h1>
    <img src="setulogo.jpeg">
    <h2>Bucket: {bucket_name}</h2>
"""

with open('index.html', 'w') as file:
    file.write(html_content)
    
s3_resource.Object(bucket_name, 'index.html').put(
    Body=open('index.html', 'rb'),
    ContentType='text/html'
)

website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'}
}

bucket_website = s3_resource.BucketWebsite(bucket_name)
bucket_website.put(WebsiteConfiguration=website_configuration)

website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"

print("S3 website configured")
print(f"\nEC2 Website: http://{instance.public_ip_address}")
print(f"S3 Website:  {website_url}")

#adding the url to an file
filename = "jvsilva-websites.txt"
with open(filename, 'w') as file:
    file.write(f"EC2 Website: http://{instance.public_ip_address}\n")
    file.write(f"S3 Website: {website_url}\n")
print(f"\nURLs written to {filename}")

#usign the scp monitoring 
ip_address = instance.public_ip_address

try:
    # Copy monitoring.sh to instance
    print(f"\nCopying monitoring.sh to instance")
    scp_cmd = f"scp -o StrictHostKeyChecking=no -i {KEY_FILE} monitoring.sh ec2-user@{ip_address}:."
    
    result = subprocess.run(scp_cmd, shell=True)
    print(f"Return code: {result.returncode}")
    
    if result.returncode != 0:
        raise Exception("SCP failed")
    
    #Make script executable
    print("\nMaking monitoring.sh executable")
    chmod_cmd = f"ssh -o StrictHostKeyChecking=no -i {KEY_FILE} ec2-user@{ip_address} 'chmod 700 monitoring.sh'"
    
    result = subprocess.run(chmod_cmd, shell=True)
    print(f"Return code: {result.returncode}")
    
    if result.returncode != 0:
        raise Exception("chmod failed")
    
    #Execute monitoring script
    print("\nExecuting monitoring.sh...")
    exec_cmd = f"ssh -o StrictHostKeyChecking=no -i {KEY_FILE} ec2-user@{ip_address} './monitoring.sh'"
    result = subprocess.run(exec_cmd, shell=True)
    print(f"Return code: {result.returncode}")
    
    print("\nMonitoring completed")
    
except Exception as e:
    print(f"Monitoring error: {e}")
    print("EC2 and S3 websites are still functional")
