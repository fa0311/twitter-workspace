// usage: node compare.cjs <dirA> <dirB>  -> per png: size, differing pixel ratio, and a diff image in diff/
const fs = require('fs'), path = require('path'), sharp = require('sharp')
const [a, b] = process.argv.slice(2)
fs.mkdirSync(path.join(a, '..', 'diff'), {recursive: true})
;(async () => {
  for (const f of fs.readdirSync(a).filter((f) => f.endsWith('.png')).sort()) {
    if (!fs.existsSync(path.join(b, f))) { console.log(`${f}: missing in B`); continue }
    const [ia, ib] = await Promise.all([a, b].map((d) => sharp(path.join(d, f)).ensureAlpha().raw().toBuffer({resolveWithObject: true})))
    if (ia.info.width !== ib.info.width || ia.info.height !== ib.info.height) { console.log(`${f}: size ${ia.info.width}x${ia.info.height} vs ${ib.info.width}x${ib.info.height}`); continue }
    const n = ia.info.width * ia.info.height, out = Buffer.alloc(n * 4)
    let diff = 0
    for (let i = 0; i < n; i++) {
      const o = i * 4
      const d = Math.max(...[0, 1, 2, 3].map((c) => Math.abs(ia.data[o + c] - ib.data[o + c])))
      if (d > 8) diff++
      out[o] = d > 8 ? 255 : ia.data[o] >> 2; out[o + 1] = ia.data[o + 1] >> 2; out[o + 2] = ia.data[o + 2] >> 2; out[o + 3] = 255
    }
    await sharp(out, {raw: {width: ia.info.width, height: ia.info.height, channels: 4}}).png().toFile(path.join(a, '..', 'diff', f))
    console.log(`${f}: ${ia.info.width}x${ia.info.height} diff ${(100 * diff / n).toFixed(2)}%`)
  }
})()
