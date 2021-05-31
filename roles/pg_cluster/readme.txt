Структура для инвентори:
[pg_cluster:children]
pg_dc1
pg_dc2

[pg_dc1]
pg-cl-1 ansible_host=192.168.121.191 master=YES
pg-cl-2 ansible_host=192.168.121.131 my_master=pg-cl-1

[pg_dc2]
pg-cl-3 ansible_host=192.168.132.218 my_master=pg-cl-1
pg-cl-4 ansible_host=192.168.132.135 my_master=pg-cl-3

################################################################################################################
    Дефолтная схема репликации: pg-cl-1 (мастер) и pg-cl-2 в pg_dc1 (Днепр), pg-cl-3 и pg-cl-4 в pg_dc2 (Киев). 

     pg-cl-1
    /       \
pg-cl-2  pg-cl-3
             |
         pg-cl-4
         
################################################################################################################

Аварийные сценарии:

1. Недоступны обе днепровские ноды. 
Действия при аварии:
    У нас остается следующая конструкция:
         pg-cl-3
             |
         pg-cl-4
    Нода pg-cl-4 и так реплецируется с ноды pg-cl-3, нужно только изменить DNS и обьявить pg-cl-3 мастером, чтобы появилась возможность писать на нее, для этого на pg-cl-3:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
Действия при восстановлении:
    Когда связь с pg-cl-1 и pg-cl-2 восстановится сначала нам нужно будет получить на них актуальные реплики, для этого построим следующую схему репликации:
     pg-cl-3
    /       \
pg-cl-4  pg-cl-1
             |
         pg-cl-2
    Для этого на pg-cl-1 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.132.218 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_1
exit
systemctl start postgresql-12
    На pg-cl-2 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.121.191 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_2
exit
systemctl start postgresql-12
    После того, как репликация будет завершена, можно снова обявить pg-cl-1 мастером, и вернутся к первоначальной схеме. Поскольку pg-cl-2 и так реплицируется с pg-cl-1 перенастроить репликацию нужно только на pg-cl-3 и pg-cl-4. Сначала на pg-cl-3 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.121.191 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3
exit
systemctl start postgresql-12
    На pg-cl-4 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.132.218 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_4
exit
systemctl start postgresql-12
    После чего изменяем DNS и объявляем нашу ноду мастером, для этого на pg-cl-1:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
    В результате получаем первоначальную схему:
     pg-cl-1
    /       \
pg-cl-3  pg-cl-2  
             |
         pg-cl-4



2. Недоступна нода pg-cl-1. 
Действия при аварии:
    У нас остается следующая конструкция:
pg-cl-2  pg-cl-3
             |
         pg-cl-4
    Можно пойти по предидущему сценарию, но если осталные ноды проекта остались в днепре, по перенос СУБД в Киев увеличит задержки, из-за чего упадет производительность. Чтобы этого избежать построим следующую схему репликации:
pg-cl-2  
    |
pg-cl-3
    |
pg-cl-4
    Нужно только изменить DNS и обьявить pg-cl-2 мастером, чтобы появилась возможность писать на нее, для этого на pg-cl-2:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
    После этого нам нужно перенастроить репликацию на pg-cl-3 и pg-cl-4 (в процессе будет перетянута вся база), для этого сначала на pg-cl-3 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.121.131 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3
exit
systemctl start postgresql-12
На pg-cl-4 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.132.218 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_2
exit
systemctl start postgresql-12
Действия при восстановлении:
    Когда связь с pg-cl-1 восстановится сначала нам нужно будет получить актуальную реплику на pg-cl-1 и перенастроить pg-cl-3 и pg-cl-4 для получения реплики с pg-cl-1, для этого построим следующую схему репликации:
pg-cl-2
    |
pg-cl-1  
    |
pg-cl-3
    |
pg-cl-4
    Для этого на pg-cl-1 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.121.131 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_1
exit
systemctl start postgresql-12
    На pg-cl-3 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.121.191 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3
exit
systemctl start postgresql-12
    На pg-cl-4 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.132.218 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_4
exit
systemctl start postgresql-12
    После того, как реплики синхронизируются с pg-cl-2 ее можно перенастроить. На pg-cl-2 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.121.191 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_2
exit
    
    Меняем DNS запись и объявляем pg-cl-1 мастером, для этого на pg-cl-1:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
    В результате получаем первоначальную схему:
     pg-cl-1
    /       \
pg-cl-2  pg-cl-3
             |
         pg-cl-4


################################################################################################################
Дебаг и прочее:

Кто реплицируется с машины?
Слот репликации -- создается на машине с которой происходит репликация. Проверить слоты репликации:
psql -c "select slot_name from pg_replication_slots;"
Посмотреть ip, с которых реплицируют данную машину:
psql -c "select client_addr from pg_stat_replication;"

С кого реплицируется машина?
Посмотреть с какого хоста и через какой слот реплицируется данная машина:
psql -c "select sender_host, slot_name from pg_stat_wal_receiver;"

Удалить слот репликации можно с той машины, на которой он был создан, т.е. той, с которой идет репликация. Сделать это можно так:
psql -c "select pg_drop_replication_slot('slot_name');"

Обьчвить реплику мастером можно для postgresql 12 можно так:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/

После этого на всех нодах кластера, кроме тех, что и так синхронизировались с ноды объявленной мастером, нужно перенастроить репликацию и перетянуть все данные:
systemctl stop postgresql-12; su postgres; rm -rf /var/lib/pgsql/12/data/*; su postgress
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host my_master_ip --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S slot_name 
где my_master_ip это ip с которого мы будем реплицировать данные (не обязательно именно мастер, возможна каскадная репликация), а slot_name это слот репликации(я их именовал как pgstandby_hostname, только если в hostname есть -, то его нужно заменить на _, иначе не приймет)
exit
systemctl start postgresql-12
Пример:
Мы объявили мастером хост pg-cl-1(192.168.121.191), и хотим реплицировать с него данные на pg-cl-3(192.168.132.218)
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 192.168.121.191 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3 
exit
systemctl start postgresql-12
В результате на pg-cl-1 будет создан слот репликации pgstandby_pg_cl_3,а наша нода через него начнет перетягивать базу.

В некоторых случаях (например мы переразвернули машинку pg-cl-3 и снова настраиваем репликацию) можно увидить ошибку вида:
pg_basebackup: error: could not send replication command "CREATE_REPLICATION_SLOT "pgstandby_pg_cl_3" PHYSICAL RESERVE_WAL": ERROR:  replication slot "pgstandby_pg_cl_3" already exists
Это связанно с тем, что слот с таким именем уже был создан, но поскольку мы сбрасывали ноду pg-cl-3 продолжить репликацию с него мы уже не можем. Такой слод нужно удалить, для этого заходим на pg-cl-1 и выполняем:
psql -c "select pg_drop_replication_slot('pgstandby_pg_cl_3');"
