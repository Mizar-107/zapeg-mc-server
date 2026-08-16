# ZapeG Citizens — host setup

ZapeG Citizens has two runtime pieces:

- the Numen and ZapeG Citizens Forge mods run in Minecraft; and
- one private `citizen-brain` container uses the shared Ollama account for every
  citizen and keeps their conversational memory in SQLite.

Players do not run the brain and never receive the Ollama key. The old `muhtar`
Compose profile was an unrelated single chat-character prototype and has been
removed. `citizen-brain` replaces only that prototype; the optional Heraldor
service is unchanged.

## Before starting

Run these commands from the checked-out `zapeg-server` directory on the Linux
host. Confirm the three pinned client/server components are present:

```bash
git pull --ff-only
test -f overrides/mods/zapeg-citizens-forge-1.20.1-0.2.1.jar
test -f overrides/mods/cc-tweaked-1.20.1-forge-1.116.1.jar
printf '%s  %s\n' \
  '00DCFB4820CCD8B1F85B091668C274A4CD335087B68088AECB7D5609CAFB9801' \
  'overrides/mods/zapeg-citizens-forge-1.20.1-0.2.1.jar' | sha256sum -c -
printf '%s  %s\n' \
  'FFFA7EAC48606DBC9F8E88DDF6C09EF218F0004B42F165F5476B700788806C9E' \
  'overrides/mods/cc-tweaked-1.20.1-forge-1.116.1.jar' | sha256sum -c -
grep -F 'CF_EXCLUDE_MODS: "cc-tweaked"' docker-compose.yml
grep -F 'CF_FORCE_SYNCHRONIZE: "true"' docker-compose.yml
grep -i numen extras/cf-mods.txt
```

Do not start the production world if either check fails. The exact same Numen and
ZapeG Citizens versions must be in the player pack before anyone joins.

## One-time secret setup

The Ollama API key and the bridge token are different secrets. The key is mounted
only into `citizen-brain`. The random bridge token is shared only by `mc` and
`citizen-brain` so they can authenticate their private HTTP calls.

```bash
mkdir -p secrets
chmod 700 secrets
umask 077
BRIDGE_TOKEN="$(openssl rand -hex 32)"
read -rsp 'Paste the Ollama API key, then press Enter: ' OLLAMA_KEY; echo
printf '%s' "$OLLAMA_KEY" > secrets/citizens_ollama_api_key.txt
unset OLLAMA_KEY
chmod 600 secrets/citizens_ollama_api_key.txt

test -f .env || cp .env.example .env
chmod 600 .env
if grep -q '^CITIZENS_BRAIN_TOKEN=' .env; then
  sed -i "s|^CITIZENS_BRAIN_TOKEN=.*|CITIZENS_BRAIN_TOKEN=$BRIDGE_TOKEN|" .env
else
  printf 'CITIZENS_BRAIN_TOKEN=%s\n' "$BRIDGE_TOKEN" >> .env
fi
unset BRIDGE_TOKEN
if grep -q '^CITIZENS_BRAIN_URL=' .env; then
  sed -i 's|^CITIZENS_BRAIN_URL=.*|CITIZENS_BRAIN_URL=http://citizen-brain:8787|' .env
else
  printf '%s\n' 'CITIZENS_BRAIN_URL=http://citizen-brain:8787' >> .env
fi
test -s secrets/citizens_ollama_api_key.txt
grep -Eq '^CITIZENS_BRAIN_TOKEN=.+$' .env
```

Do not paste either secret into Discord, an issue, a commit, or a client pack.
Both `.env` and `secrets/` are gitignored. The default cloud settings are:

```dotenv
CITIZENS_LLM_URL=https://ollama.com/api/chat
CITIZENS_LLM_MODEL=gpt-oss:20b
```

Change those only in the host's `.env`. `CITIZENS_LLM_*` is passed exclusively to
the brain container. Port 8787 is not published to the host or internet.

## Build and start

The build is pinned to the public `zapeg-citizens` tag `v0.2.1`, specifically its
`brain/` directory. This starts/recreates Minecraft, its backup service, and the
opt-in brain:

```bash
docker compose --profile citizens config --quiet
docker compose --profile citizens build --pull citizen-brain
docker compose stop mc
rm -f -- data/mods/cc-tweaked-1.20.1-forge-1.113.1.jar
rm -f -- data/mods/zapeg-citizens-forge-1.20.1-0.2.0.jar
test ! -e data/mods/cc-tweaked-1.20.1-forge-1.113.1.jar
test ! -e data/mods/zapeg-citizens-forge-1.20.1-0.2.0.jar
docker compose --profile citizens up -d mc backup citizen-brain
docker compose --profile citizens ps
```

