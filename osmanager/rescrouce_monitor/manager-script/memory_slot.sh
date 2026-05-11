#!/bin/bash

# ==================== 工具函数 ====================

# 检查依赖工具
check_dependencies() {
    if ! command -v dmidecode &> /dev/null; then
        echo "错误: dmidecode命令不可用，请安装dmidecode包" >&2
        return 1
    fi
    return 0
}

# 检查sudo权限
check_sudo_permission() {
    if ! sudo -n dmidecode -t memory &> /dev/null; then
        echo "错误: 需要sudo权限来运行dmidecode" >&2
        return 1
    fi
    return 0
}

# 获取原始内存数据
get_raw_memory_data() {
    sudo dmidecode -t memory 2>/dev/null
}

# 提取冒号后的值
extract_value() {
    local line="$1"
    echo "$line" | sed 's/.*: //'
}

# 映射技术到内存类型
map_technology_to_type() {
    local tech="$1"
    case "$tech" in
        *DDR5*) echo "DDR5 SDRAM" ;;
        *DDR4*) echo "DDR4 SDRAM" ;;
        *DDR3*) echo "DDR3 SDRAM" ;;
        *DDR2*) echo "DDR2 SDRAM" ;;
        *DDR*)  echo "DDR SDRAM" ;;
        *)      echo "$tech" ;;
    esac
}

# 推断Rank信息
infer_rank() {
    local size="$1"
    local type="$2"
    local rank="$3"
    
    # 如果已有Rank信息，直接返回
    if [[ -n "$rank" ]]; then
        echo "$rank"
        return
    fi
    
    # 如果没有安装模块
    if [[ "$size" == "No Module Installed" ]]; then
        echo "No Module"
        return
    fi

    echo "Unknown"
}

# 构建拓扑信息
build_topology() {

    local bank_locator="$1"
    local topology
    
    if [[ -n "$bank_locator" ]]; then
        topology="$bank_locator"
    else
        topology="未知"
    fi
    
    echo "$topology"
}

# 处理单个内存设备
process_memory_device() {
    local device_data="$1"
    
    # 初始化变量
    local id="" locator="" bank_locator=""
    local type="" size="" status="" rank="" speed="" technology=""
    
    # 解析设备数据
    while IFS= read -r line; do
        case "$line" in
            *"Socket Designation:"*) 
                id=$(extract_value "$line")
                ;;
            *"Locator:"*|*"Bank Locator:"*)
                if [[ "$line" == *"Bank Locator:"* ]]; then
                    bank_locator=$(extract_value "$line")
                else
                    locator=$(extract_value "$line")
                fi
                ;;
            *"Type:"*) 
                type=$(extract_value "$line")
                ;;
            *"Installed Size:"*|*"Size:"*) 
                size=$(extract_value "$line")
                if [[ "$line" == *"No Module Installed"* ]]; then
                    status="空缺"
                else
                    status="当前"
                fi
                ;;
            *"Speed:"*|*"Configured Memory Speed:"*) 
                speed=$(extract_value "$line")
                ;;
            *"Rank:"*) 
                rank=$(extract_value "$line")
                ;;

        esac
    done <<< "$device_data"
    
    # 推断Rank
    local inferred_rank=$(infer_rank "$size" "$type" "$rank")
    
    # 构建拓扑
    local topology=$(build_topology  "$bank_locator" )
    
    # 输出JSON格式
    cat << EOF
  {
    "ID": "${id:-$locator}",
    "内存拓扑": "$topology",
    "类型": "${type:-DRAM}",
    "大小": "${size:-No Module Installed}",
    "状态": "${status:-$(if [[ "$size" == "No Module Installed" ]]; then echo "空缺"; else echo "当前"; fi)}",
    "Rank": "$inferred_rank",
    "速度": "${speed:-Unknown}"
  }
EOF
}

# ==================== 主函数 ====================

# 主内存信息获取函数
get_memory_info() {
    # 检查依赖
    if ! check_dependencies; then
        return 1
    fi
    
    # 检查权限
    if ! check_sudo_permission; then
        return 1
    fi
    
    # 获取原始数据
    local raw_data
    raw_data=$(get_raw_memory_data)
    if [[ -z "$raw_data" ]]; then
        echo "错误: 无法获取内存数据" >&2
        return 1
    fi
    
    # 开始输出JSON
    echo "["
    
    # 分割设备数据并处理
    local first=true
    local current_device=""
    local in_device=false
    
    while IFS= read -r line; do
        if [[ "$line" == "Memory Device" ]]; then
            # 处理前一个设备
            if [[ "$in_device" == true && -n "$current_device" ]]; then
                if [[ "$first" == true ]]; then
                    first=false
                else
                    echo ","
                fi
                process_memory_device "$current_device"
            fi
            
            # 开始新设备
            in_device=true
            current_device=""
        elif [[ "$line" == "" ]]; then
            # 设备结束
            if [[ "$in_device" == true && -n "$current_device" ]]; then
                if [[ "$first" == true ]]; then
                    first=false
                else
                    echo ","
                fi
                process_memory_device "$current_device"
            fi
            in_device=false
            current_device=""
        elif [[ "$in_device" == true ]]; then
            # 累积设备数据
            current_device+="$line"$'\n'
        fi
    done <<< "$raw_data"
    
    # 处理最后一个设备
    if [[ "$in_device" == true && -n "$current_device" ]]; then
        if [[ "$first" == true ]]; then
            first=false
        else
            echo ","
        fi
        process_memory_device "$current_device"
    fi
    
    echo ""
    echo "]"
}

# ==================== 使用示例 ====================
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    get_memory_info
fi
