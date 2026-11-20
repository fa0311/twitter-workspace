// Preload for a Node script that browses X with Playwright's launchPersistentContext (twitter-api-safe-dump):
// what the page puts on the wire is logged next to what the script itself records.
//
//     WIRE_TEE_OUT=<dir> node --import ../tools/wire_tee.mjs --conditions=development packages/dump/src/dump.ts ...
//
// <dir>/wire.ndjson gets one line per API request ({at, method, url, postData of GraphQL POSTs, page}) and per API
// response ({at, status, url, file}); <dir>/wire_responses/<Operation>.<n>.json gets every GraphQL 200 body.
// No header is written, so cookies and tokens stay in the browser. The bodies carry other people's posts.
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const out = process.env.WIRE_TEE_OUT;
mkdirSync(path.join(out, "wire_responses"), { recursive: true });
const log = (line) => appendFileSync(path.join(out, "wire.ndjson"), `${JSON.stringify({ at: new Date().toISOString(), ...line })}\n`);
const isApi = (url) => /\/i\/api\/|\/graphql\//.test(new URL(url).pathname);
const operation = (url) => /\/graphql\/[^/]+\/([^/?]+)/.exec(new URL(url).pathname)?.[1];
const counts = {};

const { chromium } = createRequire(path.resolve(process.argv[1]))("playwright");
const launch = chromium.launchPersistentContext.bind(chromium);
chromium.launchPersistentContext = async (...args) => {
	const context = await launch(...args);
	context.on("request", (request) => {
		if (!isApi(request.url())) {
			return;
		}
		const name = operation(request.url());
		log({
			method: request.method(),
			url: request.url(),
			postData: name === undefined ? undefined : (request.postData() ?? undefined),
			page: request.serviceWorker() ? undefined : request.frame().page()?.url(),
		});
	});
	context.on("response", async (response) => {
		if (!isApi(response.url())) {
			return;
		}
		const name = operation(response.url());
		const body = name !== undefined && response.status() === 200 ? await response.text().catch(() => undefined) : undefined;
		if (body === undefined) {
			log({ status: response.status(), url: response.url() });
			return;
		}
		counts[name] = (counts[name] ?? 0) + 1;
		const file = `wire_responses/${name}.${counts[name]}.json`;
		writeFileSync(path.join(out, file), body);
		log({ status: 200, url: response.url(), file });
	});
	return context;
};
