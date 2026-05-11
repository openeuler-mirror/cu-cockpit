#!/bin/bash

current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 检查依赖,看命令是否存在
function check_dependencies() {
    operation=$1

    if ! command -v $operation &> /dev/null; then
        echo "错误: lspci 命令不可用，请安装 pciutils 包" >&2
        return 1
    fi
    return 0
}


# 输出bios的JSON对象
function output_bios_json() {
    local vendor="$1"
    local version="$2"
    local release_date="$3"

    cat <<EOF
      {
        "vendor": "$vendor",
        "version": "$version",
        "release_date": "$release_date"
      }
EOF
}


# 输出bios的JSON对象
function output_network_json() {
    local iface="$1"
    local state="$2"
    local iface_type="$3"
    local mac="$4"
    local ipv4="$5"
    local ipv6="$6"
    local rx_bytes="$7"
    local tx_bytes="$8"
    local speed="$9"
    local duplex="${10}"
    local auto_neg="${11}"
cat <<EOF
      {
        "interface": "$iface",
        "state": "$state",
        "type": "$iface_type",
        "mac": "$mac",
        "ipv4": $([ "$ipv4" = "null" ] && echo "null" || echo "\"$ipv4\""),
        "ipv6": $([ "$ipv6" = "null" ] && echo "null" || echo "\"$ipv6\""),
        "rx_bytes": $([ "$rx_bytes" = "null" ] && echo "null" || echo "$rx_bytes"),
        "tx_bytes": $([ "$tx_bytes" = "null" ] && echo "null" || echo "$tx_bytes"),
        "ethtool": {
          "speed": $([ "$speed" = "null" ] && echo "null" || echo "\"$speed\""),
          "duplex": $([ "$duplex" = "null" ] && echo "null" || echo "\"$duplex\""),
          "auto_negotiation": $([ "$auto_neg" = "null" ] && echo "null" || echo "\"$auto_neg\"")
        }
      }
EOF
}


# 输出cpu的JSON对象
function output_cpu_json() {
    local cpu_model="$1"
    local cpu_cores="$2"
    local cpu_vendor="$3"

    # 构造完整的 cpu_JSON 输出
cat <<EOF
{
  "cpu": {
    "model": "${cpu_model}",
    "cores": $cpu_cores,
    "vendor": "${cpu_vendor}"
  }
}
EOF

}


