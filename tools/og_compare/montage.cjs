const fs = require('fs'), path = require('path'), sharp = require('sharp')
;(async () => {
  for (const f of fs.readdirSync('baseline').filter((f) => f.endsWith('.png') && f.includes(process.argv[2] || ''))) {
    const imgs = ['baseline', process.argv[3] || 'branch'].map((d) => path.join(d, f)).filter(fs.existsSync)
    const metas = await Promise.all(imgs.map((p) => sharp(p).metadata()))
    const h = Math.max(...metas.map((m) => m.height)), w = metas.reduce((a, m) => a + m.width + 10, 0)
    let x = 0
    const composite = imgs.map((p, i) => { const c = {input: p, left: x, top: 0}; x += metas[i].width + 10; return c })
    await sharp({create: {width: w, height: h, channels: 4, background: '#ff00ff'}}).composite(composite).png().toFile(path.join(process.argv[4] || 'montage', f))
  }
})()
