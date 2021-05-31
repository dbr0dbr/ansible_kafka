Структура для инвентори:
[pg_cluster:children]
pg_dc1
pg_dc2

[pg_dc1]
SH-DB-MAIN-P01 ansible_host=10.0.6.81 master=YES
SH-DB-MAIN-P02 ansible_host=10.0.6.82 my_master=SH-DB-MAIN-P01

[pg_dc2]
SH-DB-KYIV-P01 ansible_host=10.1.6.29 my_master=SH-DB-MAIN-P01
SH-DB-KYIV-P02 ansible_host=10.1.6.30 my_master=SH-DB-KYIV-P01

################################################################################################################
    Дефолтная схема репликации: SH-DB-MAIN-P01 (мастер) и SH-DB-MAIN-P02 в pg_dc1 (Днепр), SH-DB-KYIV-P01 и SH-DB-KYIV-P02 в pg_dc2 (Киев). 

     SH-DB-MAIN-P01
    /              \
SH-DB-MAIN-P02  SH-DB-KYIV-P01
                    |
                SH-DB-KYIV-P02
         
################################################################################################################

Аварийные сценарии:

1. Недоступны обе днепровские ноды. 
Действия при аварии:
    У нас остается следующая конструкция:
         SH-DB-KYIV-P01
             |
         SH-DB-KYIV-P02
    Нода SH-DB-KYIV-P02 и так реплецируется с ноды SH-DB-KYIV-P01, нужно только изменить DNS и обьявить SH-DB-KYIV-P01 мастером, чтобы появилась возможность писать на нее, для этого на SH-DB-KYIV-P01:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
Действия при восстановлении:
    Когда связь с SH-DB-MAIN-P01 и SH-DB-MAIN-P02 восстановится сначала нам нужно будет получить на них актуальные реплики, для этого построим следующую схему репликации:
     SH-DB-KYIV-P01
    /               \
SH-DB-KYIV-P02  SH-DB-MAIN-P01
                    |
                SH-DB-MAIN-P02
    Для этого на SH-DB-MAIN-P01 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.1.6.29 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_1
exit
systemctl start postgresql-12
    На SH-DB-MAIN-P02 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.0.6.81 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_2
exit
systemctl start postgresql-12
    После того, как репликация будет завершена, можно снова обявить SH-DB-MAIN-P01 мастером, и вернутся к первоначальной схеме. Поскольку SH-DB-MAIN-P02 и так реплицируется с SH-DB-MAIN-P01 перенастроить репликацию нужно только на SH-DB-KYIV-P01 и SH-DB-KYIV-P02. Сначала на SH-DB-KYIV-P01 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.0.6.81 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3
exit
systemctl start postgresql-12
    На SH-DB-KYIV-P02 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.1.6.29 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_4
exit
systemctl start postgresql-12
    После чего изменяем DNS и объявляем нашу ноду мастером, для этого на SH-DB-MAIN-P01:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
    В результате получаем первоначальную схему:
     SH-DB-MAIN-P01
    /              \
SH-DB-KYIV-P01  SH-DB-MAIN-P02  
                    |
                SH-DB-KYIV-P02



2. Недоступна нода SH-DB-MAIN-P01. 
Действия при аварии:
    У нас остается следующая конструкция:
SH-DB-MAIN-P02  SH-DB-KYIV-P01
                    |
                SH-DB-KYIV-P02
    Можно пойти по предидущему сценарию, но если осталные ноды проекта остались в днепре, по перенос СУБД в Киев увеличит задержки, из-за чего упадет производительность. Чтобы этого избежать построим следующую схему репликации:
SH-DB-MAIN-P02  
    |
SH-DB-KYIV-P01
    |
SH-DB-KYIV-P02
    Нужно только изменить DNS и обьявить SH-DB-MAIN-P02 мастером, чтобы появилась возможность писать на нее, для этого на SH-DB-MAIN-P02:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
    После этого нам нужно перенастроить репликацию на SH-DB-KYIV-P01 и SH-DB-KYIV-P02 (в процессе будет перетянута вся база), для этого сначала на SH-DB-KYIV-P01 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.0.6.82 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3
exit
systemctl start postgresql-12
На SH-DB-KYIV-P02 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.1.6.29 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_2
exit
systemctl start postgresql-12
Действия при восстановлении:
    Когда связь с SH-DB-MAIN-P01 восстановится сначала нам нужно будет получить актуальную реплику на SH-DB-MAIN-P01 и перенастроить SH-DB-KYIV-P01 и SH-DB-KYIV-P02 для получения реплики с SH-DB-MAIN-P01, для этого построим следующую схему репликации:
SH-DB-MAIN-P02
    |
SH-DB-MAIN-P01  
    |
SH-DB-KYIV-P01
    |
SH-DB-KYIV-P02
    Для этого на SH-DB-MAIN-P01 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.0.6.82 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_1
exit
systemctl start postgresql-12
    На SH-DB-KYIV-P01 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.0.6.81 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3
exit
systemctl start postgresql-12
    На SH-DB-KYIV-P02 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.1.6.29 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_4
exit
systemctl start postgresql-12
    После того, как реплики синхронизируются с SH-DB-MAIN-P02 ее можно перенастроить. На SH-DB-MAIN-P02 (pg_basebackup попросит пароль для repuser):
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.0.6.81 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_2
exit
    
    Меняем DNS запись и объявляем SH-DB-MAIN-P01 мастером, для этого на SH-DB-MAIN-P01:
/usr/pgsql-12/bin/pg_ctl  promote -D /var/lib/pgsql/12/data/
    В результате получаем первоначальную схему:
     SH-DB-MAIN-P01
    /              \
SH-DB-MAIN-P02  SH-DB-KYIV-P01
                    |
                SH-DB-KYIV-P02


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
Мы объявили мастером хост SH-DB-MAIN-P01(10.0.6.81), и хотим реплицировать с него данные на SH-DB-KYIV-P01(10.1.6.29)
systemctl stop postgresql-12; rm -rf /var/lib/pgsql/12/data/*; su postgres
pg_basebackup  --progress --write-recovery-conf --wal-method=stream --checkpoint=fast --host 10.0.6.81 --username repuser --pgdata=/var/lib/pgsql/12/data/ -C -S pgstandby_pg_cl_3 
exit
systemctl start postgresql-12
В результате на SH-DB-MAIN-P01 будет создан слот репликации pgstandby_pg_cl_3,а наша нода через него начнет перетягивать базу.

В некоторых случаях (например мы переразвернули машинку SH-DB-KYIV-P01 и снова настраиваем репликацию) можно увидить ошибку вида:
pg_basebackup: error: could not send replication command "CREATE_REPLICATION_SLOT "pgstandby_pg_cl_3" PHYSICAL RESERVE_WAL": ERROR:  replication slot "pgstandby_pg_cl_3" already exists
Это связанно с тем, что слот с таким именем уже был создан, но поскольку мы сбрасывали ноду SH-DB-KYIV-P01 продолжить репликацию с него мы уже не можем. Такой слод нужно удалить, для этого заходим на SH-DB-MAIN-P01 и выполняем:
psql -c "select pg_drop_replication_slot('pgstandby_pg_cl_3');"
