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

#### 4. Keterkaitan dengan Materi (Bab 1–7)
### T1 (Bab 1): Karakteristik Sistem Terdistribusi dan Trade-off
Sistem terdistribusi adalah kumpulan beberapa komputer yang saling terhubung melalui jaringan dan bekerja bersama untuk menjalankan suatu tugas. Setiap bagian sistem dapat berjalan secara bersamaan, sehingga proses menjadi lebih cepat dan efisien. Namun, karena terdiri dari banyak komponen, sistem seperti ini juga memiliki risiko gangguan, misalnya salah satu bagian mati atau koneksi terputus. Pada project Pub-Sub Log Aggregator ini, ada beberapa trade-off yang perlu diperhatikan. Jika sistem terlalu fokus pada konsistensi data dan pengurutan sempurna, maka performa bisa menurun. Sebaliknya, jika fokus pada kecepatan dan throughput, maka ada kemungkinan data diterima tidak langsung berurutan. Karena itu, sistem ini lebih mengutamakan efisiensi proses dan deduplication dibanding total ordering.

### T2 (Bab 2): Client-Server dan Publish-Subscribe
Model client-server menggunakan komunikasi langsung antara client dan server. Artinya client harus menghubungi server secara langsung untuk mengirim atau meminta data. Sedangkan pada model publish-subscribe, publisher cukup mengirim event ke sistem tanpa perlu tahu siapa penerimanya. Subscriber juga cukup menerima event sesuai topic yang dibutuhkan. Pada project ini, pendekatan publish-subscribe lebih cocok karena data log bisa dikirim dari banyak sumber secara bersamaan tanpa saling bergantung. Sistem menjadi lebih fleksibel dan mudah dikembangkan.

### T3 (Bab 3): At-least-once, Exactly-once, dan Idempotent Consumer
Dalam sistem terdistribusi, pengiriman pesan bisa mengalami gangguan. Karena itu sering digunakan model **at-least-once delivery**, yaitu pesan dipastikan terkirim minimal satu kali. Kekurangannya, pesan yang sama bisa terkirim ulang. Model **exactly-once** lebih ideal karena pesan hanya diproses satu kali, tetapi implementasinya lebih sulit. Untuk mengatasi hal tersebut, project ini menggunakan konsep **idempotent consumer**. Artinya, jika event yang sama diterima berkali-kali, hasil akhirnya tetap sama karena event duplicate akan ditolak.

### T4 (Bab 4): Topic dan Event ID
Setiap event memiliki topic dan event_id.
- **Topic** digunakan untuk mengelompokkan jenis data, misalnya `order`, `payment`, atau `log`.
- **event_id** digunakan sebagai identitas unik dari setiap event.
Pada sistem ini, kombinasi topic dan event_id dipakai untuk mengecek apakah event sudah pernah diproses atau belum. Jika sudah ada, maka event dianggap duplicate dan tidak diproses ulang.

### T5 (Bab 5): Ordering Data
Dalam sistem log aggregator, urutan data tidak selalu harus sempurna. Yang lebih penting adalah data berhasil diterima dan diproses. Jika memaksakan semua event harus urut secara global, maka sistem bisa menjadi lebih lambat karena perlu sinkronisasi tambahan. Karena itu, project ini menggunakan pendekatan yang lebih sederhana, yaitu memproses event sesuai urutan queue pada satu instance. Untuk kebutuhan praktis, cara ini sudah cukup baik.

### T6 (Bab 6): Kegagalan Sistem dan Penanganannya
Gangguan dalam sistem terdistribusi bisa terjadi kapan saja, misalnya:
- aplikasi crash
- koneksi terputus
- event terkirim ulang
- data datang tidak berurutan
Pada project ini, duplicate event diatasi dengan mekanisme deduplication menggunakan SQLite. Data event yang sudah pernah diproses disimpan ke database, sehingga meskipun aplikasi restart, sistem tetap bisa mengenali event lama dan mencegah proses ulang.

### T7 (Bab 7): Eventual Consistency, Idempotency, dan Deduplication
Eventual consistency berarti data mungkin tidak langsung sama di semua bagian sistem, tetapi akan konsisten setelah beberapa waktu. Pada project ini, event diproses secara asynchronous menggunakan queue. Jadi event tidak selalu langsung diproses saat dikirim, tetapi akan masuk antrian terlebih dahulu. Agar sistem tetap aman dan konsisten, digunakan:
- **Idempotency** → event yang sama tidak mengubah hasil jika dikirim ulang.
- **Deduplication** → event duplicate akan dibuang.
Dengan cara ini, sistem tetap stabil walaupun bekerja secara asynchronous.

### T8 (Bab 1–7): Metrik Evaluasi Sistem
Beberapa hal yang bisa digunakan untuk menilai performa sistem ini:
1. **Throughput**  
   Jumlah event yang dapat diproses dalam waktu tertentu.
2. **Latency**  
   Waktu yang dibutuhkan sejak event dikirim sampai selesai diproses.
3. **Duplicate Rate**  
   Jumlah duplicate event yang berhasil dideteksi dan ditolak.
Semakin baik nilai ketiga metrik tersebut, maka semakin baik performa sistem.

#### 5. Kesimpulan
Project ini berhasil membuat sistem log aggregator sederhana menggunakan konsep publish-subscribe. Sistem dapat menerima event, memproses event secara asynchronous, serta mencegah duplicate menggunakan SQLite. Selain itu, sistem tetap bisa mengenali duplicate walaupun aplikasi di-restart. Hal ini menunjukkan bahwa konsep idempotency dan deduplication sudah berjalan dengan baik. Penggunaan Docker juga membantu proses deployment agar aplikasi lebih mudah dijalankan di berbagai perangkat.

#### 6. Referensi
Tanenbaum, A. S., & van Steen, M. (2023). *Distributed Systems* (4th ed.). Maarten van Steen.

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
