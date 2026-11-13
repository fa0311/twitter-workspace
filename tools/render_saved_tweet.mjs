// Render the saved TweetResultByRestId response of a deleted post through twitter-snap's guest pipeline
import fs from 'node:fs'
import {getSnapAppRenderWithCache} from '/root/workspace/twitter-snap/dist/main.js'
import {TwitterOpenApi} from '/root/workspace/twitter-snap/node_modules/twitter-openapi-typescript/dist/src/index.js'
const [saved, out, scale = '2', width = '1440'] = process.argv.slice(2)
const body = fs.readFileSync(saved, 'utf8')
const realFetch = globalThis.fetch
// the client captured fetch at import time; the library path never installs twitter-snap's own fetchApi
TwitterOpenApi.fetchApi = async (input, init) => {
  const url = typeof input === 'string' ? input : input.url
  if (process.env.DEBUG_FETCH) console.error('fetch', url.slice(0, 90))
  if (url.includes('/TweetResultByRestId')) return new Response(body, {status: 200, headers: {'content-type': 'application/json'}})
  return realFetch(input, init)
}
const api = getSnapAppRenderWithCache({})
const t0 = Date.now()
const data = await api({
  url: 'https://x.com/daru_daru_d/status/2121160905715269756',
  limit: 1,
  sessionType: 'guest',
  callback: async (run) => {
    const output = await run({output: out, theme: 'RenderOceanBlueColor', scale: Number(scale), width: Number(width)})
    await output.file.tempCleanup()
    return out
  },
})
console.log('done', JSON.stringify(data), `${Date.now() - t0} ms`)
