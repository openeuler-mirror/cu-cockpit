#!/bin/bash

# 检查依赖,看命令是否存在
function check_dependencies() {
    operation=$1

    if ! command -v $operation &> /dev/null; then
        echo "错误: $operation 命令不可用，请安装 $operation 包" >&2
        return 1
    fi
    return 0
}

# 输出cpu的JSON对象
function output_cpu_json() {
    local cpu_total_percent="$1"
    local user_percent="$2"
    local system_percent="$3"
    local idle_percent="$4"
    local load_average="$5"

    # 构造完整的 cpu_JSON 输出
cat <<EOF
{
  "cpu": {
    "total_utilization_percent": "$cpu_total_percent%",
    "user_percent": "$user_percent%",
    "system_percent": "$system_percent%",
    "idle_percent": "$idle_percent%",
    "load_average": "$load_average"
  }
}
EOF

}

# ========== CPU 信息 ==========
function get_cpu_info(){
    if ! check_dependencies "top -bn1"; then
        return 1
    fi
    # ====== 1. CPU 信息 ======
    # CPU 型号
    cpu_line=$(top -bn1 | grep '^%Cpu(s):')
    user=$(echo "$cpu_line" | sed -n 's/.*: *\([0-9.]\+\) us.*/\1/p')
    system=$(echo "$cpu_line" | sed -n 's/.*us, *\([0-9.]\+\) sy.*/\1/p')
    idle=$(echo "$cpu_line" | sed -n 's/.*ni, *\([0-9.]\+\) id.*/\1/p')
    load_average=$(uptime | awk -F 'load average: ' '{print $2}' | awk -F ', ' '{print "1分钟:", $1, "5分钟:", $2, "15分钟:", $3}')
    # 转换为带百分号的字符串
    cpu_total_percent=$(echo "scale=1; 100 - $idle" | bc)

    # 如果以 . 开头（如 .8），补零变成 0.8
    if [[ "$cpu_total_percent" == .* ]]; then
        cpu_total_percent="0${cpu_total_percent}"
    fi

    # 加上百分号
    cpu_total_percent="${cpu_total_percent}"
    user_percent="${user}"
    system_percent="${system}"
    idle_percent="${idle}"

    # 输出cpu_json
    output_cpu_json "$cpu_total_percent" "$user" "$system" "$idle" "$load_average"
}


# 输出memory的JSON对象
function output_memory_json() {
    local mem_total_mb="$1"
    local mem_used_mb="$2"
    local mem_available_mb="$3"
    local swap_total_mb="$4"
    local swap_used_mb="$5"
    local swap_free_mb="$6"
    # 构造完整的memory_JSON 输出
cat <<EOF
{
  "memory": {
    "total_mb": $mem_total_mb,
    "used_mb": $mem_used_mb,
    "available_mb": $mem_available_mb,
    "swap_total_mb": $swap_total_mb,
    "swap_used_mb": $swap_used_mb,
    "swap_free_mb": $swap_free_mb
  }
}
EOF

}



# ========== memory 信息 ==========
function get_memory_info(){

    # ========== 内存信息 ==========
    mem_total_kb=$(grep 'MemTotal:' /proc/meminfo | awk '{print $2}')
    mem_available_kb=$(grep 'MemAvailable:' /proc/meminfo | awk '{print $2}')
    swap_total_kb=$(grep 'SwapTotal:' /proc/meminfo | awk '{print $2}')
    swap_free_kb=$(grep 'SwapFree:' /proc/meminfo | awk '{print $2}')
    swap_used_kb=$((swap_total_kb - swap_free_kb))

    # KB转为Mb
    mem_total_mb=$((mem_total_kb / 1024))
    mem_available_mb=$((mem_available_kb / 1024))
    mem_used_mb=$((mem_total_mb -mem_available_mb))
    swap_total_mb=$((swap_total_kb / 1024))
    swap_used_mb=$((swap_used_kb / 1024))
    swap_free_mb=$((swap_free_kb / 1024))

    # 输出memory_json
    output_memory_json "$mem_total_mb" "$mem_used_mb" "$mem_available_mb" "$swap_total_mb" "$swap_used_mb" "$swap_free_mb"
}


# 输出service_memory的JSON对象
function output_service_memory_json() {
    local top5="$1"
    echo '{'
    echo '  "service_memory": {'
    first=true
    echo "$top5" | while read -r unit bytes; do
        service_name=$(echo "$unit" | awk -F '.service' '{print $1}')
        mem_mb=$(echo "scale=2; $bytes / 1024 / 1024" | bc)
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        echo -n "    \"${service_name}\": \"${mem_mb}MB\""
    done
    echo
    echo '  }'
    echo '}'
}

# ========== service_memory 信息 ==========
function get_top_memory_services() {
    # 1. 获取运行中的服务列表
    services=$(systemctl list-units --type=service --state=running | awk '{print $1}' | grep -vE 'loaded|UNIT|LIST')

    # 2. 获取每个服务的内存信息
    memory_info=$(echo "$services" | xargs -I {} sh -c 'echo -n "{}: "; systemctl show {} --property=MemoryCurrent --no-pager 2>/dev/null || echo "N/A"')

    # 3. 过滤掉没有内存信息的服务
    valid_memory=$(echo "$memory_info" | grep -v 'N/A$')

    # 4. 格式化输出为 "服务名 字节数" 的格式
    formatted=$(echo "$valid_memory"  | awk -F': MemoryCurrent=' '{print $1, $2}')

    # 5. 按内存大小排序，取前5个
    top5=$(echo "$formatted" | sort -k2 -nr | head -n 5)

    # 6. 调用紧凑JSON输出函数
    output_service_memory_json "$top5"
}


