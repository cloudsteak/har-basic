# HAR és agent harness: tanulási jegyzet

Gyakorlórepó: `har-basic`. Ez a jegyzet élő dokumentum, minden lecke után bővül.
Állapot: 2026-11-26, HAR CLI 1.31.0, profil: `cli`.

---

## 1. Mire jó ez az egész?

### A probléma

Egy kódoló ágenst (Claude Code, Cursor, Codex) elindítani könnyű. A nehéz része az, hogy **megbízzunk abban, amit csinált**:

- Honnan tudja az ágens, hogyan kell a projektet futtatni és tesztelni? Ez ma szét van szórva a README-ben, a `CLAUDE.md`-ben, a Cursor-szabályokban és a CI-yamlban, és idővel eltérnek egymástól.
- Ha egyszerre több ágens dolgozik ugyanazon a repón, ütköznek: közös dev szerver, közös adatbázis, közös portok, közös git állapot.
- Az ágens azt mondja: „lefuttattam a teszteket". Ezt csak úgy hihetjük el, ha újra lefuttatjuk magunk.
- Ha az ellenőrzés egy gyártó felhős felületén él, ágenst váltani azt jelenti, hogy újra kell építeni az egészet.
- A kézzel írt scriptek elavulnak: új függőség, új szolgáltatás, új env változó, és senki nem frissíti, amíg egy ágens futása érthetetlen hibával el nem bukik.

### A megoldás egy mondatban

> **Az ágens = modell + harness.** A modell dönt, a harness adja a környezetet, a korlátokat és az ellenőrzést.

A HAR ennek a harness-nek egy nyílt forráskódú megvalósítása kódoló ágensekre. Nem teszi okosabbá a modellt. Azt éri el, hogy **minden változás mellé bizonyíték kerül** arról, mi futott le, átment-e, és meddig tartott.

### DevOps-párhuzam

| Ismert világ                                          | HAR megfelelője                                            |
| ----------------------------------------------------- | ---------------------------------------------------------- |
| Infrastructure as Code: a környezet leírása a repóban | `.har/`: a futtatás és ellenőrzés leírása a repóban        |
| CI pipeline: egységes, ismételhető ellenőrzés         | `har env verify`: ugyanaz a pipeline minden ágensnek       |
| Izolált környezet fejlesztőnként (feature env)        | slot + git worktree + külön port és adatbázis              |
| Audit trail, artifact                                 | `runs/` és `validations/`: bizonyíték                      |
| Branch protection / gate                              | commit gate: bizonyíték nélkül nincs commit a worktree-ben |

Röviden: a HAR olyan, mint egy CI pipeline és egy izolált dev környezet, amit az ágens **a gépén, commit előtt** használ.

### Mit mér a benchmark?

A HAR README-je szerint 35 már mergelt pull requestet futtattak le kétszer, ugyanazzal a prompttal és Claude Opusszal: egyszer HAR-os repón, egyszer sima repón. Egyik prompt sem kérte, hogy az ágens tesztelje a munkáját.

|                                             | HAR-ral | Sima Claude Code |
| ------------------------------------------- | ------: | ---------------: |
| Lefuttatta a teljes verifikációs pipeline-t |   35/35 |             0/35 |
| Egyetlen ellenőrzés nélkül szállított       |       0 |            10/35 |
| Átment a rejtett teszteken                  |   19/35 |            17/35 |

A tanulság: a megoldott feladatok aránya kb. ugyanaz (zajon belül). A HAR **nem a minőséget növeli, hanem az ellenőrizhetőséget**. A reviewernek nem az ágens szavában kell hinnie.

---

## 2. Mi az a `.har/`?

A `.har/` könyvtár a repóba commitolt **szerződés** (contract): gépileg olvasható leírás arról, hogyan fut és hogyan ellenőrizhető a projekt. Cursor, Claude Code és Codex ugyanebből dolgozik, ezért nem kell eszközönként külön leírás.

### Verziókezelt rész (a contract)

