#!/usr/bin/bash
#
# Some basic monitoring.
#
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
PROCESSES=$(expr $(ps -A | grep -c .) - 1)
HTTPD_PROCESSES=$(ps -A | grep -c httpd)
UPTIME=$(uptime -p)
WHOAMI=$(whoami)
SPACEUSAGE=$(df | awk 'NR>1{sum+= $5} END {print sum}')

echo "SYSTEM MONITORING REPORT"
echo "Instance ID: $INSTANCE_ID"
echo "Memory utilisation: $MEMORYUSAGE"
echo "No of processes: $PROCESSES"
echo "the system is $UPTIME"
echo "the user is: $UPTIME"
echo "space usage: $SPACEUSAGE%"

if [ $HTTPD_PROCESSES -ge 1 ]
then
    echo "Web server is running"
else
    echo "Web server is NOT running"
fi
