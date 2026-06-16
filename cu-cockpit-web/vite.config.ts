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

const viteConfig = defineConfig(async (mode: ConfigEnv) => {
    const env = loadEnv(mode.mode, process.cwd());
    // 当Vite构建时，生成版本文件
    generateVersionFile()
    // 动态加载插件
    const vueJsxPlugin = await getVueJsxPlugin();
    const plugins = [
        vue(),
        vueSetupExtend()
    ];

    // 如果 JSX 插件加载成功，则添加
    if (vueJsxPlugin) {
        plugins.push(vueJsxPlugin);
    }
    return {
        plugins,
        root: process.cwd(),
        resolve: { alias },
        base: mode.command === 'serve' ? './' : env.VITE_PUBLIC_PATH,
        optimizeDeps: {
            include: ['element-plus/es/locale/lang/zh-cn', 'element-plus/es/locale/lang/en', 'element-plus/es/locale/lang/zh-tw'],
        },
        server: {
            host: '0.0.0.0',
            port: env.VITE_PORT as unknown as number,
            open: true,
            hmr: true,
            proxy: {
                '/api/terminal/connect': {
                    target: 'http://172.25.14.141:8001/',
                    ws: false,
                    changeOrigin: false,
                    rewrite: (path) => path.replace(/^\/api\/terminal\/connect/, ''),
                },
                '/api/terminal/ws': {
                    target: 'http://172.25.14.141:8001/ws',
                    ws: true,
                    changeOrigin: false,
                    rewrite: (path) => path.replace(/^\/api\/terminal\/ws/, ''),
                },
                '/api': {
                    target: 'http://172.25.14.141:8080',
                    ws: false,
                    changeOrigin: true,
                }
            },
        },
        build: {
            outDir: env.VITE_DIST_PATH || 'dist',
            chunkSizeWarningLimit: 1500,
            rollupOptions: {
                output: {
                    entryFileNames: `assets/[name].[hash].js`,
                    chunkFileNames: `assets/[name].[hash].js`,
                    assetFileNames: `assets/[name].[hash].[ext]`,
                    compact: true,
                    manualChunks: {
                        vue: ['vue', 'vue-router', 'pinia'],
                        echarts: ['echarts'],
                    },
                },
            },
        },
        css: { preprocessorOptions: { css: { charset: false } } },
        define: {
            __VUE_I18N_LEGACY_API__: JSON.stringify(false),
            __VUE_I18N_FULL_INSTALL__: JSON.stringify(false),
            __INTLIFY_PROD_DEVTOOLS__: JSON.stringify(false),
            __VERSION__: JSON.stringify(process.env.npm_package_version),
        },
    };
});

export default viteConfig;
