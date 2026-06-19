// Batasan paket langganan. Nilai ini ditampilkan di UI (Pricing, Quota indicator,
// validasi sebelum upload) — sesuaikan dengan logika kuota nyata di backend
// (tabel `quotas`: daily_used, daily_limit, storage_used_bytes) bila berbeda.
export const PLAN_LIMITS = {
  free: {
    label: 'Free',
    price: 0,
    dailyAnalysisLimit: 5,
    maxPagesPerDocument: 20,
    maxFileSizeMB: 10,
    maxStorageMB: 50,
    chatMessagesPerDay: 15,
    features: [
      '5 analisis dokumen / hari',
      'Maks. 20 halaman per PDF',
      'Maks. ukuran file 10 MB',
      'Chat dokumen (15 pesan/hari)',
      'Riwayat analisis 7 hari terakhir',
    ],
  },
  pro: {
    label: 'Pro',
    price: 79000,
    dailyAnalysisLimit: 50,
    maxPagesPerDocument: 150,
    maxFileSizeMB: 50,
    maxStorageMB: 1024,
    chatMessagesPerDay: 300,
    features: [
      '50 analisis dokumen / hari',
      'Maks. 150 halaman per PDF',
      'Maks. ukuran file 50 MB',
      'Chat dokumen (300 pesan/hari)',
      'Riwayat analisis tanpa batas',
      'Prioritas antrian AI',
    ],
  },
  enterprise: {
    label: 'Enterprise',
    price: null, // hubungi sales
    dailyAnalysisLimit: Infinity,
    maxPagesPerDocument: Infinity,
    maxFileSizeMB: 200,
    maxStorageMB: 1024 * 20,
    chatMessagesPerDay: Infinity,
    features: [
      'Analisis dokumen tanpa batas',
      'Tanpa batas jumlah halaman',
      'Maks. ukuran file 200 MB',
      'Chat dokumen tanpa batas',
      'Dukungan prioritas & SLA',
      'Multi-user / tim',
    ],
  },
}

export const ANALYSIS_TYPES = [
  { value: 'summary', label: 'Ringkasan', description: 'Ringkasan inti isi dokumen' },
  { value: 'key_points', label: 'Poin Penting', description: 'Daftar poin-poin kunci' },
  { value: 'recommendations', label: 'Rekomendasi', description: 'Saran & rekomendasi tindak lanjut' },
  { value: 'custom', label: 'Kustom', description: 'Instruksi analisis bebas' },
]

export const DOCUMENT_STATUS = {
  processing: { label: 'Memproses', color: 'bg-highlight-soft text-ink' },
  ready: { label: 'Siap', color: 'bg-stamp-soft text-stamp' },
  failed: { label: 'Gagal', color: 'bg-rubric-soft text-rubric' },
}
