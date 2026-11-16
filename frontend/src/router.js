import { createRouter, createWebHistory } from 'vue-router'
import Crew from './views/Crew.vue'
import Persona from './views/Persona.vue'
import Lab from './views/Lab.vue'
import Tierra from './views/Tierra.vue'
import English from './views/English.vue'

//RUTAS en inglés; las rutas antiguas en español redirigen
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Crew, meta: { title: 'Crew' } },
    { path: '/crew/:id', component: Persona, props: true, meta: { title: 'Profile' } },
    { path: '/lab', redirect: '/lab/simulator' },
    { path: '/lab/:tab', component: Lab, props: true, meta: { title: 'Laboratory' } },
    { path: '/reports', component: Tierra, meta: { title: 'Reports' } },
    { path: '/about', component: English, meta: { title: 'About' } },
    { path: '/en', redirect: '/' },
    { path: '/persona/:id', redirect: (to) => `/crew/${to.params.id}` },
    { path: '/salud/:id', redirect: (to) => `/crew/${to.params.id}` },
    { path: '/tierra', redirect: '/reports' },
    { path: '/laboratorio/:tab?', redirect: (to) => `/lab/${{ validacion: 'validation', datos: 'data', ciencia: 'science' }[to.params.tab] || 'simulator'}` },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 110, behavior: 'smooth' } : { top: 0 })
})

//TÍTULO de pestaña por vista ("BASAL · Alerts")
router.afterEach((to) => {
  const t = to.path === '/' && to.hash === '#alerts' ? 'Alerts' : to.meta.title
  document.title = t ? `Zero G Health · ${t}` : 'Zero G Health'
})

export default router
