#!/bin/bash
#for vm in kafka1 kafka2 kafka3; do vm_clean $vm; done
#for vm in kafka-str-4 kafka-str-5 kafka-str-6; do vm_clean $vm; done
ansible-playbook -i hosts kafka_stretch.yml --tags clean;
vmconnect kafka-c 'docker-compose stop'
#ansible-playbook -i hosts kafka_stretch.yml --tags clean;
#for vm in kafka-str-4 kafka-str-5 kafka-str-6 kafka1 kafka2 kafka3; do vmconnect $vm 'systemctl restart kafka '; done; beep
sleep 60
ansible-playbook -i hosts kafka_cluster.yml; vmconnect kafka-c 'docker-compose up -d'; sleep 30; vmconnect kafka-c 'bash post.sh'
sleep 60
#ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc1 
#ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc1 --limit kafka_dc1; 
#sleep 60
#ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc1 --limit kafka_dc2; 
#sleep 60
ansible-playbook -i hosts kafka_stretch.yml 
sleep 20
for vm in kafka-str-4 kafka-str-5 kafka-str-6 kafka1 kafka2 kafka3; do vmconnect $vm 'systemctl status kafka |grep Act'; echo ''; done; beep
