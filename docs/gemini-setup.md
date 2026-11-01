# Gemini ücretsiz bağlantı kurulumu

İnceleme tarihi: **30 Ekim 2026**. Bu proje yalnızca yerel ve eğitim amaçlı kullanım için hazırlanmıştır. Kurulum, faturalandırma açmaz ve ücretli katmana otomatik geçmez.

## Kullanılan model

Uygulama yalnızca `gemini-3.5-flash-lite` modelini kabul eder. Google'ın güncel model belgesi yeni projelerde 2.5 ailesi yerine güncel modelleri öneriyor; fiyatlandırma sayfası 3.5 Flash-Lite giriş/çıkış tokenlarını Free tier için ücretsiz gösteriyor. Model adı değişirse uygulama çağrıyı engeller; takma ad veya otomatik model değişimi yoktur.

Resmî kaynaklar: [model sayfası](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [model listesi](https://ai.google.dev/gemini-api/docs/models), [fiyatlandırma](https://ai.google.dev/gemini-api/docs/pricing), [kota sayfası](https://ai.google.dev/gemini-api/docs/rate-limits), [ek kullanım şartları](https://ai.google.dev/gemini-api/terms).

## Hesap kontrolü

1. Google AI Studio'da kullanacağın API anahtarının bağlı olduğu projeyi aç.
2. Projede etkin bir Cloud Billing hesabı bulunmadığını doğrula. Google şartlarına göre aktif faturalandırma hesabına bağlı proje üzerinden erişim Paid Service sayılır.
3. Hesabının ve bulunduğun bölgenin Gemini Developer API için uygun olduğunu kontrol et. Bölge veya hesap uygun değilse bağlantıyı açma.
4. Model listesinden `gemini-3.5-flash-lite` erişimini doğrula. 2.5 modeli için eski kullanıcı erişimine güvenme.
5. Anahtarı sohbet, ekran görüntüsü, frontend dosyası veya Git deposunda paylaşma.

Ücretsiz hizmette gönderdiğin girdiler ve model çıktıları Google ürünlerini geliştirmek için kullanılabilir; insan inceleyiciler bunları okuyabilir. Bağlantı testi yalnızca sabit bir mesaj gönderir. Gemini plan üretimi ise açıkça seçildiğinde seyahat isteğini, notları ve halka açık araç sonuçlarını gönderir. Kişisel, gizli veya hassas bilgi gönderme.

## Yerel ayar

`backend/.env.example` dosyasını `backend/.env` olarak kopyala ve yalnızca yerel dosyada şu değerleri düzenle:

```dotenv
FREE_ONLY_MODE=true
GEMINI_API_KEY=buraya_kendi_anahtarin
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FREE_TIER_CONFIRMED=true
ENABLE_GOOGLE_MAPS_GROUNDING=false
ENABLE_GOOGLE_SEARCH_GROUNDING=false
```

`GEMINI_FREE_TIER_CONFIRMED=true`, uygulamanın Google hesabına veya faturalandırma ayarına eriştiği anlamına gelmez. Yukarıdaki kontrolleri yaptığını belirten yerel bir kilittir. Anahtarı kaldırmak veya değeri `false` yapmak çağrıyı kapatır.

Backend'i yeniden başlat. Ana sayfadaki **Yapay zekâ bağlantısı** bölümünde önce **Durumu kontrol et**, ardından ayarlar uygunsa **Gemini bağlantısını dene** düğmesini kullan. Deneme başarılı olsa bile bu yalnızca modelin yanıt verdiğini gösterir; hesabın faturalandırma durumunu kanıtlamaz.

## Sınırlar ve hata davranışı

- En fazla 6 model çağrısı/dakika ve 10 çağrı/gün; sayaçlar süreç yeniden başlayınca sıfırlanır. Tek plan birden fazla turn kullanabilir.
- Aynı anda tek deneme; ikinci istek sırada bekletilmez.
- 25 saniye toplam süre ve 256 KiB yanıt sınırı.
- SDK otomatik tekrar denemesi kapalıdır. 429 yanıtı ve Retry-After bekleme süresi korunur.
- Model, ücretli servis katmanı, grounding aracı veya başka endpoint için otomatik geçiş yoktur.
- Bağlantı kontrolü için tek aday, normal bitiş, araç çağrısı içermeyen ve Pydantic şemasına uyan JSON gerekir.
- Plan üretiminde otomatik araç yürütme kapalıdır; en fazla 6 turn, 6 araç çağrısı ve 75 saniye vardır. Yalnızca `get_weather` ile `search_places` kabul edilir.
- Çıktıdaki tarihler ve mekân kimlikleri kaydedilmeden önce gerçek araç sonuçlarıyla çapraz doğrulanır.

Anahtar, hata yanıtlarına veya `/api/ai/status` çıktısına yazılmaz. Uygulama `.env` dosyalarını paketlemez ve Git yoksayma listesinde tutar.

## Google Maps ve Search araştırması

Seçilen modelin fiyat tablosunda Maps ve Search grounding Free tier için **Not available** olarak gösteriliyor. Ücretli tabloda aylık ücretsiz miktarın ardından ücretli kullanım bulunması bu projenin “faturalandırmasız ve otomatik ücret yok” kuralına uymuyor. Bu nedenle iki özellik de ayar bayrakları yanlışlıkla `true` olsa bile devre dışı kalır; uygulama OSM keşif yolunu kullanır.

Bu karar [Maps grounding](https://ai.google.dev/gemini-api/docs/maps-grounding), [Search grounding](https://ai.google.dev/gemini-api/docs/google-search) ve [fiyatlandırma](https://ai.google.dev/gemini-api/docs/pricing) sayfaları yeniden incelenmeden değiştirilmemelidir.
