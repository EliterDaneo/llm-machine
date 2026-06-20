const isProduction = import.meta.env.VITE_MIDTRANS_ENV === 'production'

export const midtransClientKey = isProduction
    ? import.meta.env.VITE_MIDTRANS_CLIENT_KEY_PRODUCTION
    : import.meta.env.VITE_MIDTRANS_CLIENT_KEY_SANDBOX

export const midtransSnapUrl = isProduction
    ? 'https://app.midtrans.com/snap/snap.js'
    : 'https://app.sandbox.midtrans.com/snap/snap.js'

let scriptPromise = null

// Load Snap.js sekali aja (idempotent), lalu window.snap siap dipakai
// buat window.snap.pay(snapToken, { onSuccess, onPending, onError, onClose })
export function loadMidtransSnap() {
    if (scriptPromise) return scriptPromise

    if (!midtransClientKey) {
        console.warn(
            `Midtrans client key kosong untuk mode "${isProduction ? 'production' : 'sandbox'}". ` +
            'Cek .env: VITE_MIDTRANS_CLIENT_KEY_' + (isProduction ? 'PRODUCTION' : 'SANDBOX')
        )
    }

    scriptPromise = new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = midtransSnapUrl
        script.setAttribute('data-client-key', midtransClientKey)
        script.onload = () => resolve()
        script.onerror = () => {
            scriptPromise = null // biar bisa di-retry kalau gagal load
            reject(new Error('Gagal memuat Midtrans Snap.js'))
        }
        document.head.appendChild(script)
    })

    return scriptPromise
}