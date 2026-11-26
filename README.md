# har-basic

Tanulórepó: a [HAR](https://github.com/os-factory/har) agent harness felépítése nulláról, CLI-profilon.

A HAR a kódoló agent köré tett keret. A `.har/` könyvtár leírja, hol dolgozhat az agent, milyen ellenőrzéseket kell lefuttatnia, és milyen bizonyíték marad utána. Cursor, Claude Code és Codex ugyanebből a szerződésből dolgozik.

Részletes tanulási jegyzet (koncepció, fogalmak, hibakeresés, cheatsheet): [`docs/har-tanulas.md`](docs/har-tanulas.md).

## Amit eddig csináltam

Node 24.22.2, az `nvm`-en keresztül:

```bash
nvm use 24.22.2
npm install -g @osfactory/har
har onboard --yes --profile cli
```

A `har onboard` 2026-11-26-án futott le, a CLI verziója `1.31.0`. A `--yes` a kérdéseket az alapértelmezéssel válaszolta meg. A `--profile cli` könyvtárhoz és parancssori programhoz való sablont másolt ide: közös Docker-szolgáltatás és webes dev szerver nélkül, legfeljebb 3 párhuzamos agent-sávval (`agentSlots` 1–3).

Ezután egy minimális Node-projektet adtam hozzá (`package.json`, `tsconfig.json`, `eslint.config.js`, `src/`), hogy a verify-nak legyen mit futtatnia.

## Mit hozott létre

| Hol                        | Mire való                                                                                                |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| `.har/harness.env`         | A szerződés beállításai: worktree be van kapcsolva, az ökoszisztéma `auto`, a közös infrastruktúra üres. |
| `.har/stages.json`         | Az ellenőrzések listája, és a commit gate: worktree-ben bizonyíték nélkül a commit tiltva van.           |
| `.har/stages/readiness.sh` | Opcionális füstteszt. A `HARNESS_READINESS_CMD` üres, ezért ez a lépés jelenleg azonnal sikeres.         |
| `.har/manifest.json`       | A CLI által kezelt verzió és checksumok.                                                                 |
| `AGENTS.md`                | Rövid utasítás az agentnek: először launch, utána verify, a végén megáll a handoffnál.                   |
| `.har/README.md`           | Részletes harness-leírás agenteknek.                                                                     |

A futások naplója (`.har/runs/`), a bizonyíték (`.har/validations/`), a slot-állapot és az `ADAPT-PROMPT.md` a `.har/.gitignore` szerint nem kerül gitbe.

## A példaprojekt

Egy apró Node-projekt, a tartalma szándékosan egyszerű: a HAR-t nem a kód érdekli, hanem hogy a scriptek lefutnak-e.

| Fájl                | Szerep                                  |
| ------------------- | --------------------------------------- |
| `src/greet.js`      | `greet(name)` függvény                  |
| `src/greet.test.js` | `node:test` tesztek a függvényhez       |
| `src/cli.js`        | parancssori belépési pont               |

| Script      | Parancs                         |
| ----------- | ------------------------------- |
| `typecheck` | `tsc --noEmit`                  |
| `test`      | `node --test "src/**/*.test.js"` |
| `lint`      | `eslint .`                      |

## Egy feladat menete

```bash
har env launch 1          # friss worktree és branch az 1-es sávon
har env verify 1          # gyors kör: a quick szintű stage-ek
har env verify 1 --full   # teljes kör: typecheck, unit-tests, lint, readiness
har env complete 1        # a worktree megy, a branch megmarad
```

A szerkesztés a launch által kiírt worktree-ben történik (`~/worktrees/<alap branch>-<sha4>-har-agent-<slot>-<véletlen>`). A fő checkout közben marad, ahonnan a session indult.

Fontos tudnivalók:

- **A worktree a commitból készül.** Ami nincs commitolva, nincs benne, ezért a launch előtt commitolni kell.
- **A commit gate csak a worktree-ben véd.** A fő checkouton verify nélkül is lehet commitolni.
- **Hol állok?** `pwd` és `git branch --show-current`. Ha a branch `init`, a fő checkouton vagyok, ha `init-<sha4>-har-agent-<slot>-<rand>`, a worktree-ben.
- **A teardown nem töröl naplót.** A `har env teardown 1` a worktree-t és az env fájlt törli, a branch és a bizonyíték megmarad.

A verify ezeket a parancsokat hívja, ebben a sorrendben:

| Stage        | Szint | Parancs                                      |
| ------------ | ----- | -------------------------------------------- |
| `typecheck`  | quick | `npm run typecheck`                          |
| `unit-tests` | full  | `npm test`                                   |
| `lint`       | full  | `npm run lint`                               |
| `readiness`  | full  | kihagyva, amíg nincs `HARNESS_READINESS_CMD` |

A `har env verify 1 --full` zölden lefut a példaprojekten.

## Mission Control

A HAR dashboardja (`http://localhost:3847`) alapból egy `har-control` nevű Docker-kontérben fut, és csak a saját `/data` kötetét látja. A host mappáit nem, ezért minden aktív worktree-re azt írja: *„Worktree path is missing on disk"*. Ez nem valódi hiba.

Megoldás: a kontér újraindítása úgy, hogy a `~/worktrees` és a `~/dev` read-only, ugyanazzal az útvonallal látszik benne:

```bash
mkdir -p ~/worktrees
docker rm -f har-control
docker run -d --restart unless-stopped --name har-control -p 3847:3847 \
  -v har_control_data:/data \
  -v "$HOME/worktrees":"$HOME/worktrees":ro \
  -v "$HOME/dev":"$HOME/dev":ro \
  -e DATABASE_URL=file:/data/har_control.db theosfactory/har-control:1.31.0
```

Ezután a `har control sync` frissíti az adatokat, és a „Needs attention" 0 lesz.

Megjegyzések:

- A `har control up` a HAR forráskódja alapján a kontért mount nélkül hozza létre, ezért indításra és leállításra inkább `docker start har-control` és `docker stop har-control` való. *(A `har control up` viselkedését nem próbáltam ki.)*
- Takarítás: `har control reset --dry-run`, majd `har control reset --keep-registry`. Ez törli a Mission Control adatait és a helyi `.har/{runs,validations,state,slots}` mappákat, a contractot nem.
- Elavult slot sorok eltávolítása: `har env teardown <slot>`, majd `har control sync`.

## Következő lépések

1. A commit gate kipróbálása a worktree-ben: jó változtatás verify nélkül, verify után, és bukó teszttel.
2. Saját stage és readiness smoke a `stages.json`-ban (`har env maintain`).
3. Külön Python példarepó (`pyproject.toml`, `pytest`), mert ha van `package.json`, a HAR Node-nak veszi a projektet.
