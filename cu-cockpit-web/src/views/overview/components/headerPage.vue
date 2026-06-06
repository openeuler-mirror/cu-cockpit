<template>

    <el-card>
        <div class="box-container">
            <div class="box-item" v-for="item in descriptions" :key="item.key">
                <i class="iconfont" :class="item.icon" :style="{ color: item.color }"></i>
                {{ system[item.key as keyof System] || '' }}
                <el-divider direction="vertical" />
            </div>
            <div class="box-item">
                <el-tag type="success" effect="dark" round>运行中</el-tag>
            </div>
        </div>
    </el-card>
</template>
<script lang="ts" setup name="overviewHeader">
import { onMounted, ref } from 'vue';
import { hardInfo } from '/@/api/run/run';
import { configGet } from '/@/api/config/config';
</script>
<style scoped lang="scss">
</style>
