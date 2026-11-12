# Panduan menjalankan proyek UTS SBDT di MacBook Neo

Marcel Immanuel — NIM 20240801117. Buka folder ini hasil ekstraksi ZIP di Finder.

**Status:** Kode dan konfigurasi tersedia; pengujian runtime harus dilakukan oleh mahasiswa di Mac/PC dengan Docker. Screenshot dan repositori Git **belum** dibuat.

## 1. Apa sebenarnya aplikasinya?

Demo REST API: akun Keycloak login -> JWT -> FastAPI -> model risiko transaksi **sintetis** -> PostgreSQL Primary (INSERT) -> Read-Replica (SELECT). Tidak memerlukan desain website UI.

## 2. Instal aplikasi awal

1. Download Docker Desktop versi **Mac with Apple silicon**: https://docs.docker.com/desktop/setup/install/mac-install/
2. Buka file .dmg, geser Docker ke Applications, jalankan Docker sampai siap.
3. Gunakan Terminal macOS (Command + Space, ketik Terminal).
4. Opsional: gunakan VS Code hanya untuk membaca file; tidak wajib.

MacBook Neo 8 GB RAM dapat terbebani saat Docker + Kubernetes berjalan bersama. Jalankan satu lingkungan pada satu waktu.

## 3. Jalankan Docker Compose

Jika folder proyek disimpan di Downloads setelah diekstrak:

```bash
cd ~/Downloads/SBDT_Proyek_Bagian_III_Marcel_Immanuel
docker --version
docker compose version
docker compose up -d --build
docker compose ps
```

Jika folder tidak ditemukan, ketik `cd ` (dengan spasi) di Terminal, drag folder dari Finder, Enter.

Setelah aplikasi berjalan, buka:
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health
- Keycloak: http://localhost:8080/

Jalankan uji:
```bash
bash scripts/smoke_test.sh
bash scripts/probe_replication.sh
```

**Yang harus terlihat:** `POST /predict` menghasilkan HTTP 201, `/inferences` memuat riwayat, primary `pg_is_in_recovery()` = f, replica = t, dan stat streaming pada Primary. Jika belum muncul, cek `docker compose ps` dan `docker compose logs --tail=80`. Simpan screenshot terminal dan respons; samarkan JWT/password.

Pengujian request tanpa token (harus HTTP 401):
```bash
curl -i -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"transaction_amount":500000,"transactions_24h":1,"new_device":false}'
```

## 4. Menyiapkan Kubernetes (lanjutan, setelah Docker berhasil)

Simpan screenshot dahulu, lalu hentikan Compose supaya MacBook Neo tidak terbebani:
```bash
docker compose down
```
JANGAN memakai `docker compose down -v`, karena `-v` menghapus volume data demo Compose.

Pasang `kind` dan `kubectl`. Jika menggunakan Homebrew:
```bash
brew install kind kubectl
```
Jika `brew` belum tersedia, lihat panduan Homebrew resmi di https://brew.sh/; untuk alternatif Kubernetes yang sudah disertakan Docker Desktop lihat https://docs.docker.com/desktop/use-desktop/kubernetes/ .

Dari folder proyek:
```bash
docker build -t sbdt-api:local .
kind create cluster --name sbdt-uts
kind load docker-image sbdt-api:local --name sbdt-uts
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/
kubectl -n sbdt-uts get pods,svc,pvc,ingress
kubectl -n sbdt-uts get pvc
```

Pod harus berstatus Running/Ready, PVC Bound. Jika Pod Pending gunakan `kubectl -n sbdt-uts describe pod NAMA_POD` dan cek storageclass.

Buka **2 Terminal** (masing-masing perintah akan tetap aktif):

Terminal A:
```bash
kubectl -n sbdt-uts port-forward svc/keycloak 8080:8080
```
Terminal B:
```bash
kubectl -n sbdt-uts port-forward svc/api 8000:8000
```

Di Terminal C, jalankan `bash scripts/smoke_test.sh` dari folder proyek dan simpan screenshot. Jangan memakai `scripts/probe_replication.sh` untuk cluster kind, karena skrip tersebut memeriksa Docker Compose, bukan Pod Kubernetes.

