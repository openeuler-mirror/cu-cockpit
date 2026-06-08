<template>

  <!--   你的自定义受控组件-->
  <el-select-v2
      v-model="data"
      :options="options"
      style="width: 100%;"
      :clearable="true"
      :props="selectProps"
      @change="onDataChange"

  />
</template>
<script lang="ts" setup>

import {ref, defineComponent, watch, computed, toRefs, toRaw, onMounted} from 'vue'
import {useUi} from "@fast-crud/fast-crud";
import {request} from "/@/utils/service";

const props = defineProps({
  dict: { // 接收来自FastCrud配置中的dict数据
    type: Array,
    required: true,
  },
  modelValue: {}
})
const emit = defineEmits(['update:modelValue'])
// 获取数据
const dataList = ref([])

function getData(params) {
  request({
    url: props.dict.url,
    params: params
  }).then(res => {
    dataList.value = res.data
  })

}

// template上使用data
const data = ref()
// const data = computed({
//   get: () => {
//     console.log("有默认值", props.modelValue)
//     //getData({id:props.modelValue})
//
//     console.log(11, dataList)
//     // const {data} = res
//     // console.log("get",data[0][selectProps.value.label])
//     if (dataList && dataList.length === 1) {
//       return dataList[0][selectProps.value.value]
//     } else {
//       // console.log("aa",res.data)
//       return props.modelValue
//     }
//     // return props.modelValue
//   },
//   set: (val) => {
//     //data.value =  val
//     return val
//   }
// })
const options = ref([])
const selectProps = ref({
  label: 'label',
  value: 'value'
})
</script>
<style scoped lang="scss">
</style>