The first command prints nothing when the Compose model is valid. The Minecraft
container copies the tracked jar from `overrides/mods/` through its dedicated
`MODS` source; do not manually copy a different Citizens jar into `data/mods/`.
The narrowly exact `rm` commands remove only ATM9's retired CC:Tweaked 1.113.1
and the previous Citizens 0.2.0 jar from the persistent server directory before
recreation. Do not replace them with wildcard deletion. `CF_EXCLUDE_MODS` plus
`CF_FORCE_SYNCHRONIZE` prevents AUTO_CURSEFORGE from restoring the base CC copy,
while `/citizens-mods` installs the pinned CC 1.116.1 and Citizens 0.2.1 jars.

## Verify before inviting players

Wait until `mc` and `citizen-brain` report healthy, then run:

```bash
docker compose --profile citizens ps
docker compose --profile citizens logs --tail=100 citizen-brain
docker compose exec -T mc rcon-cli "citizen brain-status"
docker compose exec -T mc rcon-cli "citizen list"
find data/mods -maxdepth 1 -type f -name 'cc-tweaked-1.20.1-forge-*.jar' -print
test "$(find data/mods -maxdepth 1 -type f -name 'cc-tweaked-1.20.1-forge-*.jar' -print | wc -l)" -eq 1
test -f data/mods/cc-tweaked-1.20.1-forge-1.116.1.jar
find data/mods -maxdepth 1 -type f -name 'zapeg-citizens-forge-*.jar' -print
test "$(find data/mods -maxdepth 1 -type f -name 'zapeg-citizens-forge-*.jar' -print | wc -l)" -eq 1
test -f data/mods/zapeg-citizens-forge-1.20.1-0.2.1.jar
```

The status command must say `Shared brain: configured`, not `disabled`. The brain
logs must not contain configuration, authentication, or provider errors. Container
health proves the private service is running; the Ollama key is exercised on the
first real citizen turn. The CC:Tweaked and Citizens checks must each show exactly
one pinned jar (1.116.1 and 0.2.1 respectively); stop here if an older copy remains.

For the acceptance test, have one player join, then an OP runs:

```text
/citizen spawn TestCitizen ONLINE_USERNAME
```

That player sends this in normal Minecraft chat:

```text
@TestCitizen report your status and do not move
```

After a successful reply, clean up with:

```text
/citizen remove TestCitizen
```

Test movement and mining later in an unclaimed disposable area, not beside the
production base. One Ollama key serves all citizens; the brain serializes provider
access by default, so simultaneous requests may wait briefly.

## Back up citizen memory

The normal Minecraft backup does not include the separate named brain volume.
Before a Citizens update, stop the brain briefly and make a consistent archive:

```bash
mkdir -p backups
docker compose --profile citizens stop citizen-brain
docker compose --profile citizens run --rm --no-deps --user 0:0 \
  -v "$PWD/backups:/backup" --entrypoint sh citizen-brain \
  -c 'tar -czf /backup/citizen-brain-$(date +%Y%m%d-%H%M%S).tgz -C /data .'
docker compose --profile citizens start citizen-brain
ls -lh backups/citizen-brain-*.tgz | tail -1
```

Treat this archive as private player data. Keep it with the protected server
backups, not in Git or the client pack.

## Safe disable / rollback

First remove any test citizens. Then disable LLM control without deleting the
world or its brain memory:

```bash
sed -i 's|^CITIZENS_BRAIN_URL=.*|CITIZENS_BRAIN_URL=|' .env
docker compose --profile citizens stop citizen-brain
docker compose --profile citizens rm -f citizen-brain
docker compose up -d --force-recreate mc backup
docker compose exec -T mc rcon-cli "citizen brain-status"
```

The last command must report that the shared brain is disabled. The named
`citizen-brain-data` volume is intentionally preserved, making this rollback
recoverable. Do not delete that volume or remove the mod jars while managed
citizens still exist. Re-enable by restoring the internal URL and rerunning the
build/start/verify commands above.

## Troubleshooting

- `citizen-brain` exits immediately: check that the model and both secrets are
  non-empty; do not print them while diagnosing.
- `brain-status` says disabled: set the internal URL in `.env`, ensure the bridge
  token is non-empty, and recreate `mc` (a restart alone cannot change env vars).
- HTTP/authentication failure after spawning: recreate both services so they read
  the same bridge token.
- Ollama authentication/model error: correct the host-only key or model, then
  recreate only `citizen-brain`.
- Players cannot join: verify their pack has the exact pinned Numen and Citizens
  jars. Never send them the host `.env` or anything in `secrets/`.
