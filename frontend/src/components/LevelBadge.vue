<template>
  <span class="lvl" :class="level" :title="title || LEVEL[level]?.label" role="status">
    <Icon :name="LEVEL[level]?.icon || 'minus'" :size="13" :stroke="2.4" />
    <span v-if="!iconOnly">{{ text || LEVEL[level]?.label || level }}</span>
    <span v-else class="sr">{{ LEVEL[level]?.label }}</span>
  </span>
</template>

<script setup>
import Icon from './Icon.vue'
import { LEVEL } from '../store.js'
defineProps({ level: String, text: String, title: String, iconOnly: Boolean })
</script>

<style scoped>
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
</style>
