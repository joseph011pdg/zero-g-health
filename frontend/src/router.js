import { createRouter, createWebHistory } from 'vue-router'
import Crew from './views/Crew.vue'
import Persona from './views/Persona.vue'
import Lab from './views/Lab.vue'
import Tierra from './views/Tierra.vue'

// Dos destinos en el menú (Tripulación, Laboratorio); Persona se abre desde un retrato y Tierra desde la cabecera.
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Crew },
    { path: '/persona/:id', component: Persona, props: true },
    { path: '/laboratorio', redirect: '/laboratorio/simulador' },
    { path: '/laboratorio/:tab', component: Lab, props: true },
    { path: '/tierra', component: Tierra },
    { path: '/salud/:id', redirect: (to) => `/persona/${to.params.id}` },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 110, behavior: 'smooth' } : { top: 0 })
})
