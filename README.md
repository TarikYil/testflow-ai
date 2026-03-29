# TestFlow AI

Form tanımlarından otomatik olarak **Playwright** ve **Selenium** test kodu üreten, yapay zeka destekli bir web uygulamasıdır. Kullanıcı bir HTML formu, JSON alan tanımı veya manuel alan listesi girer; sistem bu girdiyi analiz eder, Groq API üzerinden gerçek zamanlı test kodu üretir ve üretilen kodu doğrulayarak kullanıcıya sunar.

---

## Neden Bu Teknolojiler?

| Katman | Teknoloji | Tercih Sebebi |
|--------|-----------|----------------|
| Backend | **FastAPI** (Python 3.11) | Async yapısı sayesinde streaming işlemleri native destekler; Pydantic ile istek/yanıt doğrulama otomatiktir; OpenAPI dökümantasyonu ek efor gerektirmez |
| Yapay Zeka | **Groq API** (`llama-3.3-70b-versatile`) | Token üretim hızı diğer sağlayıcıların çok üstünde, streaming desteği var, ücretsiz kullanım katmanı yeterli |
| Frontend | **React 18** + **Vite** + **TypeScript** | Vite ile anlık HMR, TypeScript ile derleme zamanı hata yakalama, React ile bileşen bazlı mimari |
| Stil | **TailwindCSS** | Utility-first yaklaşım, ayrı CSS dosyalarına gerek kalmadan hızlı ve tutarlı UI geliştirme |
| Veritabanı | **MongoDB** | Üretim kayıtlarının yapısı esnek (farklı modlar, farklı alanlar); Motor async driver ile FastAPI'ye doğal uyum |
| Konteyner | **Docker Compose** | Backend, frontend ve MongoDB tek komutla ayağa kalkar; ortam farklılıkları ortadan kalkar |
| Proxy | **Nginx** | Frontend container içinde SPA serving + `/api` isteklerini backend'e yönlendirme |

---

## Proje Yapısı

