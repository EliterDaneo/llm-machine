import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import { setupContentProtection } from './utils/contentProtection'
import { useToast } from './composables/useToast'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

const protectionEnabled =
    import.meta.env.PROD || import.meta.env.VITE_FORCE_CONTENT_PROTECTION === 'true'

if (protectionEnabled) {
    const toast = useToast()
    setupContentProtection({
        onDevtoolsDetected: () => {
            toast.warning('DevTools terdeteksi terbuka pada halaman ini.', 5000)
        },
    })
}
