# Checklist bukti Bagian III (wajib diambil setelah aplikasi dijalankan)

**Status saat paket disusun:** belum ada screenshot hasil Docker/Kubernetes nyata. Gambar desain bukan bukti uji.

| No. | Bukti yang diminta | Cara memperoleh | Status |
|---|---|---|---|
| 1 | Semua container berjalan | `docker compose ps` | BELUM DIUJI |
| 2 | Login SSO dan JWT yang diterima | Keycloak web/`scripts/smoke_test.sh` (sembunyikan token) | BELUM DIUJI |
| 3 | Validasi token gagal untuk tanpa JWT | `curl -i -X POST http://localhost:8000/predict ...` | BELUM DIUJI |
| 4 | Prediksi dan penulisan ke Primary | `POST /predict`, header `X-Write-Node` | BELUM DIUJI |
| 5 | Riwayat dibaca dari Replica | `GET /inferences`, header `X-Read-Node` | BELUM DIUJI |
| 6 | Primary/Replica punya peran berbeda | `scripts/probe_replication.sh` | BELUM DIUJI |
| 7 | StatefulSet, ConfigMap, Secret, PVC | `kubectl -n sbdt-uts get pods,svc,pvc,cm,secrets` | BELUM DIUJI |
| 8 | Data tetap setelah Pod database dihapus | Bandingkan `SELECT count(*)` sebelum/sesudah delete | BELUM DIUJI |
| 9 | Headless service & hostname tetap | `kubectl -n sbdt-uts get svc` & `kubectl exec ...` | BELUM DIUJI |
| 10 | Ingress auth.lokal & api.lokal | Pengujian HTTP `Host:` melalui ingress controller | BELUM DIUJI |

**Hal yang tidak boleh diklaim tanpa pengujian:** failover otomatis, zero downtime, latensi replikasi tertentu, ketersediaan public URL GitHub, keberhasilan uji yang belum dilakukan.

Simpan screenshot terpilih dalam `docs/bukti/` dan tempelkan ke PDF laporan teknis. Gunakan perintah yang tercantum di README. Sertakan URL repositori Git aktual ketika sudah di-push.