# 输出system的JSON对象
function output_system_json() {
    local manufacturer="$1"
    local product_name="$2"
    local serial_number="$3"
    local machine_num="$4"
    local run_time="$5"
# 构造 system 部分的 JSON（即使某些字段为空）
cat <<EOF
{
  "system":
{
  "manufacturer": ${manufacturer:+\"$manufacturer\"},
  "product_name": ${product_name:+\"$product_name\"},
  "serial_number": ${serial_number:+\"$serial_number\"},
  "machine_num": ${machine_num:+\"$machine_num\"},
  "run_time": ${run_time:+\"$run_time\"}
}
}
EOF

}


# 输出os_system的JSON对象
function output_os_system_json() {
    local architecture="$1"
    local os_name="$2"
    local os_version="$3"
# 构造 system 部分的JSON
cat <<EOF
{
  "os_system":
{
  "architecture": ${architecture:+\"$architecture\"},
  "os_name": ${os_name:+\"$os_name\"},
  "os_version": ${os_version:+\"$os_version\"}
}
}
EOF

}

# 输出network的JSON对象
function output_network_json() {
    local iface="$1"
    local state="$2"
    local iface_type="$3"
    local mac="$4"
    local ipv4="$5"
    local ipv6="$6"
    local rx_bytes="$7"
    local tx_bytes="$8"
    local speed="$9"
    local duplex="${10}"
    local auto_neg="${11}"
cat <<EOF
      {
        "interface": "$iface",
        "state": "$state",
        "type": "$iface_type",
        "mac": "$mac",
        "ipv4": $([ "$ipv4" = "null" ] && echo "null" || echo "\"$ipv4\""),
        "ipv6": $([ "$ipv6" = "null" ] && echo "null" || echo "\"$ipv6\""),
        "rx_bytes": $([ "$rx_bytes" = "null" ] && echo "null" || echo "$rx_bytes"),
        "tx_bytes": $([ "$tx_bytes" = "null" ] && echo "null" || echo "$tx_bytes"),
        "ethtool": {
          "speed": $([ "$speed" = "null" ] && echo "null" || echo "\"$speed\""),
          "duplex": $([ "$duplex" = "null" ] && echo "null" || echo "\"$duplex\""),
          "auto_negotiation": $([ "$auto_neg" = "null" ] && echo "null" || echo "\"$auto_neg\"")
        }
      }
EOF
}


function get_cpu_info(){
    if ! check_dependencies "uname"; then
        return 1
    fi
    # ====== 1. CPU 信息 ======
    # CPU 型号
    cpu_model=$(grep "model name" /proc/cpuinfo | uniq | sed 's/.*: //')

    # CPU 核心数
    cpu_cores=$(grep -c ^processor /proc/cpuinfo)

    # CPU 厂商 (Vendor ID，例如 GenuineIntel, AuthenticAMD)
    cpu_vendor=$(grep "vendor_id" /proc/cpuinfo | uniq | awk -F ': ' '{print $2}')


    # ====== 3. 厂商信息（系统级，通过 dmidecode 获取） ======

    system_info_json="{}"
     # 提取 Manufacturer, Product Name, Serial Number
    manufacturer=$(sudo dmidecode -t system 2>/dev/null | grep "Manufacturer:" | awk -F ': ' '{print $2}' | head -n 1)
    product_name=$(sudo dmidecode -t system 2>/dev/null | grep "Product Name:" | awk -F ': ' '{print $2}' | head -n 1)
    serial_number=$(sudo dmidecode -t system 2>/dev/null | grep "Serial Number:" | awk -F ': ' '{print $2}' | head -n 1)

    # 输出cpu_json
    output_cpu_json "$cpu_model" "$cpu_cores" "$cpu_vendor"
}


# 获取系统信息
function get_system_info(){
    if ! check_dependencies "dmidecode"; then
        return 1
    fi

    # ====== 3. 厂商信息（系统级，通过 dmidecode 获取） ======
     # 提取 Manufacturer, Product Name, Serial Number
    manufacturer=$(sudo dmidecode -t system 2>/dev/null | grep "Manufacturer:" | awk -F ': ' '{print $2}' | head -n 1)
    product_name=$(sudo dmidecode -t system 2>/dev/null | grep "Product Name:" | awk -F ': ' '{print $2}' | head -n 1)
    serial_number=$(sudo dmidecode -t system 2>/dev/null | grep "Serial Number:" | awk -F ': ' '{print $2}' | head -n 1)
    run_time=$(awk '{printf "系统已运行 %.2f 小时\n", $1/3600}' /proc/uptime)
    machine_num=$(cat /etc/machine-id)

    # 输出system_json
    output_system_json "$manufacturer" "$product_name" "$serial_number" "$machine_num" "$run_time"
}




# 获取OS系统信息
function get_os_system_info(){
    if ! check_dependencies "dmidecode"; then
        return 1
    fi

    # 获得os_information,包络 类型、名称、版本
    architecture=$(uname -m)
    os_name=$(grep '^NAME=' /etc/os-release | cut -d'"' -f2)
    os_version=$(grep '^VERSION=' /etc/os-release | cut -d'"' -f2)

    # 输出os_system_json
    output_os_system_json "$architecture" "$os_name" "$os_version"
}

# 获取bios资源信息
function get_bios_info(){
    if ! check_dependencies "dmidecode"; then
        return 1
    fi
    # ====== BIOS 信息 ======

    bios_info_json="{}"
    if command -v dmidecode &>/dev/null; then
        # 提取 BIOS 信息
        bios_vendor=$(sudo dmidecode -t bios 2>/dev/null | grep "Vendor:" | awk -F ': ' '{print $2}' | head -n 1)
        bios_version=$(sudo dmidecode -t bios 2>/dev/null | grep "Version:" | awk -F ': ' '{print $2}' | head -n 1)
        bios_release_date=$(sudo dmidecode -t bios 2>/dev/null | grep "Release Date:" | awk -F ': ' '{print $2}' | head -n 1)
        # 构造 BIOS 部分的 JSON
        bios_info_json=`output_bios_json "$bios_vendor" "$bios_version" "$bios_release_date"`
    fi

    # 打印最终 JSON
    echo "$bios_info_json"
}



# 获取网卡基础信息
function get_interface_basic_info() {
    local iface="$1"
    local state="UNKNOWN"
    local mac="无（可能未启用或虚拟网卡）"
    local iface_type="虚拟网卡"

    # 检查 ip 命令是否存在
    if ! check_dependencies "ip"; then
        return 1
    fi

    # 获取网卡状态
    local state_result=$(ip -o link show "$iface" 2>/dev/null | awk '{print $9}')
    [ -n "$state_result" ] && state="$state_result"

    # 获取 MAC 地址
    local mac_result=$(ip link show "$iface" 2>/dev/null | awk '/ether/ {print $2}')
    [ -n "$mac_result" ] && mac="$mac_result"

    # 判断网卡类型
    if [ -e "/sys/class/net/$iface/device" ]; then
        iface_type="物理网卡"
    fi

    echo "$state|$mac|$iface_type"
}

# 获取网卡 IP 地址信息
function get_interface_ip_info() {
    local iface="$1"
    local ipv4="null"
    local ipv6="null"

    # 检查 ip 命令是否存在
    if ! check_dependencies "ip"; then
        echo "$ipv4|$ipv6"
        return 1
    fi

    # 获取 IPv4 地址
    local ipv4_result=$(ip -4 addr show "$iface" 2>/dev/null | awk '/inet / {print $2}' | cut -d'/' -f1 | head -n 1)
    [ -n "$ipv4_result" ] && ipv4="$ipv4_result"

    # 获取 IPv6 地址
    local ipv6_result=$(ip -6 addr show "$iface" 2>/dev/null | awk '/inet6 / {print $2}' | cut -d'/' -f1 | head -n 1)
    [ -n "$ipv6_result" ] && ipv6="$ipv6_result"

    echo "$ipv4|$ipv6"
}

# 获取网卡流量统计信息
function get_interface_stats() {
    local iface="$1"
    local rx_bytes="null"
    local tx_bytes="null"

    # 检查 ip 命令是否存在
    if ! check_dependencies "ip"; then
        echo "$rx_bytes|$tx_bytes"
        return 1
    fi

    local rx_tx_stats=$(ip -s link show "$iface" 2>/dev/null)
    if [ -n "$rx_tx_stats" ]; then
        local rx_result=$(echo "$rx_tx_stats" | awk '/RX:/ {getline; print $1}' 2>/dev/null)
        local tx_result=$(echo "$rx_tx_stats" | awk '/TX:/ {getline; print $1}' 2>/dev/null)
        [ -n "$rx_result" ] && rx_bytes="$rx_result"
        [ -n "$tx_result" ] && tx_bytes="$tx_result"
    fi

    echo "$rx_bytes|$tx_bytes"
}

# 获取网卡硬件信息（仅物理网卡）
function get_interface_hardware_info() {
    local iface="$1"
    local iface_type="$2"
    local speed="null"
    local duplex="null"
    local auto_neg="null"

    # 只对物理网卡获取硬件信息
    if [ "$iface_type" != "物理网卡" ]; then
        echo "$speed|$duplex|$auto_neg"
        return 0
    fi

    # 检查 ethtool 命令是否存在
    if ! check_dependencies "ethtool"; then
        echo "$speed|$duplex|$auto_neg"
        return 0
    fi

    # 检查是否有 sudo 权限
    if ! sudo -n true 2>/dev/null; then
        echo "$speed|$duplex|$auto_neg"
        return 0
    fi

    local ethtool_out=$(sudo ethtool "$iface" 2>/dev/null)
    if [ -n "$ethtool_out" ]; then
        local speed_result=$(echo "$ethtool_out" | awk -F': ' '/Speed:/ {print $2}' | head -n 1)
        local duplex_result=$(echo "$ethtool_out" | awk -F': ' '/Duplex:/ {print $2}' | head -n 1)
        local auto_neg_result=$(echo "$ethtool_out" | awk -F': ' '/Auto-negotiation:/ {print $2}' | head -n 1)

        [ -n "$speed_result" ] && speed="$speed_result"
        [ -n "$duplex_result" ] && duplex="$duplex_result"
        [ -n "$auto_neg_result" ] && auto_neg="$auto_neg_result"
    fi

    echo "$speed|$duplex|$auto_neg"
}

# 获取所有网络接口列表
function get_network_interfaces() {
    if [ ! -d "/sys/class/net" ]; then
        echo "错误: 无法访问 /sys/class/net 目录" >&2
        return 1
    fi
    local interfaces=$(ls /sys/class/net/ 2>/dev/null | grep -v lo)
    if [ -z "$interfaces" ]; then
        echo "警告: 未找到任何网络接口" >&2
        return 1
    fi

    echo "$interfaces"
}

# 主函数：获取网络信息
function get_network_info(){
    # 检查基本命令是否存在
    if ! check_dependencies "ip"; then
        echo "[]"
        return 1
    fi

    # 获取网络接口列表
    interfaces=$(get_network_interfaces)
    if [ $? -ne 0 ]; then
        echo "[]"
        return 1
    fi

    # 输出 JSON 数组开头
    echo "["

    local first=true

    # 遍历所有网络接口
    for iface in $interfaces; do
        # 获取基础信息
        basic_info=$(get_interface_basic_info "$iface")
        if [ $? -ne 0 ]; then
            continue  # 跳过这个接口，继续处理下一个
        fi

        local state=$(echo "$basic_info" | cut -d'|' -f1)
        local mac=$(echo "$basic_info" | cut -d'|' -f2)
        local iface_type=$(echo "$basic_info" | cut -d'|' -f3)

        # 获取 IP 信息
        local ip_info=$(get_interface_ip_info "$iface")
        local ipv4=$(echo "$ip_info" | cut -d'|' -f1)
        local ipv6=$(echo "$ip_info" | cut -d'|' -f2)

        # 获取流量统计
        local stats_info=$(get_interface_stats "$iface")
        local rx_bytes=$(echo "$stats_info" | cut -d'|' -f1)
        local tx_bytes=$(echo "$stats_info" | cut -d'|' -f2)

        # 获取硬件信息
        local hw_info=$(get_interface_hardware_info "$iface" "$iface_type")
        local speed=$(echo "$hw_info" | cut -d'|' -f1)
        local duplex=$(echo "$hw_info" | cut -d'|' -f2)
        local auto_neg=$(echo "$hw_info" | cut -d'|' -f3)

        # 构造 JSON 对象
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi

        output_network_json "$iface" "$state" "$iface_type" "$mac" "$ipv4" "$ipv6" "$rx_bytes" "$tx_bytes" "$speed" "$duplex" "$auto_neg"
    done

    # JSON 数组结尾
    echo ""
    echo "]"
}


# 获得存储的信息，包括子级存储结构
function get_storage_info(){
    if ! check_dependencies "lsblk"; then
        return 1
    fi
    # 直接用命令输出json格式
    storage_info=`lsblk -J -o NAME,TYPE,FSTYPE,PTTYPE,SIZE,MOUNTPOINT,PARTUUID,UUID`
    storage_info=`python3 $current_dir/storage_info_json.py "$storage_info"`
    
    echo "$storage_info"

}

if [ "$1" == "cpu" ]; then
    get_cpu_info
elif [ "$1" == "network" ]; then
    get_network_info
elif [ "$1" == "system" ]; then
    get_system_info
elif [ "$1" == "os_system" ]; then
    get_os_system_info
elif [ "$1" == "bios" ]; then
    get_bios_info
elif [ "$1" == "storage" ]; then
    get_storage_info
fi