| Fájl                     | Szerep                                                                                   |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| `harness.env`            | Beállítások: projektnév, worktree használata, portok, ökoszisztéma, infra szolgáltatások |
| `stages.json`            | Az ellenőrzési lépések listája, sorrendje, szintje (quick / full), és a commit gate      |
| `stages/`                | Stage-scriptek (pl. `readiness.sh`)                                                      |
| `manifest.json`          | A CLI által kezelt verzió és checksumok                                                  |
| `README.md`, `STAGES.md` | Részletes leírás ágenseknek és embereknek                                                |
| `../AGENTS.md`           | Rövid utasítás az ágensnek: először launch, utána verify, a végén megáll                 |

### Helyi rész (gitignore, nem commitoljuk)

| Mappa             | Tartalom                                         |
| ----------------- | ------------------------------------------------ |
| `slots/`          | Az aktív slotok állapota                         |
| `runs/`           | Minden parancs futásának naplója                 |
| `validations/`    | A verify bizonyítéka: tree hash, branch, státusz |
| `state/`          | Infrastruktúra-állapot                           |
| `ADAPT-PROMPT.md` | Prompt a harness testreszabásához                |

---

## 3. Alapfogalmak

- **Harness:** az ágens köré épített keret: eszközök, környezet, korlátok, ellenőrzés.
- **Contract:** a `.har/` tartalma. Egyetlen forrás arról, hogyan kell futtatni és ellenőrizni a projektet.
- **Slot:** egy ágens saját munkaterülete (1–3). Külön branch, külön portok, szükség esetén külön adatbázis.
- **Worktree:** a slot git worktree-je (`~/worktrees/...`). Az ágens csak itt szerkeszt, a fő checkout érintetlen. A worktree a **commitból** jön létre, a nem commitolt fájlok nincsenek benne.
- **Stage:** egy ellenőrzési lépés. A `verificationStages` sorrendjében futnak.
- **Tier:** a stage szintje. A `verify` a `quick` szintet futtatja, a `verify --full` az egész listát.
- **Validation / evidence:** a verify eredménye, amit a kód pontos állapotához (tree hash) köt. Ha a kód változik, a régi bizonyíték nem érvényes.
- **Commit gate:** a `stages.json`-ban beállított szabály (`mode: block`, `scope: worktrees`): a worktree-ben érvényes bizonyíték nélkül nem lehet commitolni. _(A 3. leckében próbáljuk ki.)_
- **Mission Control:** helyi dashboard a repókról, slotokról, futásokról és bizonyítékokról.

### A har-basic stage-ei

| Stage        | Szint | Parancs                                       |
| ------------ | ----- | --------------------------------------------- |
| `typecheck`  | quick | `npm run typecheck`                           |
| `unit-tests` | full  | `npm test`                                    |
| `lint`       | full  | `npm run lint`                                |
| `readiness`  | full  | kihagyva, amíg a `HARNESS_READINESS_CMD` üres |

---

## 4. Egy feladat életciklusa

```
Discover → Isolate → Build → Verify → Hand off
```

1. **Discover:** az ágens beolvassa a contractot (stack, scriptek, ellenőrzések).
2. **Isolate:** `har env launch 1` → új worktree, branch, portok.
3. **Build:** az ágens a worktree-ben szerkeszt és tesztel.
4. **Verify:** `har env verify 1 --full` → pipeline, bizonyíték.
5. **Hand off:** a branch és a bizonyíték megmarad review-hoz. Az ágens megáll, nem pushol, nem nyit PR-t. `har env teardown 1` / `complete 1` zárja le a slotot.

Fontos szabály: a commitot, a pusht és a lezárást **mindig ember végzi**.

---

## 5. Tanulási út

- [x] **1. Alapfogalmak:** harness, contract, slot, worktree, stage
- [x] **2. Első kör:** `launch` → `verify --full` zöld (worktree: `init-c706-har-agent-1-8a2b`)
- [ ] **3. Commit gate:** bukó teszttel kipróbálni, hogyan blokkol
- [ ] **4. Testreszabás:** `stages.json`, saját stage, readiness smoke, `har env maintain`
- [ ] **5. Ágens-integráció:** Claude Code + MCP (`har_launch_environment`), `AGENTS.md`
- [ ] **6. Több ágens párhuzamosan:** slotok, Mission Control, OTel-telemetria
- [ ] **7. Éles minta:** Docker sandbox, éjszakai ágens-VM (`mentor-agent-workspace`)
- [ ] **8. Mérés és bizalom:** mit bizonyít a verify, és mit nem

