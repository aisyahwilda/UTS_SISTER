# UTS Aggregator Service
Project ini adalah layanan aggregator event sederhana yang dibuat menggunakan **FastAPI**, **asyncio queue**, dan **SQLite**.  
Fungsi utama sistem ini adalah menerima event dari publisher, memproses event melalui queue, lalu mencegah data yang sama diproses lebih dari satu kali.

## Fitur Utama
- Menerima event satuan maupun batch.
- Event masuk ke queue dan diproses oleh worker.
- Sistem dapat mendeteksi event duplicate.
- Data duplicate tidak akan diproses ulang.
- Riwayat duplicate disimpan di SQLite.
- Menyediakan endpoint untuk melihat data event dan statistik.

## Format Event
Contoh data event yang dikirim:

```json
{
  "topic": "order",
  "event_id": "100",
  "timestamp": "2026-04-22T10:00:00Z",
  "source": "mobile",
  "payload": {
    "user_id": 1
  }
}
````
## Menjalankan Project Secara Lokal
Install dependency terlebih dahulu:
pip install -r requirements.txt

Lalu jalankan server:
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080

Jika berhasil, aplikasi akan berjalan di:
http://localhost:8080

Dokumentasi Swagger:
http://localhost:8080/docs


## Menjalankan dengan Docker
Build image:
docker build -t uts-aggregator .

Jalankan container:
docker run -p 8080:8080 --name my-aggregator uts-aggregator

Jika ingin menjalankan kembali container yang sudah ada:
docker start my-aggregator

Jika ingin menghentikan container:
docker stop my-aggregator

## Menjalankan dengan Docker Compose (Opsional)
docker compose up --build

## Endpoint API
### POST /publish
Digunakan untuk mengirim event ke sistem.
Bisa menerima:
* satu event
* beberapa event sekaligus (batch)

### GET /events
Menampilkan semua event yang sudah berhasil diproses.

### GET /events?topic=order
Menampilkan event berdasarkan topic tertentu.

### GET /stats
Menampilkan statistik sistem, seperti:
* jumlah event diterima
* jumlah event unik yang diproses
* jumlah duplicate yang ditolak
* topic yang pernah diproses
* waktu server berjalan

## Menjalankan Test Duplicate

Untuk simulasi pengiriman banyak event dan duplicate:
python -m src.publisher_sim --base-url http://localhost:8080 --total 5000 --duplicate-ratio 0.2
Artinya sekitar 20% event yang dikirim adalah duplicate.

## Menjalankan Unit Test
pytest -q

## Asumsi Sistem

* Sistem berjalan pada satu instance / satu node.
* Deduplikasi hanya berlaku di aplikasi ini, bukan antar banyak server.
* Data duplicate disimpan di file SQLite (`dedup.db`).
* Urutan proses mengikuti queue pada instance yang sama.
* Fokus utama sistem adalah mencegah duplicate dan menjaga proses tetap stabil.

## Kesimpulan
Sistem ini berhasil menerapkan konsep pub-sub sederhana dengan queue internal, worker asynchronous, serta deduplication menggunakan SQLite.
