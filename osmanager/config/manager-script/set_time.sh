#!/bin/bash

# 检查依赖工具
check_dependencies() {
    operation=$1
    if ! command -v "$operation" &> /dev/null; then
        echo "错误: $operation命令不可用，请安装$operation包" >&2
        return 1
    fi
    return 0
}

# 手动设置时间
function SetTime() {
   time=$1
    # 检查依赖
    if ! check_dependencies "timedatectl"; then
        return 1
    fi
   # 关闭时钟同步
   operation=$(sudo timedatectl set-ntp false;sudo systemctl stop chronyd)
   # 查看chronyd服务状态
   status=$(sudo systemctl status chronyd)

   status_ans=$(echo "$status" | grep -E 'Active:' | grep "inactive")
   if [ -z "$status_ans" ]; then
     code=1
     return $code
   fi
    
   set_date=$(sudo date -s "$time")
   # 验证设置结果
   current_time=$(date '+%Y-%m-%d %H:%M:%S')
   current_zone=$(date '+%Z')
   echo "设置成功，当前时间: $current_time $current_zone"
   code=$?
   return $code
}



# 时钟同步时间
function AutoSetTime() {

    # 检查依赖
    if ! check_dependencies "timedatectl"; then
        return 1
    fi
   # 开启时钟同步
   operation=$(sudo timedatectl set-ntp true;sudo systemctl start chronyd)
   code=$?
   if [ "$code" != 0 ] ; then
    return $code
   fi
   # 查看chronyd服务状态
   status=$(sudo systemctl status chronyd)
   status_ans=$(echo "$status" | grep -E 'Active:' | grep "active (running)")
   if [ -z "$status_ans" ]; then
     code=1
   fi
   return $code

}



# 缺少必需参数或请求帮助时输出用法
if [ "$1" = "-h" ] ; then
   echo "settime.sh <autotime|settime> [time]"
   echo " - update system_time"
   [ "$1" = "-h" ] && exit 0
fi
if [ $# -lt 1 ]; then
  echo "缺少参数"
  exit 1
fi



type="$1"
time="$2"
if [ "$type" == "autotime" ]; then
    AutoSetTime
elif [ "$type" == "settime" ]; then
    SetTime "$time"
fi
code=$?
exit $code
