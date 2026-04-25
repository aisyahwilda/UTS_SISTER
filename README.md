# UTS Aggregator Service

Layanan aggregator event berbasis **FastAPI + asyncio queue** dengan deduplikasi persisten lokal menggunakan **SQLite**.

## Fitur Utama

- `POST /publish` menerima single event atau batch event.
- Validasi skema event dengan Pydantic.
- Worker internal memproses event dari in-memory queue.
- Deduplikasi idempoten berdasarkan `(topic, event_id)`.
- `GET /events?topic=...` mengembalikan event unik yang sudah diproses.
- `GET /stats` mengembalikan `received`, `unique_processed`, `duplicate_dropped`, `topics`, `uptime`.

## Skema Event

```json
{
  "topic": "string",
  "event_id": "string-unik",
  "timestamp": "ISO8601",
  "source": "string",
  "payload": {}
}
```

## Menjalankan Lokal (tanpa Docker)

```powershell
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## Menjalankan dengan Docker (wajib)

```powershell
docker build -t uts-aggregator .
docker run -p 8080:8080 uts-aggregator
```

## Uji Simulasi Duplicate Delivery

Jalankan aggregator terlebih dahulu, lalu kirim event dalam jumlah besar dengan duplikasi:

```powershell
python -m src.publisher_sim --base-url http://localhost:8080 --total 5000 --duplicate-ratio 0.2
```

Parameter `--duplicate-ratio 0.2` berarti sekitar 20% dari total event akan dikirim sebagai duplikasi, sementara sisanya unik.

## Docker Compose (opsional bonus)

```powershell
docker compose up --build
```

Compose menyediakan dua service:

- `aggregator` (API)
- `publisher` (simulator duplicate delivery)

## Menjalankan Unit Test

```powershell
pytest -q
```

## Endpoint Ringkas

- `POST /publish`
- `GET /events?topic=orders`
- `GET /events`
- `GET /stats`

## Asumsi Penting

- Deduplikasi bersifat lokal-node (tidak distributed).
- Persistensi dedup disimpan di SQLite file lokal (`dedup.db`).
- Ordering total lintas topik **tidak diwajibkan**; sistem menjaga proses queue FIFO pada instance yang sama, tetapi fokus utama adalah idempotency dan throughput.
