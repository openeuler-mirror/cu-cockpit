<template>

  <div class="custom-input-select">
    <el-input 
      :model-value="inputLabel" 
      :placeholder="placeholder" 
      :disabled="disabled"
      @update:model-value="handleInput" 
      @click="handleInputClick"
      @blur="handleBlur" 
      @keydown="handleKeyDown"
      class="input-with-arrow" 
      :class="{ 'open': showOptions }"> 
    </el-input>
    <div class="options-container" v-show="showOptions && filteredOptions.length">
      <div class="demo">
        <div class="options-cont">
          <div 
            v-for="(option, index) in filteredOptions" 
            :key="option.value" 
            class="option-item"
            :class="{ 'selected': index === selectedIndex }" 
            @mousedown="selectOption(option)"
            @mouseenter="selectedIndex = index">
            {{ option.label }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts" name="inputSelect">

import { ref, watch, PropType } from "vue";

interface Option {
  label: string;
  value: string | number;
}

// 定义props
const props = defineProps({
  value: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array as PropType<Option[]>,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请选择或输入'
  },
  filterable: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

// 定义emits
const emit = defineEmits(['update:value']);

// 定义响应式数据
const inputValue = ref<string | number>(props.value);
const inputLabel = ref<string>('');
const showOptions = ref<boolean>(false);
const filteredOptions = ref<Option[]>([]);
const selectedIndex = ref<number>(-1);

// 更新输入框显示标签
const updateInputLabel = (value: string | number) => {
  const option = props.options.find(opt => opt.value === value);
  inputLabel.value = option ? option.label : String(value);
};

// 更新选中索引
const updateSelectedIndex = () => {
  selectedIndex.value = filteredOptions.value.findIndex(
    item => item.value == inputValue.value
  );
};

// 处理输入
const handleInput = (value: string) => {
  inputLabel.value = value;
  inputValue.value = value;
  emit('update:value', value);
  if (props.filterable) {
    filterOptions(value);
  }
};

// 过滤选项
const filterOptions = (query: string) => {
  if (!query) {
    filteredOptions.value = [...props.options];
    selectedIndex.value = -1;
    return;
  }

  const queryLower = query.toLowerCase();
  filteredOptions.value = props.options.filter(option =>
    option.label.toLowerCase().includes(queryLower)
  );

  selectedIndex.value = filteredOptions.value.length > 0 ? 0 : -1;
};

// 选择选项
const selectOption = (option: Option) => {
  inputLabel.value = option.label;
  inputValue.value = option.value;
  emit('update:value', option.value);
  showOptions.value = false;
};

// 处理焦点事件
const handleFocus = () => {
  if (props.disabled) return;

  showOptions.value = true;
  if (props.filterable) {
    filteredOptions.value = [...props.options];
    updateSelectedIndex();
  }
};
//点击事件
const handleInputClick = () => {
 
  if (props.disabled) return;

  showOptions.value = !showOptions.value;
  if (props.filterable && showOptions.value) {
    filteredOptions.value = [...props.options];
    updateSelectedIndex();
  }
  
};
// 处理失去焦点事件
const handleBlur = () => {
  // 延迟隐藏以便点击选项
  setTimeout(() => {
    showOptions.value = false;
    selectedIndex.value = -1;

    // 如果不是可过滤模式，保持输入框显示对应标签
    if (!props.filterable) {
      updateInputLabel(inputValue.value);
    }
  }, 200);
};

// 处理键盘事件
const handleKeyDown = (e: KeyboardEvent) => {
  if (!showOptions.value) return;

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      selectedIndex.value = Math.min(selectedIndex.value + 1, filteredOptions.value.length - 1);
      break;
    case 'ArrowUp':
      e.preventDefault();
      selectedIndex.value = Math.max(selectedIndex.value - 1, 0);
      break;
    case 'Enter':
      e.preventDefault();
      if (selectedIndex.value >= 0 && filteredOptions.value.length > 0) {
        selectOption(filteredOptions.value[selectedIndex.value]);
      }
      break;
    case 'Escape':
      showOptions.value = false;
      break;
  }
};

// 监听value变化
watch(() => props.value, (newVal) => {
  inputValue.value = newVal;
  updateInputLabel(newVal);
}, { immediate: true });

// 监听options变化
watch(() => props.options, (newOptions) => {
  filteredOptions.value = [...newOptions];
  if (showOptions.value && props.filterable) {
    updateSelectedIndex();
  }
});

// 添加点击外部区域关闭下拉菜单的功能
const handleClickOutside = (event: MouseEvent) => {
  const el = document.querySelector('.custom-input-select');
  if (el && !el.contains(event.target as Node)) {
    showOptions.value = false;
    selectedIndex.value = -1;
  }
};

// 组件挂载时添加事件监听器
import { onMounted, onBeforeUnmount } from "vue";

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>
<style scoped lang="scss">

.selected-value {
  margin-top: 15px;
  padding: 12px;
  background-color: #ecf5ff;
  border-radius: 4px;
  font-size: 14px;
  border-left: 4px solid #409EFF;
}

.selected-value strong {
  color: #409EFF;
}

.custom-input-select {
  position: relative;
}

.options-container {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 999;
  margin-top: -1px;
}

.demo {
  position: relative;
  z-index: 1;
}

.options-cont {
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 0 0 4px 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  max-height: 242px;
  overflow-y: auto;
  margin-top: 7px;
}

/* 添加上方的三角凸起 */
.demo:before {
  content: "";
  position: absolute;
  top: -4px;
  left: calc(50% - 10px);
  width: 10px;
  height: 10px;
  background: white;
  border-top: 1px solid #dcdfe6;
  border-left: 1px solid #dcdfe6;
  transform: rotate(45deg);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 1;
}

.option-item {
  position: relative;
  padding: 0px 15px;
  background: #fff;
  cursor: pointer;
  transition: background 0.3s;
  height: 40px;
  line-height: 40px;
  z-index: 2;
}

.option-item:hover {
  position: relative;
  background: #f5f7fa;
  z-index: 2;
}

.option-item.selected {
  position: relative;
  background: #ecf5ff;
  color: #409EFF;
  z-index: 2;
}

/* 修改箭头样式为线性三角箭头 */
.input-with-arrow {
  position: relative;
}

.input-with-arrow:after {
  content: "";
  position: absolute;
  right: 12px;
  top: 50%;
  width: 8px;
  height: 8px;
  border-left: 1px solid #c0c4cc;
  border-bottom: 1px solid #c0c4cc;
  transform: translateY(-70%) rotate(-45deg);
  transition: transform 0.3s;
  pointer-events: none;
}

.input-with-arrow.open:after {
  transform: translateY(-30%) rotate(135deg);
}

/* 添加滚动条样式 */
.options-cont::-webkit-scrollbar {
  width: 6px;
}

.options-cont::-webkit-scrollbar-thumb {
  background-color: #c0c4cc;
  border-radius: 3px;
}

.options-cont::-webkit-scrollbar-track {
  background-color: #f5f7fa;
}
</style>