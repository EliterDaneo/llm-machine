// Deterrent terhadap inspect element & copy-paste sembarangan.
// BUKAN proteksi keamanan sungguhan — lihat catatan di chat.

function isAllowed(target) {
    return target.closest?.('.allow-copy, input, textarea, [contenteditable="true"]') !== null
}

function blockContextMenu(e) {
    if (isAllowed(e.target)) return
    e.preventDefault()
}

function blockSelectStart(e) {
    if (isAllowed(e.target)) return
    e.preventDefault()
}

function blockCopyCut(e) {
    if (isAllowed(e.target)) return
    e.preventDefault()
}

function blockDevtoolsShortcuts(e) {
    const key = e.key?.toLowerCase()
    const blocked =
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && ['i', 'j', 'c'].includes(key)) ||
        (e.ctrlKey && key === 'u') // Ctrl+U: view-source

    if (blocked) e.preventDefault()
}

// Heuristik deteksi devtools terbuka, berbasis selisih ukuran window.
// TIDAK akurat 100% — bisa false-positive di layar kecil/zoom browser/mobile.
// Cuma buat warning lunak (mis. toast), JANGAN dipakai buat blokir akses total.
let warningShown = false
function checkDevtools(onDetected) {
    const threshold = 160
    const isOpen =
        window.outerWidth - window.innerWidth > threshold ||
        window.outerHeight - window.innerHeight > threshold

    if (isOpen && !warningShown) {
        warningShown = true
        onDetected?.()
    } else if (!isOpen) {
        warningShown = false
    }
}

export function setupContentProtection({ onDevtoolsDetected } = {}) {
    document.addEventListener('contextmenu', blockContextMenu)
    document.addEventListener('selectstart', blockSelectStart)
    document.addEventListener('copy', blockCopyCut)
    document.addEventListener('cut', blockCopyCut)
    document.addEventListener('keydown', blockDevtoolsShortcuts)

    let interval = null
    if (onDevtoolsDetected) {
        interval = setInterval(() => checkDevtools(onDevtoolsDetected), 1000)
    }

    return function teardown() {
        document.removeEventListener('contextmenu', blockContextMenu)
        document.removeEventListener('selectstart', blockSelectStart)
        document.removeEventListener('copy', blockCopyCut)
        document.removeEventListener('cut', blockCopyCut)
        document.removeEventListener('keydown', blockDevtoolsShortcuts)
        if (interval) clearInterval(interval)
    }
}