---

## 6. 1. lecke: ellenőrző kérdések

Válaszolj a saját szavaiddal, aztán beszéljük át.

**1. Miért jobb egy `.har/` contract, mint ha a README-ben, a `CLAUDE.md`-ben és a CI-yamlban is leírod, hogyan kell futtatni a projektet?**

Válaszom:

**2. Mi a különbség a `verify` és a `verify --full` között, és melyik stage-ek tartoznak a quick szintbe?**

Válaszom:

**3. (a 2. leckéből) Mi köti a bizonyítékot a kódhoz, hogy utólag ne lehessen átírni a kódot úgy, hogy a „pass" megmaradjon?**

Válaszom:

---

## 7. Tapasztalatok és hibakeresés (har-basic)

| Tünet                                                  | Ok                                                                                                  | Megoldás                                                                   |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `verify` bukik, `ENOENT package.json`                  | Nincs `package.json`, így nincs mit futtatni                                                        | Minimális Node-projekt: `typecheck`, `test`, `lint` scriptek               |
| A worktree-ben nincsenek az új fájlok                  | A worktree a commitból jön, nem a munkakönyvtárból                                                  | Először commit, utána `launch`                                             |
| A launch a repo rootot használja (_worktree disabled_) | Repo-szintű beállítás (`Worktree: off`) felülírja a `harness.env`-et                                | `har worktree on`, teardown, új launch                                     |
| zsh: `no matches found` / `#` hibák                    | Az interaktív zsh nem kezeli a `#` megjegyzést (`setopt interactive_comments`)                      | Megjegyzés nélkül másold a parancsot                                       |
| `.har/validations/` hiányzik                           | Takarítás után a mappa újra létrejön az első verify-nál                                             | Futtass `verify`-t                                                         |
| Mission Control: _Worktree path is missing on disk_    | A dashboard a saját nézőpontjából ellenőrzi az útvonalat (Dockerben nem látja a host fájlrendszert) | `har env status` az igazság forrása. _(Forráskód alapján, ellenőrizendő.)_ |
| A teardown után megmaradnak a naplók                   | Az állapot (slot, worktree) és a bizonyíték (`runs/`, `validations/`) külön él, szándékosan         | `har control reset --dry-run`, vagy `rm -rf .har/runs .har/validations`    |

### Általános tanulságok

- A beállítások rétegesek: commitolt contract (`harness.env`) és gépszintű, repóhoz kötött override. Hibakereséskor a `har env status` mutatja a ténylegesen érvényes értéket.
- A harness **nem a modellt javítja**, hanem a folyamatot: izolál, ellenőriz, bizonyítékot ad.

---

## 8. Parancs-cheatsheet

```bash
har onboard                  # .har/ scaffold, prompt az ágensnek
har worktree on              # worktree mód bekapcsolása a repóhoz
har env launch 1             # slot indítása (worktree + branch + portok)
har env status               # slotok és az érvényes beállítások
har env verify 1             # quick szint
har env verify 1 --full      # teljes pipeline, bizonyíték rögzítése
har env teardown 1           # slot lezárása (a branch megmarad)
har env complete 1           # slot lezárása feladat végén
har env maintain             # harness frissítés, drift-ellenőrzés
har env cleanup              # elavult session worktree-k takarítása
har control sync             # slot- és futásállapot küldése a Mission Controlnak
har control reset --dry-run  # Mission Control adat és helyi előzmények törlése (előbb dry-run!)
```

---

## 9. Nyitott kérdések és bővítendő anyagok

- [ ] Hogyan viselkedik a commit gate bukó teszt esetén? (3. lecke)
- [ ] Saját stage írása (pl. `shellcheck`, `terraform validate`) és a `readiness` smoke (4. lecke)
- [ ] Hogyan hívja az ágens a harnesst MCP-n keresztül? (5. lecke)
- [ ] Hogyan skálázódik több párhuzamos ágensre? (6. lecke)
- [ ] Hogyan illeszthető a HAR az éjszakai ágens-VM-hez? (7. lecke)
- [ ] Mit **nem** bizonyít a verify? (8. lecke)

## Források

- HAR repó: https://github.com/os-factory/har
- Dokumentáció: https://harproject.dev/
