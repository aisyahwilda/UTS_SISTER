# Laporan UTS Sistem Paralel dan Terdistribusi

## Pub-Sub Log Aggregator

**Nama:** Aisyah Wilda Fauziah Amanda
**NIM:** 11231005
**GitHub:** https://github.com/aisyahwilda/UTS_SISTER
**Video Demo:** https://youtu.be/YrOnDY7P2sE?si=cnd9WF6rJ8-KLlpK

## 1. Ringkasan Sistem dan Arsitektur
Sistem yang saya buat adalah sebuah layanan log aggregator sederhana yang menggunakan konsep publish-subscribe. Intinya, sistem ini menerima data event dari berbagai sumber (publisher), lalu memprosesnya tanpa harus mengetahui secara langsung siapa pengirim maupun siapa penerima akhirnya.
Berikut gambaran sederhana arsitektur sistem:

[ Publisher ]
      |
      | HTTP POST (/publish)
      v
[ FastAPI API ]
      |
      v
[ asyncio.Queue ]
      |
      v
[ Worker / Consumer ] ----> [ SQLite (Dedup Store) ]
      |
      v
[ Stored Events ]
      ^
      |
      | HTTP GET (/events, /stats)
      |
[ Client / User ]

Alur kerja sistem ini adalah sebagai berikut:
* Publisher mengirim data ke endpoint `/publish`
* Data akan masuk ke dalam queue (antrian sementara di memori)
* Consumer (worker) mengambil data dari queue
* Sebelum diproses, data akan dicek terlebih dahulu ke database apakah sudah pernah diproses atau belum
* Jika belum → data diproses dan disimpan
* Jika sudah → dianggap duplikat dan tidak diproses lagi

Sistem ini fokus pada dua hal utama, yaitu tidak memproses data yang sama lebih dari satu kali (deduplication) serta tetap dapat berjalan dengan baik walaupun terjadi pengiriman ulang data. Selain itu, sistem menggunakan pendekatan asynchronous agar proses pengiriman event tidak terhambat oleh proses pengecekan dan penyimpanan data.

## 2. Keputusan Desain
### Idempotency
Consumer dirancang agar bersifat idempotent. Artinya, jika event yang sama dikirim berulang kali, hasil akhirnya tetap sama dan tidak menyebabkan data ganda.

### Dedup Store
Sistem menggunakan SQLite sebagai penyimpanan data deduplikasi. Alasan pemilihan SQLite adalah karena ringan, mudah digunakan, dan tidak memerlukan konfigurasi tambahan. Selain itu, data tetap tersimpan walaupun aplikasi di-restart.

### Ordering
Sistem tidak menerapkan total ordering karena dalam kasus ini urutan event tidak terlalu berpengaruh. Yang lebih penting adalah semua event tetap dapat diproses dengan benar.

### Retry
Sistem menggunakan konsep at-least-once delivery, sehingga memungkinkan adanya pengiriman ulang (retry). Duplicate yang muncul akan ditangani oleh mekanisme deduplication di sisi consumer.

## 3. Analisis Performa
Berdasarkan hasil pengujian, sistem mampu menangani ribuan event dengan baik, termasuk yang mengandung duplikasi. Pada pengujian, sistem mampu memproses lebih dari 5.000 event dengan sekitar 20% data duplikat, dan tetap berjalan secara responsif.
Beberapa metrik yang dapat dilihat melalui endpoint `/stats` antara lain:
* `received`: total event yang diterima
* `unique_processed`: event yang berhasil diproses
* `duplicate_dropped`: event yang dibuang karena duplikat
* `topics`: daftar topik yang ada
* `uptime`: lama waktu sistem berjalan

Penggunaan queue asynchronous (`asyncio.Queue`) membuat proses input tetap cepat dan tidak terblokir, meskipun terdapat proses pengecekan ke database.

## 4. Keterkaitan dengan Materi (Bab 1–7)
* **Bab 1:** Sistem ini termasuk sistem terdistribusi dan terdapat trade-off antara performa dan konsistensi.
* **Bab 2:** Menggunakan arsitektur publish-subscribe sehingga publisher dan consumer tidak saling bergantung langsung.
* **Bab 3:** Menggunakan konsep at-least-once delivery sehingga membutuhkan idempotent consumer (Tanenbaum & van Steen, 2023).
* **Bab 4:** `event_id` digunakan sebagai identitas unik untuk mendukung proses deduplication.
* **Bab 5:** Tidak menggunakan total ordering karena tidak terlalu dibutuhkan dalam konteks ini.
* **Bab 6:** Mengatasi kemungkinan duplicate dan crash dengan menggunakan SQLite sebagai penyimpanan persisten.
* **Bab 7:** Sistem ini menggunakan konsep eventual consistency, di mana data akan menjadi konsisten seiring waktu.

## 5. Kesimpulan
Sistem yang dibuat berhasil mengimplementasikan log aggregator sederhana dengan fitur utama seperti deduplication, idempotency, dan pemrosesan asynchronous. Selain itu, sistem ini juga telah diuji menggunakan Docker untuk memastikan kemudahan dalam deployment dan portability.

## 6. Referensi
Tanenbaum, A. S., & van Steen, M. (2023). *Distributed systems: principles and paradigms* (4th ed.). Pearson.

## 7. Cara Menjalankan
Pastikan Docker sudah terinstal pada perangkat.
### Build Image
```bash
docker build -t uts-aggregator .
```
### Run Container
```bash
docker run -p 8080:8080 uts-aggregator
```
