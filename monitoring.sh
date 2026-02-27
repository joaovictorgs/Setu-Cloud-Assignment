#!/usr/bin/bash
#
# Some basic monitoring.
#
TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
MEMORYUSAGE=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
PROCESSES=$(expr $(ps -A | grep -c .) - 1)
HTTPD_PROCESSES=$(ps -A | grep -c httpd)
#
# Enhanced Monitoring
#
UPTIME=$(uptime -p)
WHOAMI=$(whoami)
SPACEUSAGE=$(df | awk 'NR>1{sum+= $5} END {print sum}')
FREEMEMORY=$(free -m | awk 'NR==2 {print $4}')

echo "BASIC SYSTEM MONITORING REPORT:"
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Memory utilisation: $MEMORYUSAGE"
echo "No of processes: $PROCESSES"
echo ""
echo "ENHANCED SYSTEM MONITORING REPORT:"
echo "the system is $UPTIME"
echo "the user is: $WHOAMI"
echo "space usage: $SPACEUSAGE%"
echo "Free memory: $FREEMEMORY"

if [ $HTTPD_PROCESSES -ge 1 ]
then
    echo "Web server is running"
else
    echo "Web server is NOT running"
fi