# 输出disk的JSON对象
function output_disk_json() {

    local disk_total="$1"
    local disk_used="$2"
    local disk_free="$3"
    local disk_boot_total="$4"
    local disk_boot_used="$5"
    local disk_boot_free="$6"
    # 构造完整的disk_JSON 输出

cat <<EOF
{
  "total_disk": {
    "total": "$disk_total",
    "used": "$disk_used",
    "free": "$disk_free"
  },
  "boot_disk": {
    "boot_total": "$disk_boot_total",
    "boot_used": "$disk_boot_used",
    "boot_free": "$disk_boot_free"
  }
}
EOF

}

# ========== disk 信息 ==========
function get_disk_info(){
  # ========== 磁盘信息（默认根分区 /) ==========
  disk_info=$(df -h / | tail -n 1)
  disk_total=$(echo $disk_info | awk '{print $2}')
  disk_used=$(echo $disk_info | awk '{print $3}')
  disk_free=$(echo $disk_info | awk '{print $4}')

  # ========== 磁盘信息（默认/boot分区 /) ==========
  disk_boot_info=$(df -h /boot | tail -n 1)
  disk_boot_total=$(echo $disk_boot_info | awk '{print $2}')
  disk_boot_used=$(echo $disk_boot_info | awk '{print $3}')
  disk_boot_free=$(echo $disk_boot_info | awk '{print $4}')

  # 输出根目录和/boot目录磁盘大小的json格式
  output_disk_json "$disk_total" "$disk_used" "$disk_free" "$disk_boot_total" "$disk_boot_used" "$disk_boot_free"
}



function output_network_json() {

    local iface="$1"
    local rx="$2"
    local tx="$3"
    # 构造完整的network_JSON 输出

cat <<EOF
{
    "interface_name": "$iface",
    "rx": "$rx B/S",
    "tx": "$tx B/s"

}
EOF


}

function get_rx_tx_info(){
    iface=$1
    rx_path="/sys/class/net/$iface/statistics/rx_bytes"
    tx_path="/sys/class/net/$iface/statistics/tx_bytes"

    if [ -r "$rx_path" ] && [ -r "$tx_path" ]; then
        rx1=$(<"$rx_path")
        tx1=$(<"$tx_path")
        sleep 1
        rx2=$(<"$rx_path")
        tx2=$(<"$tx_path")
    else
        # 回退到 ip -s link
        read rx1 tx1 <<< $(ip -s link show "$iface" | awk '
            /RX:/ {getline; rx=$1}
            /TX:/ {getline; tx=$1; print rx, tx; exit}
        ')
        sleep 1
        read rx2 tx2 <<< $(ip -s link show "$iface" | awk '
            /RX:/ {getline; rx=$1}
            /TX:/ {getline; tx=$1; print rx, tx; exit}
        ')
    fi
    # ===== 计算差值 =====
    delta_rx=$((rx2 - rx1))
    delta_tx=$((tx2 - tx1))
    echo "$delta_rx,$delta_tx"
}

# 主函数：获取网络信息
function get_network_info(){
    # 依赖检查
    if ! check_dependencies "ip"; then
        echo "[]"
        return 1
    fi

    echo "{"
    echo '"network_interfaces":'
    echo "["

    # 获取接口列表
    ifaces=$(ip -o link show | awk -F': ' '{print $2}')

    # 并行采集：每个接口输出一行 iface|rx|tx，最后一次性收集
    nw_lines=$( (
        for iface in $ifaces; do
        {
            rx_tx=$(get_rx_tx_info "$iface")
            rx=${rx_tx%%,*}
            tx=${rx_tx##*,}
            printf '%s|%s|%s\n' "$iface" "$rx" "$tx"
        } &
        done
        wait
    ) )

    # 串行输出 JSON，确保逗号正确
    local first=true
    while IFS='|' read -r iface rx tx; do
        [ -z "$iface" ] && continue
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        output_network_json "$iface" "$rx" "$tx"
    done <<< "$nw_lines"

    echo "]"
    echo "}"
}



# ========== 全部信息 ==========
# 拼接上述所有json

function output_all_json() {
    # 调用各自的函数，收集输出
    cpu_json=$(get_cpu_info)
    memory_json=$(get_memory_info)
    top_memory_services_json=$(get_top_memory_services)
    disk_json_json=$(get_disk_info)
    network_json=$(get_network_info)

    # 拼接成数组
    echo "["
    echo "$cpu_json,"
    echo "$memory_json,"
    echo "$top_memory_services_json,"
    echo "$disk_json_json,"
    echo "$network_json"
    echo "]"
}

type=$1

if [ "$type" == "cpu" ]; then
    get_cpu_info
elif [ "$1" == "memory" ]; then
    get_memory_info
elif [ "$1" == "memory_service" ]; then
    get_top_memory_services
elif [ "$1" == "disk" ]; then
    get_disk_info
elif [ "$type" == "network" ]; then
    get_network_info
elif [ "$1" == "all" ]; then
    output_all_json
fi
