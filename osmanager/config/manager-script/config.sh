#!/bin/bash

COMMON_PATH=$(dirname $(readlink -f "$0"))

source $COMMON_PATH/common_params.sh

# ==================== 工具函数 ====================

# 检查依赖工具
check_dependencies() {
    operation=$1
    if ! command -v "$operation" &> /dev/null; then
        echo "错误: $operation命令不可用，请安装$operation包" >&2
        return 1
    fi
    return 0
}




# 输出time的JSON对象
function output_time_json() {

    time="$1"
    zone="$2"
    ntp_sync_status="$3"
    json_data=$(printf "{\"time\": \"%s\",\"zone\": \"%s\",\"ntp\": \"%s\"}" "$time" "$zone" "$ntp_sync_status")
    echo "$json_data"

}


# 输出RSA的JSON对象
function output_RSA_json() {
    local algorithm="$1"
    local SHA256="$2"
    local MD5="$3"
    SHA256=$(echo "$SHA256" | cut -d ':' -f2-)
    MD5=$(echo "$MD5" | cut -d ':' -f2-)
    # 构造完整的RSA_JSON 输出

cat <<EOF
{
  "$algorithm": {
    "sha256":"$SHA256",
     "md5":"$MD5"
  }
}
EOF

}

# 获取主机ssh密钥指纹
get_ssh_key() {
    # 检查依赖
    if ! check_dependencies "ssh-keygen"; then
        return 1
    fi

    path=/etc/ssh/ssh_host_*_key.pub
    echo "["
    first=true

        for key in $path; do
          # 只处理存在的文件
          if [[ ! -f "$key" ]]; then
            continue
          fi
          file_name=$(basename $key)
          type=$(echo "$file_name" | cut -d'_' -f3)
          sha_256=`ssh-keygen -lf "$key" | awk -F ' ' '{print $2}'`
          md5=`ssh-keygen -E md5 -lf "$key" | awk -F ' ' '{print $2}'`
          json_key=$(output_RSA_json $type $sha_256 $md5)
          # 如果函数有输出（即不是空或出错）
          if [[ -n "$json_key" ]]; then
            if [ "$first" = true ]; then
              first=false
            else
              echo ","
            fi
            echo "$json_key"
          fi
        done
        echo "
        ]"

}


# 获取主机名
get_hostname() {
    # 检查依赖
    if ! check_dependencies "hostname"; then
        return 1
    fi

    hostname=`hostname`
    echo "$hostname"

}


# 读取配置文件
function readConfigFile() {

   config_file=$1
   config=`cat $1 2>/dev/null`
   code=$?
   if [ $code == 0 ]; then
     echo "$config"
   fi
   return $code

}

# 获取时间
get_time() {
    # 检查依赖
    if ! check_dependencies "timedatectl"; then
        return 1
    fi

    timeinfo=`timedatectl`
    localtime=$(echo "$timeinfo" | grep "Local time" | cut -d ':' -f2-)
    zone=$(echo "$timeinfo" | grep "Time zone" | cut -d ':' -f2-)
    ntp_sync_status=$(timedatectl |grep "System clock synchronized" | cut -d ':' -f2-)
    if [[ "$ntp_sync_status" =~ "yes" ]]; then
        ntp_sync_status="true"
    else
        ntp_sync_status="false"
    fi
    output_time_json "$localtime" "$zone" "$ntp_sync_status"

}


# 修改主机名
set_hostname() {
    # 检查依赖

    if ! check_dependencies "hostnamectl"; then
        return 1
    fi

    server_name="$1"
    hostname=`hostnamectl set-hostname $server_name`
    code=$?
    return $code

}

type=$1
type_name=$2
if [ "$type" == "sshkey" ]; then
    get_ssh_key
elif [ "$type" == "gethostname" ]; then
    get_hostname
elif [ "$type" == "time" ]; then
    get_time
elif [ "$type" == "sethostname" ]; then
    set_hostname "$type_name"
elif [ "$type" == "get" ]; then
   if [ "$type_name" == ".bashrc" ]; then
      readConfigFile "$BASHRC"
   fi
    
fi

code=$?
exit $code

