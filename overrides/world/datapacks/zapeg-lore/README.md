# zapeg-lore datapack (server-side, world/datapacks)

Yüklenme: sunucu restart (veya OP `/reload` — KubeJS scriptlerini de yeniler, restart tercih).
Sekme herkese girişte açılır (root=tick). AUTO olanlar kendiliğinden düşer.

TÖREN başarımları (Ödüller gecesi, OP):
  /advancement grant kralxlarge only zapeg:kral_unvani
  /advancement grant eminomi12 only zapeg:vali
  /advancement grant MertOnal only zapeg:garaj_krali
  /advancement grant Thekingim only zapeg:gokyuzu_bekcisi
  /advancement grant SalihKarahan only zapeg:itfaiye_sefi
  /advancement grant <hedef> only zapeg:dokuzuncu   # Heraldor gecesi için. Açıklama yok.

Tören advancement'ı düşünce kubejs/zapeg_unvan.js OTOMATİK devreye girer:
renkli tab öneki ([Kral] vb.) + sunucu geneli title + ses. dokuzuncu bilerek
önek TAKMAZ (gizli kalır). Düzeltme/geri alma: /zapeg-unvan (OP).

HARABE (ilk lore yapısı, OP yerleştirir):
  /place template zapeg:harabe_1        # 9x5x9, güney kapılı; düz bir yere bak
  /zapeg-kitap ver <kendi-nick> kayip_sayfa
  → kitabı elinde tut, ortadaki kürsüye sağ tık. 8 beyaz + 1 siyah mum
    söndürülmüş durur; kimseye açıklama yapılmaz.
  Kaynak üreteç: tools/gen-harabe-structure.py (deterministik; elle düzenleme).

LORE KİTAPLARI (kubejs/zapeg_lore_kitap.js, OP):
  /zapeg-kitap liste
  /zapeg-kitap ver <oyuncu> kurulus|kanunlar|tutanaklar|kayip_sayfa
  /zapeg-kitap hepsi <oyuncu>
  kurulus + kanunlar + tutanaklar köy kütüphanesine/lectern'e; kayip_sayfa harabeye.
  tutanaklar: nick beklemeyen oyuncu lore'u (Enes Ö., Yusuf S. dahil, herkes görür).

Not: ilk_temas üç ejderha türünü açık id ile dinler (tag varsayımı yok).
