# determine blog Agent API

The Cloudflare Worker proxies bounded chat requests to the Shanghai Jiao Tong University model API. The API key stays in the Worker secret `SJTU_API_KEY`; it is never sent to the browser or stored in this repository. The Worker accepts requests only from `https://determine123.github.io`, sends the visitor's question and matching public blog titles/URLs, and does not persist conversation data.

## Models

The default is `deepseek-chat`. The server accepts only these approved model names:

- `deepseek-chat` (DeepSeek V4 Flash)
- `deepseek-reasoner` (DeepSeek V4 Flash reasoning)
- `minimax` or `minimax-m2.7`
- `qwen` or `qwen3.6-27b`

The page selects the model through `_data/blog_agent.yml`. The Worker validates it against the allowlist before forwarding the request.

## Network and account limits

SJTU's notice says this API must be used from the campus network. A Cloudflare Worker may make upstream requests from outside that network and therefore may not be able to reach the service. Deploy and test the Worker from the intended environment first. If campus access is enforced by source network, host this small proxy on an SJTU-reachable server instead, while keeping the same server-side secret and API contract. Do not expose the key in browser code, GitHub Actions artifacts, or GitHub Pages.

The account limit is 10 requests/minute. This Worker applies a best-effort limit of 8 requests/minute per IP per isolate to leave room for other usage. Cloudflare can run multiple isolates, so this is not a global quota guarantee; enable an edge-wide rate limit or a shared counter before broad public use. Each answer is capped at 600 output tokens. The SJTU weekly token quota remains enforced by the upstream service.

## Deploy

1. Install Node.js and Wrangler, then run `npx wrangler login` in this directory.
2. Store the real key as an encrypted Worker secret. Wrangler prompts for the value; do not put it in a command, file, or chat:
   ```sh
   npx wrangler secret put SJTU_API_KEY --config wrangler.toml
   ```
3. The default upstream is `https://models.sjtu.edu.cn/api/v1`. To override it for a permitted network gateway, configure `SJTU_API_BASE_URL` as a Worker variable. Never use a browser-side variable for credentials.
4. Deploy and check `/health`:
   ```sh
   npx wrangler deploy --config wrangler.toml
   ```
5. Set the deployed `/api/agent` URL in `_data/blog_agent.yml` under `endpoint`, then publish the site. Keep `endpoint` empty until the Worker has been deployed and verified from the required network.
6. Confirm the online-mode notice is visible and test a short request while connected to SJTU's network.

The Worker includes request validation, a response token cap, a timeout, strict origin checks, and a best-effort per-isolate rate limit. It is a lightweight personal-site endpoint, not a hardened public multi-tenant service. Review SJTU's API terms and privacy guidance before enabling it for public visitors.

## Verify locally

From the repository root, run:

```sh
node --test tests/test_blog_agent_worker.cjs
```
