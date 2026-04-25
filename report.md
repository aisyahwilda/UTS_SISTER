# Report UTS Aggregator

## 1. Latar Belakang

Sistem event-driven sering menghadapi duplicate delivery dan kebutuhan idempotency. Proyek ini membangun aggregator lokal yang memproses event secara asynchronous dan tahan restart untuk deduplikasi.

## 2. Tujuan

- Menerima event single/batch via HTTP.
- Menjamin idempotency berbasis `(topic, event_id)`.
- Menyediakan statistik operasional dan observability sederhana.

## 3. Desain Arsitektur

Komponen utama:

- `src/main.py`: API FastAPI, queue in-memory, lifecycle worker.
- `src/models.py`: validasi skema event (Pydantic).
- `src/queue_worker.py`: consumer async dari queue.
- `src/dedup_store.py`: dedup store SQLite persisten lokal.
- `src/storage.py`: penyimpanan event unik yang telah diproses.
# Report UTS Aggregator

## 1. Ringkasan Sistem dan Arsitektur

Sistem ini adalah layanan aggregator event berbasis Python dengan FastAPI dan `asyncio`. Layanan menerima event melalui HTTP, memasukkannya ke antrean internal in-memory, lalu memprosesnya secara asinkron melalui consumer worker. Event unik disimpan, sedangkan duplikasi dibuang berdasarkan pasangan `(topic, event_id)`.

### Diagram Sederhana

```text
Publisher / Client
  |
  v
POST /publish
  |
  v
In-memory Queue (asyncio.Queue)
  |
  v
Queue Worker / Consumer
  |
  +--> Dedup Store (SQLite lokal)
  |
  +--> Event Storage (event unik)
  |
  +--> Stats (received, unique_processed, duplicate_dropped, topics, uptime)
```

### Komponen Utama

- `src/main.py`: entrypoint aplikasi FastAPI, lifecycle worker, dan endpoint API.
- `src/models.py`: validasi skema event.
- `src/queue_worker.py`: consumer yang memproses event dari queue.
- `src/dedup_store.py`: dedup store SQLite lokal dan persisten.
- `src/storage.py`: penyimpanan event unik per topic.
- `src/stats.py`: metrik runtime dan snapshot statistik.
- `src/publisher_sim.py`: simulasi duplicate delivery untuk skenario at-least-once.

## 2. Keputusan Desain

### 2.1 Idempotency

Idempotency diterapkan dengan key dedup `(topic, event_id)`. Satu event dengan key yang sama hanya diproses sekali meskipun diterima berkali-kali. Pendekatan ini sesuai untuk aggregator karena identitas event ditentukan oleh topik dan ID uniknya.

### 2.2 Dedup Store

Dedup store menggunakan SQLite lokal agar data dedup tetap ada setelah restart container. Pilihan SQLite dipakai karena:

- sederhana dan lokal-only,
- tidak membutuhkan layanan eksternal,
- mendukung constraint `PRIMARY KEY` untuk mencegah duplikasi,
- cocok untuk skenario tugas yang menekankan persistensi restart.

### 2.3 Ordering

Total ordering global tidak diwajibkan untuk kasus ini. Yang utama adalah event unik diproses idempoten dan hasilnya konsisten per key dedup. Queue internal tetap mempertahankan urutan pemrosesan pada satu instance, tetapi duplikasi dapat dibuang saat diproses sehingga urutan akhir yang tersimpan tidak harus identik dengan urutan masuk mentah.

### 2.4 Retry dan Reliability

Reliability disimulasikan dengan publisher yang dapat mengirim event duplikat (at-least-once delivery). Jika container restart, dedup store SQLite tetap mencegah event yang sama diproses ulang selama file database lokal masih tersedia atau di-mount sebagai volume.

## 3. Analisis Performa dan Metrik

### 3.1 Metrik yang Diukur

- `received`: jumlah event yang diterima endpoint `/publish`.
- `unique_processed`: jumlah event unik yang berhasil diproses.
- `duplicate_dropped`: jumlah event duplikat yang dibuang.
- `topics`: daftar topik yang sudah diproses.
- `uptime`: lama layanan berjalan.

### 3.2 Hasil Uji

Unit test mencakup skenario berikut:

- event single dan batch,
- duplikasi event,
- persistensi dedup setelah restart simulasi,
- validasi skema event,
- konsistensi `/events` dan `/stats`,
- stress test kecil,
- stress test skala 5.000 event dengan sekitar 20% duplikasi.

### 3.3 Catatan Performa

Sistem tetap responsif karena pemrosesan event dilakukan secara asinkron melalui queue internal. Untuk beban besar, publisher simulator dapat mengirim 5.000 event dengan rasio duplikasi sekitar 20% untuk menguji dedup dan stabilitas layanan.

## 4. Keterkaitan ke Bab 1–7

### Bab 1. Pendahuluan

Menjelaskan masalah duplicate delivery, kebutuhan idempotency, dan tujuan membangun layanan aggregator lokal.

### Bab 2. Tinjauan Pustaka

Menghubungkan konsep FastAPI, asyncio queue, SQLite, at-least-once delivery, dan deduplication dalam sistem event-driven.

### Bab 3. Analisis Kebutuhan

Mencakup kebutuhan input event, endpoint API, dedup persisten, toleransi restart, dan skenario pengujian performa.

### Bab 4. Perancangan Sistem

Menjelaskan arsitektur komponen, alur data, strategi dedup, dan keputusan desain ordering.

### Bab 5. Implementasi

Berisi implementasi pada `src/main.py`, `src/models.py`, `src/queue_worker.py`, `src/dedup_store.py`, `src/storage.py`, dan `src/stats.py`.

### Bab 6. Pengujian dan Hasil

Berisi hasil `pytest`, validasi skema, dedup, persistensi restart, dan stress test 5.000 event.

### Bab 7. Kesimpulan dan Saran

Menyimpulkan bahwa layanan memenuhi kebutuhan dasar aggregator lokal dan menyarankan peningkatan seperti volume persistence yang lebih eksplisit, observability yang lebih kaya, dan pemisahan worker bila skala bertambah.

## 5. Sitasi Buku Utama (APA 7)

> **Catatan:** metadata buku utama perlu diambil dari `docs/buku-utama.pdf`. File PDF tersebut tidak tersedia di workspace ini, jadi bagian berikut disiapkan dalam format APA 7 dan perlu dilengkapi sesuai metadata asli.

### Format Sitasi Buku

Nama Belakang, Inisial. (Tahun). *Judul buku: Subjudul jika ada*. Penerbit. https://doi.org/... atau URL

### Contoh Sitasi dalam Teks

- (Nama Belakang, Tahun)
- Nama Belakang (Tahun)

### Daftar Pustaka

- Nama Belakang, I. (Tahun). *Judul buku: Subjudul jika ada*. Penerbit.
- Jika tersedia DOI/URL, tambahkan setelah penerbit: *Penerbit. https://doi.org/...*

## 6. Kesimpulan

Implementasi sudah mencakup endpoint utama, consumer internal, dedup lokal persisten, logging duplikasi, simulasi at-least-once delivery, dan pengujian performa. Struktur laporan ini disusun agar mudah dipetakan ke Bab 1–7 dan siap dilengkapi dengan metadata buku utama dari PDF referensi.
