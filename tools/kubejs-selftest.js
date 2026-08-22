// ZapeG SELF-TEST — SADECE yerel test sunucusunda durur, canlıya ASLA gitmez.
// Kanıt iki katmanlı:
//  1) Brigadier dispatcher'ından KAYIT kanıtı: kök düğümde komut var mı,
//     çocuk literalleri bekleneni içeriyor mu.
//  2) Gerçek ÇALIŞTIRMA: oyuncu gerektirmeyen dallar console source ile koşulur.
// Tüm çıktı '[zapeg-selftest]' etiketiyle logs/kubejs/server.log'a düşer.

ServerEvents.loaded(event => {
  const server = event.server

  function childNames(node) {
    var names = []
    try {
      var it = node.getChildren().iterator()
      while (it.hasNext()) names.push(String(it.next().getName()))
    } catch (err) {
      names.push('<children unreadable: ' + err + '>')
    }
    return names
  }

  let root = null
  try {
    root = server.minecraftServer.getCommands().getDispatcher().getRoot()
  } catch (e1) {
    try {
      root = server.commands.dispatcher.root
      console.log('[zapeg-selftest] dispatcher via beans')
    } catch (e2) {
      console.log('[zapeg-selftest] DISPATCHER UNREACHABLE: ' + e1 + ' / ' + e2)
    }
  }

  const expected = {
    'zapeg-kitap': ['liste', 'ver', 'hepsi'],
    'zapeg-unvan': ['liste', 'ver', 'kaldir'],
    'zapeg-cark': ['oyna'],
    'zapeg-lore': ['story', 'servant', 'rehearse', 'trigger', 'cancel', 'discord', 'voice']
  }

  if (root) {
    for (const commandName in expected) {
      var node = null
      try {
        node = root.getChild(commandName)
      } catch (err) {
        console.log('[zapeg-selftest] REG ' + commandName + ' -> getChild threw: ' + err)
        continue
      }
      if (!node) {
        console.log('[zapeg-selftest] REG ' + commandName + ' -> MISSING (not registered)')
        continue
      }
      var kids = childNames(node)
      var want = expected[commandName]
      var missing = []
      for (let i = 0; i < want.length; i++) {
        if (kids.indexOf(want[i]) < 0) missing.push(want[i])
      }
      console.log('[zapeg-selftest] REG ' + commandName + ' -> OK children=[' + kids.join(',') + ']'
        + (missing.length ? ' MISSING=[' + missing.join(',') + ']' : ' (all expected present)'))
    }
  }

  const runs = [
    ['kitap-usage', 'zapeg-kitap'],
    ['kitap-liste', 'zapeg-kitap liste'],
    ['unvan-usage', 'zapeg-unvan'],
    ['unvan-liste', 'zapeg-unvan liste'],
    ['cark-rules', 'zapeg-cark'],
    ['lore-usage', 'zapeg-lore'],
    ['lore-story-status', 'zapeg-lore story status'],
    ['lore-servant-usage', 'zapeg-lore servant']
  ]
  for (let i = 0; i < runs.length; i++) {
    try {
      var result = server.runCommandSilent(runs[i][1])
      console.log('[zapeg-selftest] RUN ' + runs[i][0] + ' -> result=' + result)
    } catch (err) {
      console.log('[zapeg-selftest] RUN ' + runs[i][0] + ' -> THREW: ' + err)
    }
  }
  console.log('[zapeg-selftest] DONE')
})
