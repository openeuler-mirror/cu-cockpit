<template>

  <!--   你的自定义受控组件-->
  <div>
    <el-tag class="many-to-many-tag" :type="randomType" v-for="(item,index) in data" :key="index">{{item}}</el-tag>
  </div>
</template>
<script lang="ts" setup>
import {watch, ref} from "vue";
</script>
<style scoped>
</style>
