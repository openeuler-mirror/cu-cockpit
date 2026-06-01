import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path, {resolve} from 'path';
import vueJsx from "@vitejs/plugin-vue-jsx";
import vueSetupExtend from "vite-plugin-vue-setup-extend";
import { terser } from 'rollup-plugin-terser';
import postcss from 'rollup-plugin-postcss';
import pxtorem from 'postcss-pxtorem';
const pathResolve = (dir: string) => {
  return resolve(__dirname, '.', dir);
};