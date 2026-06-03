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
</script>
<style scoped lang="scss">
</style>