## 5. Tes apakah data tidak hilang saat Pod dihapus (nilai 25%)

Pastikan POST /predict telah berhasil menyimpan minimal satu record di cluster. Lalu:
```bash
kubectl -n sbdt-uts exec postgres-primary-0 -- psql -U sbdt -d sbdt -c 'SELECT count(*) FROM inference_history;'
kubectl -n sbdt-uts get pvc
kubectl -n sbdt-uts delete pod postgres-primary-0
kubectl -n sbdt-uts rollout status statefulset/postgres-primary
kubectl -n sbdt-uts exec postgres-primary-0 -- psql -U sbdt -d sbdt -c 'SELECT count(*) FROM inference_history;'
kubectl -n sbdt-uts get pvc
```

Ambil screenshot hasil sebelum dan sesudah. Nilai `count` tetap sama (pastikan tidak ada request baru di antaranya), PVC masih Bound. Ini membuktikan **persistence**, bukan automatic failover.

Cek replica di Kubernetes:
```bash
kubectl -n sbdt-uts exec postgres-primary-0 -- psql -U sbdt -d sbdt -c 'SELECT application_name,state,sync_state FROM pg_stat_replication;'
kubectl -n sbdt-uts exec postgres-replica-0 -- psql -U sbdt -d sbdt -c 'SELECT pg_is_in_recovery();'
```

## 6. Ingress — ada pekerjaan tambahan!

File `k8s/08-ingress.yaml` baru berisi definisi host `auth.lokal` dan `api.lokal` dengan class `nginx`. Belum ada controller yang dipasang. Untuk mendapat bukti lengkap rubrik, harus memasang **controller Ingress yang masih didukung**, menyesuaikan class jika perlu, mengatur hostname lokal, dan menguji benar-benar terhubung. Jangan mengaku Ingress sudah lulus hanya karena objeknya muncul di `kubectl get ingress`.

Controller komunitas `ingress-nginx` lama telah pensiun Maret 2026. Untuk alternatif aktif lihat https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/ dan https://kind.sigs.k8s.io/docs/user/ingress/ . Jika tidak yakin, fokuskan Docker + PVC + SSO dulu dan catat Ingress sebagai **belum diuji**.

## 7. Bukti screenshot sesuai rubrik

Ambil screenshot asli, masukkan ke `docs/bukti/` dan ke laporan teknis Word; ekspor ulang ke PDF:
1. `docker compose ps`
2. API health dan POST /predict yang berhasil
3. GET /inferences dari Replica
4. Uji tanpa token gagal 401
5. `pg_stat_replication` state streaming
6. Pod dan PVC pada Kubernetes (Bound)
7. SELECT count(*) sebelum dan setelah hapus Pod
8. Ingress akses hostname jika sudah dibuat
9. Screenshot repo GitHub (URL asli)

**Keamanan:** sembunyikan JWT, kata sandi, dan kredensial pribadi. Akun/password yang ada di repositori ini khusus demo dan tidak boleh digunakan untuk produksi.

## 8. GitHub

Buat **repo kosong dulu** melalui github.com (Create repository, misalnya `uts-sbdt-marcel`). Baru kemudian jalankan:
```bash
git init
git add .
git commit -m "UTS SBDT Bagian III"
git branch -M main
git remote add origin https://github.com/USERNAME/uts-sbdt-marcel.git
git push -u origin main
```

Ganti USERNAME dan alamat repo sesuai repo yang benar-benar dibuat. Jika sebelumnya remote origin sudah ada gunakan `git remote set-url origin URL_REPO_BENAR`. Jika remote `Repository not found`, pastikan repo sudah dibuat dan akun GitHub yang digunakan memiliki akses.

## 9. Pengumpulan

Dosen meminta **repositori Git yang bisa dibuka** serta **laporan teknis PDF berisi screenshot nyata**. Paket ZIP dan PDF tanpa screenshot tidak otomatis memenuhi penilaian penuh. Dalam revisi ini PDF pada folder `docs/` telah diselaraskan dengan kelima unsur rubrik, tetapi hasil aktual tetap harus dilengkapi setelah pengujian.
