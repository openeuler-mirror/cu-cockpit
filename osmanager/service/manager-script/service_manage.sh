#!/bin/bash

MKDIR="/bin/mkdir -p"
# 日志位置
MANAGER_LOG_DIR=/opt/chinaunicom/log
if [ ! -d "$MANAGER_LOG_DIR" ]; then
    $MKDIR "$MANAGER_LOG_DIR"
fi
MANAGER_LOG_FILE=$MANAGER_LOG_DIR/$(date '+%Y%m%d').log

# 错误日志输出
print_cmd_result(){
  result="${1}"
  status_code=${2}
  local log_file=${operation}
  if [ $status_code -ne 0 ];then
    echo  "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $result" >> $MANAGER_LOG_FILE
  fi
}


# 服务stop、start、restart函数
function manageService() {
   service_name=$1
   operation=$2
   host_name=$(hostname)
   echo "__service-task__#start:$service_name:$operation:$(date '+%Y-%m-%d %H:%M:%S')" >> $MANAGER_LOG_FILE
   echo "__node-task__#start:$service_name:$host_name:$operation:$(date '+%Y-%m-%d %H:%M:%S')" >> $MANAGER_LOG_FILE
   result=`sudo systemctl $operation $service_name 2>&1`
   code=$?
   echo "__node-task__#end:$service_name:$host_name:$operation:$code:$(date '+%Y-%m-%d %H:%M:%S')" >> $MANAGER_LOG_FILE
   print_cmd_result "$result" "$code"
   echo "__service-task__#end:$service_name:$operation:$(date '+%Y-%m-%d %H:%M:%S')" >> $MANAGER_LOG_FILE
   return $code
}



# 缺少必需参数或请求帮助时输出用法
if [ "$1" = "-h" ] ; then
   echo "service-manager.sh <status|start|stop|restart|rollup> <service>"
   echo " - start/stop/restart/rollup the specified  service"
   echo "service:"
   echo "  systemtem_service - eg:fillwared"
   [ "$1" = "-h" ] && exit 0
fi
if [ $# -lt 2 ]; then
  echo "缺少service_name or operation"
  exit 1
fi
service_name=$1
operation=$2
manageService $service_name $operation
code=$?
exit $code
