#!/bin/bash
psql -d "testdb" -c "CREATE TABLE IF NOT EXISTS large_test (num1 bigint, num2 double precision, num3 double precision);"
echo "`date` add 200 lines" >> /tmp/mypg.log
psql -d "testdb" -c "INSERT INTO large_test (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 200) s(i);"

psql -d "testdb" -c "CREATE TABLE IF NOT EXISTS table1 (num1 bigint, num2 double precision, num3 double precision);"
psql -d "testdb" -c "INSERT INTO table1 (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 2000000) s(i);"

psql -d "testdb" -c "CREATE TABLE IF NOT EXISTS ololo (num1 bigint, num2 double precision, num3 double precision);"
psql -d "testdb" -c "INSERT INTO ololo (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 200) s(i);"

exit 0
sleep 300
echo "`date` add 2000000 lines" >> /tmp/mypg.log
psql -d "testdb" -c "INSERT INTO large_test (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 2000000) s(i);"
sleep 300
echo "`date` add 2000000 lines" >> /tmp/mypg.log
psql -d "testdb" -c "INSERT INTO large_test (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 2000000) s(i);"
sleep 300
echo "`date` add 2000000 lines" >> /tmp/mypg.log
psql -d "testdb" -c "INSERT INTO large_test (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 2000000) s(i);"
sleep 300
echo "`date` add 2000000 lines" >> /tmp/mypg.log
psql -d "testdb" -c "INSERT INTO large_test (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 2000000) s(i);"
sleep 300
echo "`date` add 2000000 lines" >> /tmp/mypg.log
psql -d "testdb" -c "INSERT INTO large_test (num1, num2, num3) SELECT round(random()*10), random(), random()*142 FROM generate_series(1, 2000000) s(i);"
