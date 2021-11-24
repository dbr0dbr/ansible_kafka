p5_4=`df --local -P | awk {'if (NR!=1) print $6'} | xargs -I '{}' find '{}' -xdev -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null`
p6_3=`grep ^RSYNC_ENABLE /etc/default/rsync |grep -v false`

function show_status () {
  test_name=$1
  test_output=$2
  if [ -z $test_output ] ;then echo "$test_name - Ok"; else echo "$test_name - Warning!"; echo "test_output"; fi
}

function check_perm () {
  file_name=$1
  file_perm=$2
  if [[ ! -d $file_name ]] && [[ ! -f $file_name ]]; then echo "$file_name ok"; return; fi
  if [[ `stat --printf "%A %U %G" $file_name` == "$file_perm" ]]; then
    echo "$file_name ok"
  else
    echo "$file_name - Warning!"
    stat --printf "%n %A %U %G" $file_name 
    echo ""
  fi
}

check_passwd () {
  if grep "^root:x:0:0:root:" /etc/passwd >> /dev/null; then
    echo "root has id=0 - Ok"
  else
    echo "root has id=0 - Warning!"
    grep "^root:x:0:0:root:" /etc/passwd
  fi
  if [[ `cat /etc/passwd | awk -F: '($3 == 0) { print $1 }'` == root ]]; then
    echo "id=0 only for root - Ok "
  else
    echo id=0 only for root - Warning
    cat /etc/passwd | awk -F: '($3 == 0) { print $1 }'
  fi
}

#show_status 5.4 $p5_4
#show_status 6.3 $p6_3
check_perm /etc/crontab '-rw-r--r-- root root'
check_perm /etc/cron.d 'drwxr-xr-x root root'
check_perm /etc/cron.allow '-rw-r--r-- root root'
check_perm /etc/at.allow '-rw-r--r-- root root'
check_perm /etc/cron.deny  'none root root'
check_perm /etc/at.deny 'none root root'
check_passwd
check_perm /etc/passwd '-rw-r--r-- root root'
check_perm /etc/group '-rw-r--r-- root root'
check_perm /etc/shadow '-rw-r----- root shadow'
check_perm /etc/ssh/sshd_config '-rw-r--r-- root root'
