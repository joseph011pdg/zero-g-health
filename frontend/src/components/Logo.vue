<template>
  <!-- Logo Zero G Health (estilo 3): monograma "0G" en serif, cruz médica ámbar y línea base -->
  <svg :width="size" :height="size" viewBox="0 0 84 84" role="img" :aria-label="label" class="zg-logo" :class="{ inverse, blue }">
    <rect class="bg" x="2" y="2" width="80" height="80" />
    <text class="mono" x="40" y="58" text-anchor="middle">0G</text>
    <path class="cross" d="M60 18v10M55 23h10" stroke-width="3.5" stroke-linecap="round" />
    <path class="base" d="M12 70h60" stroke-width="2" />
  </svg>
</template>

<script setup>
defineProps({ size: { type: Number, default: 28 }, inverse: Boolean, blue: Boolean, label: { type: String, default: 'Zero G Health' } })
</script>

<style scoped>
.zg-logo { display: block; flex: none; overflow: visible; }
.bg { fill: var(--navy); }
.mono { font-family: var(--serif); font-weight: 600; font-size: 44px; fill: #ffffff; }
.cross { stroke: #f2a93b; fill: none; }
.base { stroke: #ffffff; opacity: .4; }
/* Versión azul NASA con letras blancas y borde fino: se distingue sobre el azul marino */
.blue .bg { fill: var(--blue); stroke: rgba(255, 255, 255, .35); stroke-width: 2; }
.blue .base { stroke: #ffffff; opacity: .55; }
/* Versión sobre fondo azul marino: cuadro blanco, letras marino */
.inverse .bg { fill: #ffffff; }
.inverse .mono { fill: var(--navy); }
.inverse .cross { stroke: #c9780a; }
.inverse .base { stroke: var(--navy); }
</style>
