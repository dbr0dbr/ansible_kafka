В инвентори нам нужно иметь следующую структуру:
[all:vars]
proxy_env={"http_prox" : "http://192.168.121.1:8888", "https_proxy" : "https://192.168.121.1:8888", "no_proxy" : ".atbmarket.com,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"}
ansible_ssh_common_args='-o StrictHostKeyChecking=no'

[kafka_stretch:children]
kafka_dc1 
kafka_dc2

[kafka_dc1]
SH-KAF-MAIN-P01 ansible_host=10.0.6.83 node_id=1
SH-KAF-MAIN-P02 ansible_host=10.0.6.84 node_id=2
SH-KAF-MAIN-P03 ansible_host=10.0.6.85 node_id=3

[kafka_dc2]
SH-KAF-KYIV-P01 ansible_host=10.1.6.14 node_id=4
SH-KAF-KYIV-P02 ansible_host=10.1.6.15 node_id=5
SH-KAF-KYIV-P03 ansible_host=10.1.6.16 node_id=6

Если в группах kafka_dc1 и kafka_dc2 одинаковое количество нод, то кластер конфигурируется под иерархические выборы, т.е. возможность автономной работы половины нод при выставлении им большего веса в голосовании (опция master_dc).
В остальных случаях идет стандартная настройка кластера

Плейбук kafka_stretch имеет следующие возможности:
Для перенастройки ноды просто запускаем плейбук, никаких reconfigure не надо.
ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc1 -- дает нодам из первого датацентра более высокий вес голоса, чем нодам из второго, что позволяет им выбрать лидера без большинства.
ansible-playbook -i hosts kafka_stretch.yml --limit kafka_dc1 -- запустить плейбук только на первый датацентр
ansible-playbook -i hosts kafka_stretch.yml --tags clean -- удалить кафку, зукипер и их данные
ansible-playbook -i hosts kafka_stretch.yml --tags status -- узнать статус сервисов зукипера и кафки
ansible-playbook -i hosts kafka_stretch.yml --tags restart -- перезапустить кафку и зукипер

Для того, чтобы растянуть кластер на 6 нод необходимо сделать следующее:
Перенастраиваем ноды в первом датацентре для работы с более высоким весом голоса в растянутом кластере
ansible-playbook -i hosts kafka_stretch.yml --tags clean --limit kafka_dc2
Настраиваем все ноды для равноправной работы
ansible-playbook -i hosts kafka_stretch.yml 
Для того, чтобы установить фактор репликации для наших топиков по количеству нод заходим на любую ноду и запускаем скрипт:
/home/kafka/scripts/change_replication_factor_for_all_topics.sh
Если нужно назад ужать кластер до 3-х нод в одном датацентре, то делаем следующее: 
/home/kafka/scripts/move_topics_to_dc1.sh -- уменьшит фактор репликации и переместит все топики в первый ДЦ (запустить с любой ноды). 
После этого мы можем удалить из инвентори хосты второго ДЦ и проиграть наш плейбук:
ansible-playbook -i hosts kafka_stretch.yml

При неработоспособности одного из датацентров или обрыва канала между ними кластер распадается и перестает отвечать на запросы, при этом сервисы kafka и zookeeper останутся в статуе активно.

Примеры переходов:
Упал киевский ДЦ:
Сервисы продолжают работать, но перестают отвечать на запросы, потому что из 6 но осталось 3, и у нас нет кворума для выбора лидера кластера.    
Следующая дает команда нодам из первого датацентра более высокий вес голоса, чем нодам из второго, что позволяет им выбрать лидера.
ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc1 --limit kafka_dc1
После выполнения плейбука кластер в первом датацентре начинает нормально работать. Для восстановления штатной работы кластера после того, как второй ДЦ ввостановили, мы должны перенастроить его ноды в соответствии с работающими в первом ДЦ.
ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc1 --limit kafka_dc2
После этого начнется синхронизация, во второй ДЦ пойдут сообщения, которые он пропустил за время простоя. Для возврата кластера в нормальный равноправный режим запускаем команду:
ansible-playbook -i hosts kafka_stretch.yml

Для падения днепровского ДЦ действия аналогичные:
ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc2 --limit kafka_dc2
Для восстановления:
ansible-playbook -i hosts kafka_stretch.yml -e master_dc=kafka_dc2 --limit kafka_dc1
ansible-playbook -i hosts kafka_stretch.yml

Перенос бэкапа на стэндэлон ноду:
#!/bin/bash
На ноде, куда заливаем бкап выполняем:
systemctl stop kafka; systemctl stop zookeeper; rm -rf /home/kafka/kafka-logs/* ; rm -rf /opt/zookeeper/data/*

Заходим на одну из боевых нод, и выполняем: 
/home/kafka/scripts/change_replication_factor_for_all_topics.sh -- чтобы убедится, что на нашей ноде будут реплики всех топиков.
systemctl stop kafka
systemctl stop zookeeper
rsync -azv /home/kafka/kafka-logs/ root@$restore_host:/home/kafka/kafka-logs/
rsync -azv /opt/zookeeper/data/ root@$restore_host:/opt/zookeeper/data/

После этого заходим на ноду, куда ввостанавливаем бэкап, и в файле /home/kafka/kafka/config/server.properties добавляем unclean.leader.election.enable = true
Запускаем кафку:
systemctl start kafka
Перенастраиваем наши топики на одну ноду:
/home/kafka/scripts/move_topics_to_node_1.sh
Посмотреть текущего лидера и настройки топиков можно через /home/kafka/scripts/info_all_topics.sh.
 

