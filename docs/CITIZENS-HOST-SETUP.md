# ZapeG Citizens — host setup

ZapeG Citizens has two runtime pieces:

- the Numen and ZapeG Citizens Forge mods run in Minecraft; and
- one private `citizen-brain` container uses the shared Ollama account for every
  citizen and keeps conversational memory plus durable job plans, checkpoints and
  request journals in SQLite.

Players do not run the brain and never receive the Ollama key. The old `muhtar`
Compose profile was an unrelated single chat-character prototype and has been
removed. `citizen-brain` replaces only that prototype; the optional Heraldor
service is unchanged.

## Before starting

Run these commands from the checked-out `zapeg-server` directory on the Linux
host. Confirm the three pinned client/server components are present:

```bash
git pull --ff-only
test -f overrides/mods/zapeg-citizens-forge-1.20.1-0.4.0.jar
test -f overrides/mods/cc-tweaked-1.20.1-forge-1.116.1.jar
printf '%s  %s\n' \
  '47958FA283B08DE001E01E25F4F0AE67CB57B7BBBF79510EA0FB9F7481177A03' \
  'overrides/mods/zapeg-citizens-forge-1.20.1-0.4.0.jar' | sha256sum -c -
printf '%s  %s\n' \
  'FFFA7EAC48606DBC9F8E88DDF6C09EF218F0004B42F165F5476B700788806C9E' \
  'overrides/mods/cc-tweaked-1.20.1-forge-1.116.1.jar' | sha256sum -c -
grep -F 'CF_EXCLUDE_MODS: "cc-tweaked"' docker-compose.yml
grep -F 'CF_FORCE_SYNCHRONIZE: "true"' docker-compose.yml
grep -Fx 'numen-ai:8551640' extras/cf-mods.txt
```

Do not start the production world if any check fails. The exact same Numen and
ZapeG Citizens versions must be in the player pack before anyone joins.
The reviewed v0.4.0 JAR is 191,061 bytes. Its exact filename and SHA-256 must match
both inventory locks before deploying or generating either player pack.

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
CITIZENS_JOB_MAX_ACTIONS=128
CITIZENS_JOB_MAX_MODEL_CALLS=192
CITIZENS_JOB_MAX_ACTIVE_SECONDS=10800
CITIZENS_MAX_ACTIVE_JOBS=16
CITIZENS_MAX_TOOL_ARGUMENT_CHARS=262144
```

Change those only in the host's `.env`. `CITIZENS_LLM_*` is passed exclusively to
the brain container. The `CITIZENS_JOB_*` budgets are enforced by Minecraft;
`CITIZENS_MAX_*` bounds brain concurrency and persisted/model context. The defaults
are deliberately much larger than an ordinary dialogue turn, but they remain
finite. Raise them only after observing Ollama latency, TPS, model quality and
SQLite growth. Port 8787 is not published to the host or internet.

## Build and start

The build is pinned by commit in `docker-compose.yml` (`build.context` ref on
the public `zapeg-citizens` repo, `brain/` directory). Citizens 0.4.0 uses brain
document protocol 3: deploy the 0.4.0 JAR and brain together. A mixed
protocol-1/2/3 rollout is unsupported and deliberately fails instead of silently
corrupting a turn or durable job.

**Brain 0.4.1 (2026-08-21, brain-only — the 0.4.0 JAR is unchanged):** adds
Muhtar's village memory cards. Compose now mounts `npc/village-memory-tr.md`
read-only and sets `CITIZENS_VILLAGE_MEMORY_FILE`; the brain refuses to start
(fail-closed) if the file is missing, empty, or over 40 cards / 4000 chars, so
a bad edit surfaces as a visible boot error, not a silent lore loss. Rebuild
the image (`docker compose --profile citizens build --pull citizen-brain`) and
recreate the brain container to pick it up; no world/JAR step is needed. Only
SERVER-owned citizens receive the cards.

Take a maintenance window with no players. The retiring 0.3.0 release does not yet
have `citizen jobs` or durable-job status. Use its existing `citizen list` and
`citizen brain-status` commands instead. Let any active turn finish, or stop the
named server citizen with `citizen stop <name>`, then wait until `brain-status`
reports `0 active turn(s)`. Player-owned 0.3.0 work cancels when its owner logs out.
Use `citizen jobs` and the durable status controls only after 0.4.0 has started.

The sequence below then creates a paired world/brain backup, stops Minecraft before
the brain, removes exact retired JARs and recreates Minecraft, backup and the opt-in
brain as one coordinated rollout:

```bash
set -euo pipefail
docker compose --profile citizens config --quiet
docker compose --profile citizens build --pull citizen-brain
docker compose exec -T mc rcon-cli "citizen list"
docker compose exec -T mc rcon-cli "citizen brain-status"
PAIR_ID="$(date +%Y%m%d-%H%M%S)-pre-citizens-0.4.0"
docker compose stop backup
docker compose stop mc
docker compose --profile citizens stop citizen-brain
scripts/snapshot.sh "$PAIR_ID-world"
docker compose --profile citizens run --rm --no-deps --user 0:0 \
  -v "$PWD/backups:/backup" --entrypoint sh citizen-brain \
  -c "tar -czf /backup/${PAIR_ID}-citizen-brain.tgz -C /data ."
