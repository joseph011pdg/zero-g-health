import { createRouter, createWebHistory } from 'vue-router'
import Overview from './views/Overview.vue'
import Health from './views/Health.vue'
import Registro from './views/Registro.vue'
import Simulator from './views/Simulator.vue'
import Validation from './views/Validation.vue'
import Reports from './views/Reports.vue'

// 6 pantallas que agrupan las 10 vistas de la propuesta
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Overview },                         // 01 Mission Overview + 08 Medical Officer
    { path: '/salud', redirect: () => '/salud/A1' },
    { path: '/salud/:id', component: Health, props: true },     // 02 Astronaut Health + 05 Alerts & Decisions
    { path: '/registro', component: Registro },                 // 03 Daily Check-in + 04 Cognitive Test (+ ingesta F2)
    { path: '/simulador', component: Simulator },               // 06 Mission Simulator
    { path: '/validacion', component: Validation },             // 07 Scientific Validation Lab
    { path: '/reportes', component: Reports },                  // 09 Earth Reports + 10 About the Science
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior: () => ({ top: 0 })
})
