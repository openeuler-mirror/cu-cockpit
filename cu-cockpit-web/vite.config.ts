import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { defineConfig, loadEnv, ConfigEnv } from 'vite';
import vueSetupExtend from 'vite-plugin-vue-setup-extend';
import { generateVersionFile } from "/@/utils/upgrade";

// 动态导入 vue-jsx 插件（解决 ESM 冲突）
const getVueJsxPlugin = async () => {
    try {
        const { default: vueJsx } = await import('@vitejs/plugin-vue-jsx');
        return vueJsx();
    } catch (error) {
        console.warn('Vue JSX 插件加载失败，跳过使用');
        return null;
    }
};

const pathResolve = (dir: string) => {
    return resolve(__dirname, '.', dir);
};

const alias: Record<string, string> = {
    '/@': pathResolve('./src/'),
    '@great-dream': pathResolve('./node_modules/@great-dream/'),
    '@views': pathResolve('./src/views'),
    'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js',
    '@dvaformflow': pathResolve('./src/viwes/plugins/dvaadmin_form_flow/src/')
};
