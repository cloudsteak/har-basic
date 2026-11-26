# har-basic

Tanulórepó: a [HAR](https://github.com/os-factory/har) agent harness felépítése nulláról, CLI-profilon.

A HAR a kódoló agent köré tett keret. A `.har/` könyvtár leírja, hol dolgozhat az agent, milyen ellenőrzéseket kell lefuttatnia, és milyen bizonyíték marad utána. Cursor, Claude Code és Codex ugyanebből a szerződésből dolgozik.

## Amit eddig csináltam

Node 24.22.2, az `nvm`-en keresztül:

```bash
nvm use 24.22.2
npm install -g @osfactory/har
har onboard --yes --profile cli
```

A `har onboard` 2026-11-26-án futott le, a CLI verziója `1.31.0`. A `--yes` a kérdéseket az alapértelmezéssel válaszolta meg. A `--profile cli` könyvtárhoz és parancssori programhoz való sablont másolt ide: közös Docker-szolgáltatás és webes dev szerver nélkül, legfeljebb 3 párhuzamos agent-sávval (`agentSlots` 1–3).

## Mit hozott létre

| Hol                        | Mire való                                                                                                |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| `.har/harness.env`         | A szerződés beállításai: worktree be van kapcsolva, az ökoszisztéma `auto`, a közös infrastruktúra üres. |
| `.har/stages.json`         | Az ellenőrzések listája, és a commit gate: worktree-ben bizonyíték nélkül a commit tiltva van.           |
| `.har/stages/readiness.sh` | Opcionális füstteszt. A `HARNESS_READINESS_CMD` üres, ezért ez a lépés jelenleg azonnal sikeres.         |
| `.har/manifest.json`       | A CLI által kezelt verzió és checksumok.                                                                 |
| `AGENTS.md`                | Rövid utasítás az agentnek: először launch, utána verify, a végén megáll a handoffnál.                   |
| `.har/README.md`           | Részletes harness-leírás agenteknek.                                                                     |

A futások naplója (`.har/runs/`), a slot-állapot és az `ADAPT-PROMPT.md` a `.har/.gitignore` szerint nem kerül gitbe.

## Egy feladat menete

```bash
har env launch 1          # friss worktree és branch az 1-es sávon
har env verify 1          # gyors kör: a quick szintű stage-ek
har env verify 1 --full   # teljes kör: typecheck, unit-tests, lint, readiness
har env complete 1        # a worktree megy, a branch megmarad
```

A szerkesztés a launch által kiírt worktree-ben történik. A fő checkout közben marad, ahonnan a session indult.

A verify most ezeket a parancsokat hívná, ebben a sorrendben:

| Stage        | Szint | Parancs                                      |
| ------------ | ----- | -------------------------------------------- |
| `typecheck`  | quick | `npm run typecheck`                          |
| `unit-tests` | full  | `npm test`                                   |
| `lint`       | full  | `npm run lint`                               |
| `readiness`  | full  | kihagyva, amíg nincs `HARNESS_READINESS_CMD` |

Ezek a CLI-sablon általános Node-parancsai. A repóban még nincs `package.json`, ezért a verify-nak egyelőre nincs mit futtatnia.

## Következő lépés

Egy minimális Node-projekt, `typecheck`, `test` és `lint` scriptekkel, hogy a `har env verify 1 --full` ezen a repón ténylegesen le tudjon futni. A stage-ek utána ehhez a projekthez igazíthatók (`har env maintain`).
