hosts -- Файл с узлами, заполняется записями вида "kafka-1 ansible_host=192.168.122.142.xip.io node_id=1"
kafka_cluster.yml -- Плейбук установки и изменения кластера
ansible-playbook -i hosts kafka_cluster.yml -- Запустить установку на все узлы из группы kafka в перечисленные в файле hosts. Если на каких-то хостах kafka уже установленна, они будут пропущенны, а установка будет проиведена на остальные.
ansible-playbook -i hosts kafka_cluster.yml --tags clean -- Вычищает данные и все вайлы кафки и зукипера, после чего нода готова для повторой конфигурации 
ansible-playbook -i hosts kafka_cluster.yml --tags reconfigure -- Не трогает данные и бинарники, но перегенерирует конфиги и скрипты с учетом изменений в плейбуке, после чего рестартит сервисы
ansible-playbook -i hosts kafka_cluster.yml --tags restart -- Просто рестарт кафки на всех нодах

Структура папки с ролями:
В каталоге с плейбукао есть папка Roles, где хранятся данные о ролях, разложеные по подпапкам (в нашем случае epel, basic_centos, и kafka_node_centos). Рассмотрим структуру роли на примере kafka_node_centos:
tasks -- непосредственно задания, которые выполняются, запускается main.yml, из него могут вызыватся другие задания.
vars -- файлы с переменными, переменные в нем имеют довольно высокий приоритет среди других способов их указаний, к примеру более высокий, чем в файли инвентаризации.
defaults -- тоже файлы с переменными, с самым низким приоритетом.
files -- папка с файлами для копирования на хосты в неизменном виде.
templates -- папка с шаблонами конфигов.
meta -- папка с зависимостями этой роли от других ролей.
