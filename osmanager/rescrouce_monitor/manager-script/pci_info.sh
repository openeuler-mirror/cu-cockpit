#!/bin/bash

# 检查依赖
check_dependencies() {
    if ! command -v lspci &> /dev/null; then
        echo "错误: lspci 命令不可用，请安装 pciutils 包" >&2
        return 1
    fi
    return 0
}

# 提取等级（类别）并做映射
mapping_kind() {
    local line="$1"
    local raw_class
    raw_class=$(echo "$line" | awk -F': ' '{print $1}' | sed 's/^[^ ]* //')

    case "$raw_class" in
        "USB controller")
            class="Serial bus controller"
            ;;
        "VGA compatible controller")
            class="Display controller"
            ;;
        "SCSI storage controller"|"IDE interface")
            class="Mass storage controller"
            ;;
        "System peripheral")
            class="Generic system peripheral"
            ;;
        "Network controller"|"Ethernet controller")
            class="Network controller"
            ;;
        "Multimedia controller"|"Multimedia audio controller")
            class="Multimedia controller"
            ;;
        "Host bridge"|"PCI bridge"|"ISA bridge"|"Bridge")
            class="Bridge"
            ;;
        *)
            class="$raw_class"
            ;;
    esac
    echo "$class"
}

# 解析 lspci 输出，提取插槽、厂商、型号
parse_pci_line() {
    local line="$1"
    local slot vendor model vendor_model_part full_slot

    slot=$(echo "$line" | awk '{print $1}')
    [ -z "$slot" ] && return 1

    full_slot="0000:$slot"
    vendor_model_part=$(echo "$line" | sed 's/.*: //')

    # 常见厂商特殊处理
    if echo "$vendor_model_part" | grep -q "^Intel Corporation "; then
        vendor="Intel Corporation"
        model=$(echo "$vendor_model_part" | sed 's/^Intel Corporation //')
    elif echo "$vendor_model_part" | grep -q "^VMware "; then
        vendor="VMware"
        model=$(echo "$vendor_model_part" | sed 's/^VMware //')
    elif echo "$vendor_model_part" | grep -q "^Broadcom / LSI "; then
        vendor="Broadcom / LSI"
        model=$(echo "$vendor_model_part" | sed 's/^Broadcom \/ LSI //')
    elif echo "$vendor_model_part" | grep -q "^Ensoniq "; then
        vendor="Ensoniq"
        model=$(echo "$vendor_model_part" | sed 's/^Ensoniq //')
    else
        vendor=$(echo "$vendor_model_part" | awk '{print $1}')
        model=$(echo "$vendor_model_part" | sed "s/^$vendor //")
    fi

    [ -z "$model" ] && model="$vendor_model_part"

    # 输出为全局变量
    PCI_SLOT="$full_slot"
    PCI_VENDOR="$vendor"
    PCI_MODEL="$model"
}

# 输出单个PCI设备的JSON对象
output_pci_json() {
    local class="$1"
    local model="$2"
    local vendor="$3"
    local slot="$4"

    cat <<EOF
      {
        "等级": "$class",
        "型号": "$model",
        "厂商": "$vendor",
        "插槽": "$slot"
      }
EOF
}

# 主函数：获取PCI信息
get_pci_info() {
    if ! check_dependencies; then
        return 1
    fi

    echo "["

    local first=true
    while IFS= read -r line; do
        [ -z "$line" ] && continue

        parse_pci_line "$line" || continue
        class=$(mapping_kind "$line")

        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi

        output_pci_json "$class" "$PCI_MODEL" "$PCI_VENDOR" "$PCI_SLOT"
    done < <(lspci)

    echo ""
    echo "]"
}

# 如果直接运行此脚本，则执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    get_pci_info
fi
