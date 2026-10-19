# twitter-workspace

The maintenance workspace for [fa0311](https://github.com/fa0311)'s X / Twitter open-source projects: the OpenAPI spec
([twitter-openapi](https://github.com/fa0311/twitter-openapi)), its Python and TypeScript clients, [twitter-snap](https://github.com/fa0311/twitter-snap)
and its apps, [twitter_api_safe_relay](https://github.com/fa0311/twitter_api_safe_relay), and the supporting repositories, checked out as
submodules at the commits currently in use.

It is operated mostly by an AI agent working inside the `docker-compose.yml` sandbox. The documents are written for the next operator:

- [`CLAUDE.md`](CLAUDE.md): standing rules (how work is delivered, what must never happen).
- [`HANDOVER.md`](HANDOVER.md): the environment, the routine and the current state of the work.
- [`REFERENCE.md`](REFERENCE.md): facts about the sandbox, X and the repositories that cannot be derived from the code.
- [`tools/`](tools/README.md): local scripts for recording, sweeping and validating X responses; `tools/bootstrap.sh` prepares a fresh container.
- `.claude/memory/`: the agent's memory, mirrored so it survives the container.

```sh
git clone --recursive https://github.com/fa0311/twitter-workspace.git
cd twitter-workspace && docker compose up -d
```

`docker-compose.yml` expects the sandbox `Dockerfile` and an `.env` (with `GITHUB_TOKEN`) in the parent directory, and mounts the
host's gh, ssh and GPG configuration read-only. Secrets (`cookie.json`, `.sops/`) and the recorded X responses (`recordings/`) are not
part of the repository. Named volumes keep the agent's memory and the tool caches across container recreations.

## License

The documents and scripts in this repository are the maintainer's notes; each submodule keeps its own license.
