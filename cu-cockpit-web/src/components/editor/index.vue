<template>

	<div class="editor-container">
		<Toolbar :editor="editorRef" :mode="mode" />
		<Editor
			:mode="mode"
			:defaultConfig="state.editorConfig"
			:style="{ height }"
			v-model="state.editorVal"
			@onCreated="handleCreated"
			@onChange="handleChange"
		/>
	</div>
</template>
<script setup lang="ts" name="wngEditor">

import '@wangeditor/editor/dist/css/style.css';
import { reactive, shallowRef, watch, onBeforeUnmount } from 'vue';
import { IDomEditor } from '@wangeditor/editor';
import { Toolbar, Editor } from '@wangeditor/editor-for-vue';

// 定义父组件传过来的值
const props = defineProps({
	// 是否禁用
	disable: {
		type: Boolean,
		default: () => false,
	},
	// 内容框默认 placeholder
	placeholder: {
		type: String,
		default: () => '请输入内容...',
	},
	// 模式，可选 <default|simple>，默认 default
	mode: {
		type: String,
		default: () => 'default',
	},
	// 高度
	height: {
		type: String,
		default: () => '310px',
	},
	// 双向绑定，用于获取 editor.getHtml()
	getHtml: String,
	// 双向绑定，用于获取 editor.getText()
	getText: String,
});

// 定义子组件向父组件传值/事件
const emit = defineEmits(['update:getHtml', 'update:getText']);

// 定义变量内容
const editorRef = shallowRef();
</script>
