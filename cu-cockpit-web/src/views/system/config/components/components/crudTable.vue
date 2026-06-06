<template>

   <div>
     <fs-crud ref="crudRef" v-bind="crudBinding">
     </fs-crud>
   </div>
</template>
<script setup lang="ts">
import {computed, defineComponent, onMounted, watch} from "vue";
import {CreateCrudOptionsProps, CreateCrudOptionsRet, useFs, AddReq,
</script>
