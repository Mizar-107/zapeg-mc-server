// ZapeG denge köprüleri — SERVER-SIDE ONLY. (BALANCE.md'deki kararların kodu)
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

ServerEvents.recipes(event => {
  // --- Gümüş birleştirme -----------------------------------------------------
  // Pakette gümüş zaten var (AllTheOres + Thermal, tag'lerle birleşik).
  // Ice and Fire kendi gümüşünü getiriyor; tag'li tarifler karışık çalışır ama
  // iki fiziksel külçe kafa karıştırır. 1:1 çift yönlü dönüşüm = sıfır sürtünme.
  // (Ayrıca post-boot: I&F config'te silver ORE üretimi kapatılacak — TUNING.md)
  event.shapeless('alltheores:silver_ingot', ['iceandfire:silver_ingot']).id('zapeg:silver_to_ato')
  event.shapeless('iceandfire:silver_ingot', ['alltheores:silver_ingot']).id('zapeg:silver_to_iaf')

  // --- Rezerve (gerekirse aç) --------------------------------------------------
  // Alex's Caves nükleer bombası — sosyal kural yetmezse tarifi kaldır:
  // event.remove({ output: 'alexscaves:nuclear_bomb' })
})
