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
</script>
<style scoped lang="scss">
</style>