```
testflow-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoint tanımları
│   │   ├── core/            # Konfigürasyon, veritabanı bağlantısı, prompt şablonları
│   │   ├── schemas/         # İstek ve yanıt modelleri (Pydantic)
│   │   └── services/        # İş mantığı katmanı
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # UI bileşenleri
│   │   ├── hooks/           # SSE stream yönetimi
│   │   ├── services/        # Backend API istemcisi
│   │   ├── utils/           # ZIP dışa aktarma
│   │   └── types/           # TypeScript tip tanımları
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

---

## Özellikler

### 1. Üç Farklı Girdi Modu

- **HTML**: Kullanıcı `<form>` içeren ham HTML yapıştırır. Backend tarafında BeautifulSoup4 ile `<input>`, `<select>`, `<textarea>` etiketleri otomatik çıkarılır ve normalize edilir.
- **JSON**: `[{"name": "email", "type": "email", "label": "Email", "required": true}]` formatında alan tanımı girilir. Pydantic ile doğrudan doğrulanır.
- **Manuel**: JSON formatında serbest alan tanımlama. JSON ile aynı pipeline'ı kullanır.

Bu üç mod sayesinde kullanıcı mevcut bir HTML formunu kopyalayabilir veya sıfırdan alan tanımı yazabilir.

### 2. Gerçek Zamanlı Kod Üretimi (SSE)

Kod üretimi **Server-Sent Events** ile gerçek zamanlı yapılır. Kullanıcı butona tıkladığında:

1. Frontend, `/api/v1/generate-test` endpoint'ine POST isteği atar
2. Backend, Groq API'ye streaming isteği gönderir
3. API'den gelen her token parçası (`chunk`) anında SSE ile frontend'e iletilir
4. Frontend, gelen her chunk'ı syntax highlighting ile ekranda gösterir
5. Stream tamamlandığında backend kodu doğrular ve `done` event'i gönderir

**Neden SSE?** WebSocket'e kıyasla tek yönlü veri akışı yeterli olduğu için daha basittir. HTTP üzerinden çalıştığı için proxy ve firewall uyumluluğu yüksektir. Bağlantı koptuğunda tarayıcı otomatik yeniden bağlanır.

**İptal mekanizması**: Kullanıcı "İptal Et" butonuna bastığında frontend tarafında `AbortController` ile stream kesilir ve UI buna göre güncellenir.

### 3. Çıktı Doğrulama (3 Aşama)

Yapay zeka modelinin ürettiği kod her zaman doğru olmayabilir. Bu nedenle üretilen her çıktı şu üç aşamadan geçirilir:

1. **Syntax Kontrolü**: Python için `ast.parse()` ile AST oluşturulur; geçersiz syntax varsa yakalanır. JavaScript için temel yapısal kontrol yapılır.
2. **Import Kontrolü**: Seçilen framework'e ait `import` veya `require` ifadesinin bulunup bulunmadığı kontrol edilir (ör. `from playwright.sync_api import`).
3. **Test Yapısı Kontrolü**: Python'da `def test_` ile başlayan fonksiyon, JavaScript'te `test(`, `describe(`, `it(` pattern'lerinin varlığı doğrulanır.

Herhangi bir aşama başarısız olursa hata detayı bir sonraki denemeye eklenir ve model kendini düzeltmesi için yeniden çağrılır.

### 4. Retry ve Fallback Stratejisi

Her model için yapılandırılabilir sayıda deneme yapılır (varsayılan: 3). Birincil model (`llama-3.3-70b-versatile`) tüm denemelerinde başarısız olursa yedek modele (`llama3-8b-8192`) geçilir. Yedek model de başarısız olursa kullanıcıya anlamlı bir hata mesajı gösterilir.

- **Geçici hatalar** (429 rate limit, 503 service unavailable, timeout): Otomatik olarak tekrar denenir
- **Kalıcı hatalar** (401 unauthorized, 403 forbidden): Tekrar denemeden anında hata döndürülür

Bu yaklaşım sayesinde geçici API sorunları kullanıcıyı etkilemez; kalıcı sorunlarda ise gereksiz bekleme yaşanmaz.

### 5. Prompt Tasarımı

Modelin tutarlı ve çalıştırılabilir kod üretmesi için üç katmanlı bir prompt yapısı kullanılır:

- **System Prompt**: Framework ve dile özel kurallar tanımlar (yalnızca kod üret, markdown bloğu kullanma, gerekli import'ları ekle, her alan için assertion yaz)
- **Few-Shot Örnek**: Her framework/dil kombinasyonu için doğru bir referans çıktı sağlanır. Model bu örneği format rehberi olarak kullanır.
- **User Prompt**: Parse edilmiş form alanları JSON formatında verilir. Retry durumunda önceki denemede alınan hata bilgisi de eklenir, böylece model aynı hatayı tekrarlamaması için yönlendirilir.

### 6. Hata Yönetimi

**Backend tarafında** hatalar katmanlı şekilde ele alınır:

| Durum | Ne Olur |
|-------|---------|
| Geçersiz istek formatı | HTTP 422 + detaylı hata açıklaması |
| Form alanı bulunamadı | SSE üzerinden `no_fields` hatası |
| API kimlik doğrulama hatası | Anında hata dönüşü, retry yapılmaz |
| Rate limit veya geçici API hatası | Otomatik retry + model fallback |
| Doğrulama başarısız | Hata context'i ile yeniden deneme |
| Tüm denemeler başarısız | Hata mesajı + üretilebilmiş ham kod |

**Frontend tarafında** backend'den gelen teknik hata kodları kullanıcı dostu Türkçe mesajlara çevrilir:

| Hata Kodu | Kullanıcıya Gösterilen |
|-----------|------------------------|
| `401` | "API anahtarı geçersiz veya süresi dolmuş" |
| `429` | "İstek limiti aşıldı, birkaç dakika bekleyin" |
| `all_models_failed` | "Tüm modeller başarısız oldu" |
| `no_fields` | "Girdiğiniz içerikte form alanı bulunamadı" |
| Network hatası | "Sunucuya bağlanılamıyor" |
| HTTP 422 | Pydantic doğrulama detayları ayrıştırılıp gösterilir |

### 7. Geçmiş Sistemi

Her başarılı veya hatalı üretim MongoDB'ye otomatik kaydedilir. Kaydedilen bilgiler: girdi modu, ham girdi içeriği, parse edilmiş alanlar, framework, dil, üretilen kod, durum, hata nedeni, retry sayısı, kullanılan model ve tarih bilgileri.

**Upsert mantığı**: Aynı girdi + framework + dil kombinasyonunda tekrar üretim yapıldığında yeni kayıt oluşmaz; mevcut kayıt güncellenir. Bu eşleştirme `mode + input_content + framework + language` üzerinden hesaplanan SHA-256 hash ile yapılır. Veritabanında bu hash'e unique index tanımlıdır.

Kullanıcı geçmiş listesinden bir kayıt seçtiğinde hem üretilen kod hem de girdi içeriği ekrana yüklenir.

### 8. ZIP Dışa Aktarma

"İndir" butonu ile girdi, çıktı ve metadata tek bir ZIP dosyası olarak indirilir:

- `input.html` veya `input.json` — Kullanıcının girdiği içerik
- `test_generated.py` veya `test_generated.js` — Üretilen test kodu
- `meta.json` — Framework, dil, mod, tarih bilgileri

ZIP dosyası tamamen tarayıcı tarafında oluşturulur (JSZip + file-saver), backend'e ek istek gitmez.

---

## Halüsinasyon Önleme ve Çıktı Güvenilirliği

Yapay zeka modelleri gerçek olmayan, hatalı veya anlamsız çıktı üretebilir (halüsinasyon). Bu projede her katman bu sorunu farklı bir açıdan ele alır:

| Yöntem | Ne Yapıyor | Nerede |
|--------|-----------|--------|
| **Kısıtlayıcı System Prompt** | Modele "sadece kod yaz, açıklama ekleme, markdown bloğu kullanma, her alan için assertion ekle" gibi katı kurallar verilir. Modelin çıktı formatını serbest bırakması engellenir. | `core/prompts.py` |
| **Few-Shot Örnek** | Her framework/dil kombinasyonu için doğru formatta bir referans kod verilir. Model bu örneği şablon olarak kullanır, kendi formatını icat etmez. | `core/prompts.py` |
| **Düşük Temperature (0.1)** | Üretimi olabildiğince deterministik tutar. Yaratıcılık gerektiren bir görev olmadığı için model tutarlı ve tekrarlanabilir çıktı verir. | `core/config.py` |
| **3 Aşamalı Doğrulama** | Üretilen kod syntax, import ve test yapısı kontrolünden geçirilir. Geçemeyen çıktı doğrudan kullanıcıya gönderilmez. | `services/validator_service.py` |
| **Hata Bağlamıyla Yeniden Deneme** | Doğrulamadan geçemeyen çıktının hata detayı bir sonraki prompt'a eklenir. Model "bu hatayı yapma" uyarısıyla tekrar çağrılır; kendini düzeltme şansı verilir. | `services/llm_service.py` |
| **Model Fallback** | Birincil model tutarlı çıktı üretemezse farklı bir modele geçilir. Tek modele bağımlılık ortadan kalkar. | `services/llm_service.py` |
| **Girdi Normalizasyonu** | Kullanıcının girdiği ham HTML veya JSON, modele gönderilmeden önce parse edilip standart bir yapıya dönüştürülür. Model ham ve düzensiz girdiyle uğraşmaz. | `services/parser_service.py` |

---

## İstek ve Trafik Yönetimi

| Mekanizma | Açıklama | Konum |
|-----------|----------|-------|
| **Nginx Reverse Proxy** | Frontend container'ında Nginx, `/api/` prefix'li istekleri backend'e yönlendirir. `proxy_buffering off` ile SSE chunk'ları tamponlanmadan anında iletilir. | `frontend/nginx.conf` |
| **CORS Middleware** | Backend yalnızca `.env`'de tanımlanan origin'lerden gelen istekleri kabul eder. Yetkisiz domain'lerden gelen istekler reddedilir. | `backend/app/main.py` |
| **AbortController** | Kullanıcı "İptal Et" butonuna bastığında frontend tarafında HTTP bağlantısı kesilir. Backend gereksiz yere işlem yapmaya devam etmez. | `frontend/hooks/useSSEStream.ts` |
| **Request Timeout (30sn)** | Backend'den Groq API'ye yapılan her HTTP çağrısı 30 saniye ile sınırlıdır. Yanıt gelmezse bağlantı kapatılır ve retry mekanizması devreye girer. | `backend/app/core/config.py` |
| **Stream Timeout (60sn)** | Streaming sırasında toplam süre 60 saniyeyi geçerse bağlantı sonlandırılır. Sonsuz bekleme engellenir. | `backend/app/core/config.py` |
| **Pydantic Validation** | Tüm gelen istekler Pydantic şemaları ile doğrulanır. Geçersiz formattaki istekler backend'e ulaşmadan 422 hatasıyla reddedilir. | `backend/app/schemas/` |
| **Docker Healthcheck** | `docker-compose.yml`'de MongoDB ve backend için healthcheck tanımlıdır. Bağımlı servisler ancak sağlıklı olduktan sonra başlatılır. | `docker-compose.yml` |

---

## API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `GET` | `/api/v1/health` | Servis durumu ve Groq API erişilebilirlik kontrolü |
| `GET` | `/api/v1/frameworks` | Desteklenen framework ve dil listesi |
| `POST` | `/api/v1/validate-form` | Form girdisini parse edip normalize edilmiş alan listesi döner |
| `POST` | `/api/v1/generate-test` | SSE stream ile gerçek zamanlı test kodu üretir |
| `GET` | `/api/v1/history` | Geçmiş üretim kayıtları (sayfalanmış) |
| `GET` | `/api/v1/history/{id}` | Tek bir geçmiş kaydının detayı |
| `DELETE` | `/api/v1/history/{id}` | Geçmiş kaydını siler |

---

## Kurulum

### Docker ile (Önerilen)

Önce `backend/.env` dosyasını oluştur:

```
GROQ_API_KEY=gsk_YOUR_API_KEY_HERE
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama3-8b-8192
MAX_RETRIES=2
REQUEST_TIMEOUT=30
STREAM_TIMEOUT=60
MONGO_URL=mongodb://localhost:27017/testflow
MONGO_DB=testflow
ALLOWED_ORIGINS=http://localhost:3000
```

Ardından tüm servisleri başlat:

```bash
docker-compose up --build -d
```

| Servis | Adres |
|--------|-------|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| MongoDB | localhost:27017 |

### Lokal Geliştirme

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| `GROQ_API_KEY` | — | Groq API anahtarı (zorunlu) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Birincil model |
| `GROQ_FALLBACK_MODEL` | `llama3-8b-8192` | Yedek model |
| `TEMPERATURE` | `0.1` | Düşük değer = daha tutarlı çıktı |
| `MAX_TOKENS` | `2048` | Maksimum üretim uzunluğu |
| `MAX_RETRIES` | `2` | Model başına tekrar deneme sayısı |
| `REQUEST_TIMEOUT` | `30` | HTTP istek zaman aşımı (sn) |
| `STREAM_TIMEOUT` | `60` | Stream zaman aşımı (sn) |
| `MONGO_URL` | `mongodb://localhost:27017/testflow` | MongoDB bağlantı adresi |
| `MONGO_DB` | `testflow` | Veritabanı adı |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS izinli origin'ler (virgülle ayrılmış) |
#   t e s t f l o w - a i  
 