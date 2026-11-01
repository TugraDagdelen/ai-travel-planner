export const itineraryCopy = {
  tr: {
    eyebrow: 'AŞAMA 5 · GÜNLÜK ROTA', title: 'Planını oluştur', intro: 'Seçtiğin şehir için hava ve mekân verileri araçlarla alınır, sonuç doğrulanır ve yerel SQLite veritabanına kaydedilir.',
    mode: 'Üretim yöntemi', ai: 'Gemini araç çağırma', deterministic: 'Kurallı planlayıcı', demo: 'Sentetik demo planı',
    aiHint: 'Gemini anahtarı ve ücretsiz katman onayı gerekir. Model yalnızca araçların döndürdüğü yerleri kullanabilir.', deterministicHint: 'Yapay zekâ çağrısı yapmaz; canlı veri üzerinde belgelenmiş puanlama kurallarını kullanır.', demoHint: 'Ağ bağlantısı kurmaz; sentetik verileri açıkça demo olarak etiketler.',
    generate: 'Planı oluştur ve kaydet', generating: 'Plan oluşturuluyor…', choose: 'Önce yukarıdan doğru şehri seç.',
    failed: 'Plan oluşturulamadı.', missingKey: 'Gemini bağlantısı hazır değil. Kurallı planlayıcıyı seçebilir veya Gemini ayarlarını tamamlayabilirsin.', insufficient: 'Seçilen günlerin her biri için yeterli doğrulanmış mekân bulunamadı. Daha kısa tarih aralığı veya daha fazla ilgi alanı dene.',
    day: 'Gün', morning: 'Sabah', afternoon: 'Öğleden sonra', evening: 'Akşam', alternative: 'Yağış alternatifi', evidence: 'İşlem kaydı', saved: 'Yerel veritabanına kaydedildi',
    revise: 'Planı doğal dille düzenle', revisePlaceholder: 'Örn. İlk iki durağın sırasını değiştir', revising: 'Kayıtlı verilerle düzenleniyor…', reviseButton: 'Planı düzenle',
    synthetic: 'Sentetik demo', version: 'Sürüm', privacy: 'Notların ve revizyon isteklerin Gemini modunda modele gönderilir. Hassas bilgi yazma.',
  },
  en: {
    eyebrow: 'PHASE 5 · DAILY ROUTE', title: 'Build your itinerary', intro: 'Tools fetch weather and place evidence for your selected city, then the result is validated and saved to local SQLite.',
    mode: 'Generation method', ai: 'Gemini tool calling', deterministic: 'Rule-based planner', demo: 'Synthetic demo plan',
    aiHint: 'Requires a Gemini key and free-tier confirmation. The model may use only places returned by tools.', deterministicHint: 'Makes no AI call and applies documented scoring rules to live data.', demoHint: 'Makes no network call and labels all synthetic data as demo.',
    generate: 'Build and save itinerary', generating: 'Building itinerary…', choose: 'Choose the correct city above first.',
    failed: 'The itinerary could not be created.', missingKey: 'Gemini is not ready. Choose the rule-based planner or finish Gemini setup.', insufficient: 'There are not enough verified places for every selected day. Try a shorter date range or more interests.',
    day: 'Day', morning: 'Morning', afternoon: 'Afternoon', evening: 'Evening', alternative: 'Rain alternative', evidence: 'Activity log', saved: 'Saved to the local database',
    revise: 'Revise in natural language', revisePlaceholder: 'Example: swap the first two stops', revising: 'Revising from saved evidence…', reviseButton: 'Revise itinerary',
    synthetic: 'Synthetic demo', version: 'Version', privacy: 'Your notes and revision requests are sent to the model in Gemini mode. Do not enter sensitive information.',
  },
} as const
