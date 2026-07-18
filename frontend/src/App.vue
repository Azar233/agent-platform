<template>
  <router-view />
  <VisionPet v-if="showVisionPet" />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import VisionPet from '@/components/VisionPet.vue'

const route = useRoute()
const showVisionPet = computed(() => route.meta.hideVisionPet !== true)

// 根组件仅作为路由出口
</script>

<style>
/* 全局样式已在 global.scss 中定义 */
</style>
