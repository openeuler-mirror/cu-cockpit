<template>
  <main class="inspection-page" aria-label="巡检中心"></main>
</template>

<script setup lang="ts" name="inspectionIndex">
type PlanEditor = {
  id: number | null;
  name: string;
  kind: 'daily' | 'interval' | 'manual';
  time: string;
  minutes: 15 | 30 | 60;
  timezone: string;
  enabled: boolean;
  services: string[];
};
</script>