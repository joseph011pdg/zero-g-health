import { createRouter, createWebHistory } from 'vue-router'
import Crew from './views/Crew.vue'
import Persona from './views/Persona.vue'
import Lab from './views/Lab.vue'
import Tierra from './views/Tierra.vue'
import English from './views/English.vue'

// Dos destinos en el menú (Tripulación, Laboratorio); Persona se abre desde un retrato y Tierra desde la cabecera.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Crew, meta: { title: 'Tripulación' } },
    { path: '/persona/:id', component: Persona, props: true, meta: { title: 'Ficha' } },
    { path: '/laboratorio', redirect: '/laboratorio/simulador' },
    { path: '/laboratorio/:tab', component: Lab, props: true, meta: { title: 'Laboratorio' } },
    { path: '/tierra', component: Tierra, meta: { title: 'Reportes' } },
    { path: '/en', component: English, meta: { title: 'English summary' } },
    { path: '/salud/:id', redirect: (to) => `/persona/${to.params.id}` },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 110, behavior: 'smooth' } : { top: 0 })
})

// Título de pestaña por vista ("BASAL · Alarmas")
router.afterEach((to) => {
  const t = to.path === '/' && to.hash === '#alarmas' ? 'Alarmas' : to.meta.title
  document.title = t ? `BASAL · ${t}` : 'BASAL'
})

export default router
