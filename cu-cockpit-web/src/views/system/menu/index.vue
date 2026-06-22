<template>

	<fs-page>
		<el-row class="menu-el-row">
			<el-col :span="6">
				<div class="menu-box menu-left-box">
					<MenuTreeCom
						ref="menuTreeRef"
						:treeData="menuTreeData"
						@treeClick="handleTreeClick"
						@updateDept="handleUpdateMenu"
						@deleteDept="handleDeleteMenu"
					/>
				</div>
			</el-col>

			<el-col :span="18">
        <el-tabs type="border-card">
          <el-tab-pane label="按钮权限配置" >
            <div style="height: 72vh">
              <MenuButtonCom ref="menuButtonRef" />
            </div>
          </el-tab-pane>
          <el-tab-pane label="列权限配置">
            <div style="height: 72vh">
              <MenuFieldCom ref="menuFieldRef"></MenuFieldCom>
            </div>
          </el-tab-pane>
        </el-tabs>

			</el-col>
		</el-row>

		<el-drawer v-model="drawerVisible" title="菜单配置" direction="rtl" size="500px" :close-on-click-modal="false" :before-close="handleDrawerClose">
			<MenuFormCom
				v-if="drawerVisible"
				:initFormData="drawerFormData"
				:cacheData="menuTreeCacheData"
				:treeData="menuTreeData"
				@drawerClose="handleDrawerClose"
			/>
		</el-drawer>
	</fs-page>
</template>
<script lang="ts" setup name="menuPages">
import { ref, onMounted } from 'vue';
import XEUtils from 'xe-utils';
import { ElMessageBox } from 'element-plus';
import MenuTreeCom from './components/MenuTreeCom/index.vue';
import MenuButtonCom from './components/MenuButtonCom/index.vue';
import MenuFormCom from './components/MenuFormCom/index.vue';
import MenuFieldCom from './components/MenuFieldCom/index.vue';
import { GetList, DelObj } from './api';
import { successNotification } from '/@/utils/message';
import { APIResponseData, MenuTreeItemType } from './types';
</script>
<style lang="scss" scoped>
</style>