rm -f -- data/mods/cc-tweaked-1.20.1-forge-1.113.1.jar
rm -f -- data/mods/zapeg-citizens-forge-1.20.1-0.2.0.jar
rm -f -- data/mods/zapeg-citizens-forge-1.20.1-0.2.1.jar
rm -f -- data/mods/zapeg-citizens-forge-1.20.1-0.3.0.jar
test ! -e data/mods/cc-tweaked-1.20.1-forge-1.113.1.jar
test ! -e data/mods/zapeg-citizens-forge-1.20.1-0.2.0.jar
test ! -e data/mods/zapeg-citizens-forge-1.20.1-0.2.1.jar
test ! -e data/mods/zapeg-citizens-forge-1.20.1-0.3.0.jar
docker compose --profile citizens up -d --force-recreate citizen-brain mc backup
docker compose --profile citizens ps
ls -lh snapshots/*"$PAIR_ID"* backups/"$PAIR_ID"-citizen-brain.tgz
```

The first command prints nothing when the Compose model is valid. The Minecraft
container copies the tracked jar from `overrides/mods/` through its dedicated
`MODS` source; do not manually copy a different Citizens jar into `data/mods/`.
The narrowly exact `rm` commands remove only ATM9's retired CC:Tweaked 1.113.1
and the previous Citizens 0.2.0/0.2.1/0.3.0 jars from the persistent server directory
before recreation. Do not replace them with wildcard deletion. `CF_EXCLUDE_MODS` plus
`CF_FORCE_SYNCHRONIZE` prevents AUTO_CURSEFORGE from restoring the base CC copy,
while `/citizens-mods` installs the pinned CC 1.116.1 and Citizens 0.4.0 jars.

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
find data/mods -maxdepth 1 -type f -name 'numen-forge-*.jar' -print
test "$(find data/mods -maxdepth 1 -type f -name 'numen-forge-*.jar' -print | wc -l)" -eq 1
test -f data/mods/numen-forge-1.20.1-0.1.1-all.jar
find data/mods -maxdepth 1 -type f -name 'zapeg-citizens-forge-*.jar' -print
test "$(find data/mods -maxdepth 1 -type f -name 'zapeg-citizens-forge-*.jar' -print | wc -l)" -eq 1
test -f data/mods/zapeg-citizens-forge-1.20.1-0.4.0.jar
```

The status command must say `Shared brain: configured`, not `disabled`. The brain
logs must not contain configuration, authentication, or provider errors. Container
health proves the private service is running; the Ollama key is exercised on the
first real citizen turn. The CC:Tweaked and Citizens checks must each show exactly
one pinned jar (1.116.1 and 0.4.0 respectively), and Numen must be exactly 0.1.1;
stop here if an older copy remains.

For the protocol-3 acceptance test, have one player join in a disposable,
unclaimed area, then an OP runs:

```text
/citizen spawn TestCitizen ONLINE_USERNAME
```

That player sends this in normal Minecraft chat:

```text
@TestCitizen inspect your inventory, report the exact occupied slots, then finish without moving
@TestCitizen status
```

While it is running, an OP checks the persistent history. The final row must be
`COMPLETED` with at least one recorded action, or `CANCELED` only if you explicitly
stopped it. This smoke check proves the job round trip and journal; status output
does not expose an action's internal read-only classification:

```text
/citizen status TestCitizen
/citizen jobs TestCitizen
```

If the model asks for a choice, reply with `@TestCitizen answer <answer>` (a plain
`@TestCitizen <answer>` also works while it is waiting). Exercise cancellation once
with a second harmless job, then clean up:

```text
@TestCitizen inspect the block I am looking at and wait for my next instruction
@TestCitizen stop
/citizen jobs TestCitizen
```

`brain-status` must report `Durable jobs: enabled`. Before removing the test
citizen, perform one coordinated restart and verify that the completed/canceled
history returns without an active job:

```bash
set -euo pipefail
docker compose stop backup
docker compose stop mc
docker compose --profile citizens stop citizen-brain
docker compose --profile citizens up -d citizen-brain mc backup
docker compose --profile citizens ps
docker compose exec -T mc rcon-cli "citizen brain-status"
docker compose exec -T mc rcon-cli "citizen jobs TestCitizen"
docker compose exec -T mc rcon-cli "citizen remove TestCitizen"
```

Wait for `mc` and `citizen-brain` to become healthy before the three RCON checks.
No pending job may reappear after the restart or removal.

### Durable job controls and expectations

Player-owned workers accept a goal through `@Name <goal>`. They also understand
`@Name status`, `@Name stop`, and `@Name answer <answer>`. OP controls work for both
ownership kinds:

```text
/citizen task <serverCitizen> <goal>
/citizen status <name>
/citizen jobs [name]
/citizen resume <name> [answer]
/citizen stop <name>
```

At submission, the job records the actor's dimension, position, rotation and
looked-at block, so “here,” “this plot,” and “these chests” keep a stable anchor.
Minecraft executes one Numen world action at a time and stores the pending action
and result in its world ledger. The brain stores the plan, compact checkpoint,
recent evidence and idempotent request journal in SQLite. Unknown mutating outcomes
force a read-only observation before more changes, and the model cannot claim
completion without successful cited evidence and a later verification after the
last mutation.

The planner can load four closed, server-owned workflows—`storage`, `building`,
`mining`, and `combat`—in addition to Numen's 32 server-executable tools. It cannot
load arbitrary paths, run commands/RCON, or use Numen's client-only tools.

Practical boundaries for the first live version:

- Sorting nearby chests may span many open/inspect/transfer/close actions and can
  add overflow storage, but items stage through the citizen's inventory. A huge
  warehouse is slower than a dedicated storage macro.
- Diamond work handles normal and deepslate ore but searches known/loaded terrain,
  not an unlimited blind branch mine. Supply a suitable pick, food and empty slots.
- Numen's build primitive accepts up to 16,384 resolved cells. Large survival villas
  need staged materials because one freeform call preflights the citizen's inventory;
  creative/server-builder bodies are the most reliable initial test.
- Wither skeleton hunting works when the citizen is already in the Nether near an
  accessible fortress. Reliable autonomous portal/cross-dimension travel is not
  available in Numen 0.1.1.

A durable journal makes control and restart recovery safer; it does not bypass
claims, unloaded/unreachable targets, missing tools/materials, full containers or a
weak model decision. Test complex work on a copied world before production.

### Server-owned lore citizens

An OP can create an always-awake, server-owned character at the OP's current
position. Players talk to it with `@Name message`; OPs use explicit task commands
when it should act in the world:

```text
/citizen spawn-server Archivist lore village Remembers the settlement's history and greets visitors.
@Archivist Who founded this village?
/citizen task Archivist walk to the town bell and wait there
/citizen status Archivist
/citizen jobs Archivist
/citizen resume Archivist <answer-if-requested>
/citizen stop Archivist
/citizen persona Archivist You are the village archivist. Be concise and stay in character.
/citizen set-home Archivist
/citizen wake Archivist
/citizen remove Archivist
```

`spawn-server` accepts `name [role] [faction] [persona...]`; the shorter
`/citizen spawn-server Archivist` form uses the defaults. Server-owned bodies wake
after restart, keep their technical UUID and inventory, and recover at their saved
home after death. Their public lore dialogue remains available while a separate
operator-submitted physical job runs. They are intentionally always awake, so
keep the lore population small and use ordinary mobs for crowds or common enemies.
`/citizen task` must be entered by an in-game OP; console/RCON cannot impersonate
the speaking actor. When spawning or changing home from console/RCON, use an
explicit source such as:

```text
/execute in minecraft:overworld positioned 100 65 100 run citizen spawn-server Archivist ...
```

Use the same wrapper around `citizen set-home`.

Test movement and mining later in an unclaimed disposable area, not beside the
production base. One Ollama key serves all citizens; the brain serializes provider
access by default, so simultaneous requests may wait briefly.

## Back up durable citizen state

The normal Minecraft backup contains the world-side job ledger but not the separate
named brain volume. Never treat either half as a complete durable-job backup. Take a
maintenance window, let jobs finish or cancel them, verify zero dialogue/job HTTP
operations, stop Minecraft before the brain, and label both archives with one pair
ID. `citizen jobs` is only the ten newest history rows, so also run
`citizen status <name>` for every citizen returned by `citizen list`; do not start
the backup while any status is non-terminal:

```bash
set -euo pipefail
mkdir -p backups
docker compose exec -T mc rcon-cli "citizen list"
docker compose exec -T mc rcon-cli "citizen brain-status"
docker compose exec -T mc rcon-cli "citizen jobs"
PAIR_ID="$(date +%Y%m%d-%H%M%S)-citizens-pair"
docker compose stop backup
docker compose stop mc
docker compose --profile citizens stop citizen-brain
scripts/snapshot.sh "$PAIR_ID-world"
docker compose --profile citizens run --rm --no-deps --user 0:0 \
  -v "$PWD/backups:/backup" --entrypoint sh citizen-brain \
  -c "tar -czf /backup/${PAIR_ID}-citizen-brain.tgz -C /data ."
docker compose --profile citizens up -d citizen-brain mc backup
ls -lh snapshots/*"$PAIR_ID"* backups/"$PAIR_ID"-citizen-brain.tgz
```

Restore both artifacts from the same pair while both services are stopped. A
one-sided restore is detected conservatively, but jobs can require operator repair
or replacement because the world and sidecar disagree about the pending action.
Minecraft synchronously asks its `SavedData` store to save recovery-critical job
transitions, but Minecraft can log and swallow an underlying filesystem error; this
is a save barrier, not a separate write-ahead log. Treat the SQLite archive as
private player data and keep both artifacts in protected backups, not Git or the
client pack.

### Restore one coordinated pair

Never combine a world archive and brain archive with different pair IDs. Replace
the example ID below with the label shared by the two files. The commands validate
both archives, take an additional pre-restore safety copy, stop both state peers,
move the current world aside under ignored `snapshots/`, and archive the current
brain volume before replacing either side:

```bash
set -euo pipefail
PAIR_ID='20260817-120000-citizens-pair'
WORLD_ARCHIVE="$(find snapshots -maxdepth 1 -type f -name "*-${PAIR_ID}-world.tar.gz" -print -quit)"
BRAIN_ARCHIVE="$PWD/backups/${PAIR_ID}-citizen-brain.tgz"
test -n "$WORLD_ARCHIVE"
test -f "$BRAIN_ARCHIVE"
tar -tzf "$WORLD_ARCHIVE" >/dev/null
tar -tzf "$BRAIN_ARCHIVE" >/dev/null
scripts/snapshot.sh "pre-restore-${PAIR_ID}"
docker compose stop backup
docker compose stop mc
docker compose --profile citizens stop citizen-brain
BEFORE_ID="$(date +%Y%m%d-%H%M%S)-before-${PAIR_ID}"
docker compose --profile citizens run --rm --no-deps --user 0:0 \
  -v "$PWD/backups:/backup" --entrypoint sh citizen-brain \
  -c "tar -czf /backup/${BEFORE_ID}-citizen-brain.tgz -C /data ."
mv -- data "snapshots/data-${BEFORE_ID}"
mkdir -p data
tar -xzf "$WORLD_ARCHIVE" -C .
test -d data
docker compose --profile citizens run --rm --no-deps --user 0:0 \
  -v "$PWD/backups:/backup:ro" --entrypoint sh citizen-brain \
  -c "set -eu; find /data -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +; tar -xzf /backup/${PAIR_ID}-citizen-brain.tgz -C /data"
docker compose --profile citizens up -d --force-recreate citizen-brain mc backup
docker compose --profile citizens ps
docker compose exec -T mc rcon-cli "citizen brain-status"
docker compose exec -T mc rcon-cli "citizen list"
```

If startup validation fails, stop the services and restore
`snapshots/data-${BEFORE_ID}` plus
`backups/${BEFORE_ID}-citizen-brain.tgz`; do not continue playing on a half-restored
pair.

## Safe disable / rollback

First remove test citizens, finish or cancel every active job, and take the paired
backup above. Then disable LLM control without deleting the world or brain memory:

```bash
set -euo pipefail
docker compose exec -T mc rcon-cli "citizen list"
docker compose exec -T mc rcon-cli "citizen brain-status"
docker compose exec -T mc rcon-cli "citizen jobs"
docker compose stop backup
docker compose stop mc
docker compose --profile citizens stop citizen-brain
docker compose --profile citizens rm -f citizen-brain
sed -i 's|^CITIZENS_BRAIN_URL=.*|CITIZENS_BRAIN_URL=|' .env
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
- Protocol/version mismatch: confirm the server has only Citizens 0.4.0 and the
  brain image/build context both use `v0.4.0`/protocol 3; recreate both peers together.
- Job is paused: run `/citizen status <name>` and `/citizen jobs <name>`. Restore
  the missing owner/body/brain, supply a requested answer with `/citizen resume
  <name> <answer>`, or stop the job. A budget-exhausted job is intentionally not
  resumable without changing policy/code.
- After a crash or one-sided restore, do not delete only one state store or blindly
  replay a mutating task. Preserve logs and both backups; the recovery barrier may
  require a read-only world observation or operator repair before work continues.
- Ollama authentication/model error: correct the host-only key or model, then
  recreate only `citizen-brain`.
- Players cannot join: verify their pack has the exact pinned Numen and Citizens
  jars. Never send them the host `.env` or anything in `secrets/`.
