<template>
  <div class="box-container">
    <!-- 2025-0903 --> 
    <el-alert title="Web 控制台正运行于限制访问模式。" type="warning" show-icon :closable="false" style="border: 0px;margin-bottom: 20px" v-if="u_Permission != 'root'"/>
    <overviewHeader />
    <div class="card-container">
      <indicator class="card-item" />
      <system class="card-item" />
    </div>
  </div>
</template>

<script lang="ts" setup name="overviewIndex">
import overviewHeader from './components/headerPage.vue'
import system from './components/systemPage.vue'
import indicator from './components/indicatorPage.vue'
import { storeToRefs } from 'pinia'; 
import { userPermissiom } from '/@/stores/userPermissiom'; 
const storeUserPermissiom = userPermissiom();
const { u_Permission } = storeToRefs(storeUserPermissiom);
</script>

<style scoped lang="scss">
.box-container {
  padding: 15px 20px;

  .card-container {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    margin-top: 20px;

    .card-item {
      flex: 1;
    }
  }

  @media (max-width: 1500px) {
    .card-container {
      flex-direction: column;
    }
  }
}
</style>
