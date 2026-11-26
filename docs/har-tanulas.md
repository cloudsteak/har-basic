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

### Fő checkout és worktree: hol mi van?

Egyszerű hasonlat: van egy dokumentumod, az az **eredeti**. Mielőtt egy kollégának (az ágensnek) odaadod szerkeszteni, lemásolod egy másik mappába. Ő a **másolatban** firkálhat, az eredeti nem sérül. Ha végzett, lefuttatod az ellenőrzéseket a másolaton, és ha minden rendben, átveszed a változtatásait. A „worktree" a másolat git-es neve: ugyanannak a repónak egy második munkamappája, saját branch-csel, közös `.git`-tel.

```
Egy git repó (közös .git)
├── Fő checkout   ~/dev/github.com/cloudmentor/har-basic     branch: init
│     └── .har/   contract + runs/ + validations/             a bizonyíték itt van
└── Worktree      ~/worktrees/init-c706-har-agent-1-8a2b      branch: init-c706-har-agent-1-8a2b
      └── ide szerkeszt az ágens, itt fut a verify, itt aktív a commit gate
```

| | Fő checkout | Worktree (slot) |
| --- | --- | --- |
| Szerep | az eredeti, te (az ember) itt dolgozol | a másolat, az ágens itt dolgozik |
| Branch | `init` | `init-<sha4>-har-agent-<slot>-<rand4>` |
| Commit gate | **nem véd** | **véd** (`scope: worktrees`) |
| Bizonyíték (`runs/`, `validations/`) | itt tárolódik | innen keletkezik |

Megfigyelésünk a har-basic-ben: a fő checkouton a `c2293bd` commit verify nélkül is átment, mert ott nincs gate. A verify közben a worktree-t ellenőrizte (a `treeHash` nem változott, a `changedFiles` üres). **A commit gate kipróbálásához a worktree-ben kell commitolni.**

Mindig ellenőrizd, hol állsz:

```bash
pwd
git branch --show-current
```

Ha a branch `init`, a fő checkouton vagy. Ha `init-c706-har-agent-1-8a2b`, a worktree-ben.

Egy gyors kísérlet az izoláció megfigyelésére (veszélytelen):

```bash
cd ~/worktrees/init-c706-har-agent-1-8a2b
touch proba.txt
ls ~/dev/github.com/cloudmentor/har-basic
rm ~/worktrees/init-c706-har-agent-1-8a2b/proba.txt
```

A `proba.txt` nem jelenik meg az eredeti mappában.

### A branch és a worktree neve

A név szándékosan szabályos, és a HAR erre épít:

`<alap branch>-<commit eleje>-har-agent-<slot>-<véletlen 4 karakter>`

| Rész | Jelentése |
| --- | --- |
| `init` | melyik branchből indult |
| `c706` | melyik commitból (a `c706a47` eleje) |
| `har-agent-1` | az 1-es slot |
| `8a2b` | véletlen rész, hogy két launch neve ne ütközzön |

A HAR a `-har-agent-<slot>-` mintával találja meg a worktree-ket (status, cleanup, Mission Control). Ezért **nem érdemes átnevezni**. A forráskódban nem találtam kapcsolót a név megadására (a main branch kódja alapján; a `har env launch --help` mutatja a telepített verzió kapcsolóit).

Praktikus tippek:

- **Ne gépeld be a nevet.** A glob kiegészíti: `cd ~/worktrees/*-har-agent-1-*` (ha csak egy ilyen van). Gyakori használatra alias a `~/.zshrc`-be: `alias w1='cd ~/worktrees/*-har-agent-1-*'`.
- **Olvasható név a feladatnak:** `har env launch 1 --work-id "greet-tesztek"` (a CLI leírása szerint repo-szintű work unit azonosító, a `status` és a Mission Control mutatja). *Kipróbálandó.*
- **Az útvonal:** a `har env status` kiírja a work dirt.

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

### Egy változás útja az eredeti kódba (PR-flow)

Az 1–4. lépés a worktree-ben (az ágens területén) történik, az 5–7. az átvétel, ezt az ember végzi.

1. `har env launch 1`
   Új, izolált worktree és branch az `init` aktuális állapotából. A kiírt WORK DIR-ben dolgozz, a fő mappában ne.
2. `cd <WORK DIR>` majd `pwd` és `git branch --show-current`
   Ellenőrizd, hogy a worktree-ben vagy-e (a branch neve `init-<sha4>-har-agent-1-<rand>`). A fő mappában (`init`) nincs commit gate.
3. Szerkesztés, közben `har env verify 1`
   Gyors visszajelzés a quick szintű stage-ekkel.
4. `har env verify 1 --full`, majd `git add -A` és `git commit`
   A teljes ellenőrzés bizonyítékot rögzít a kód pontos állapotáról (tree hash), a commit gate csak ezzel enged commitolni. Mindent stage-elj, ami verify-olva lett.
5. Push és PR a szerkesztőben (Publish Branch, Create Pull Request)
   A PR base-e az `init`, nem a `main`.
6. `har env complete 1`
   Lezárja a slotot, és újrahasznosítja a meglévő bizonyítékot, ha a kód nem változott (különben `--verify` kell). A branch megmarad. A worktree-t előtte zárd be az editorból.
7. Merge a GitHubon, majd Pull a fő mappában
   A PR beolvasztása viszi vissza a változást az eredeti kódba. Utána a slot branch törölhető.

Jó tudni:

- A commit gate git hookokon alapul: `har hooks status` mutatja, telepítve vannak-e (`har hooks install` teszi fel).
- A bizonyíték (`.har/validations/`) helyi, a PR nem hordozza. A CI-nak ugyanazokat a parancsokat kell futtatnia, ami a `stages.json`-ban van.
- A har-basic-ben ellenőriztük: a commit fájának hash-e megegyezett a verify `treeHash`-ével.

---

## 5. Tapasztalatok és hibakeresés (har-basic)

| Tünet                                                  | Ok                                                                                                  | Megoldás                                                                   |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `verify` bukik, `ENOENT package.json`                  | Nincs `package.json`, így nincs mit futtatni                                                        | Minimális Node-projekt: `typecheck`, `test`, `lint` scriptek               |
| A worktree-ben nincsenek az új fájlok                  | A worktree a commitból jön, nem a munkakönyvtárból                                                  | Először commit, utána `launch`                                             |
| A launch a repo rootot használja (_worktree disabled_) | Repo-szintű beállítás (`Worktree: off`) felülírja a `harness.env`-et                                | `har worktree on`, teardown, új launch                                     |
| zsh: `no matches found` / `#` hibák                    | Az interaktív zsh nem kezeli a `#` megjegyzést (`setopt interactive_comments`)                      | Megjegyzés nélkül másold a parancsot                                       |
| `.har/validations/` hiányzik                           | Takarítás után a mappa újra létrejön az első verify-nál                                             | Futtass `verify`-t                                                         |
| Mission Control: _Worktree path is missing on disk_    | A dashboard a saját nézőpontjából ellenőrzi az útvonalat (Dockerben nem látja a host fájlrendszert) | `har env status` az igazság forrása. _(Forráskód alapján, ellenőrizendő.)_ |
| A teardown után megmaradnak a naplók                   | Az állapot (slot, worktree) és a bizonyíték (`runs/`, `validations/`) külön él, szándékosan         | `har control reset --dry-run`, vagy `rm -rf .har/runs .har/validations`    |
| A commit verify nélkül is átment | A fő checkouton commitoltál, ott nincs gate (`scope: worktrees`) | A commitot a worktree-ben végezd, `pwd` és `git branch --show-current` ellenőrzéssel |

### Általános tanulságok

- A beállítások rétegesek: commitolt contract (`harness.env`) és gépszintű, repóhoz kötött override. Hibakereséskor a `har env status` mutatja a ténylegesen érvényes értéket.
- A harness **nem a modellt javítja**, hanem a folyamatot: izolál, ellenőriz, bizonyítékot ad.

---

## 6. Parancs-cheatsheet

```bash
har onboard                  # .har/ scaffold, prompt az ágensnek
har worktree on              # worktree mód bekapcsolása a repóhoz
har env launch 1             # slot indítása (worktree + branch + portok)
har env status               # slotok és az érvényes beállítások (work dir is)
har env verify 1             # quick szint
har env verify 1 --full      # teljes pipeline, bizonyíték rögzítése
har env teardown 1           # slot lezárása (a branch megmarad)
har env complete 1           # slot lezárása feladat végén
har env maintain             # harness frissítés, drift-ellenőrzés
har env cleanup              # elavult session worktree-k takarítása
har control sync             # slot- és futásállapot küldése a Mission Controlnak
pwd && git branch --show-current   # hol állok: fő checkout vagy worktree?
cd ~/worktrees/*-har-agent-1-*     # belépés az 1-es slot worktree-ébe
har control reset --dry-run  # Mission Control adat és helyi előzmények törlése (előbb dry-run!)
```

---

## 7. Nyitott kérdések és bővítendő anyagok

- [ ] Hogyan viselkedik a commit gate bukó teszt esetén a worktree-ben? (3. lecke)
- [ ] Saját stage írása (pl. `shellcheck`, `terraform validate`) és a `readiness` smoke (4. lecke)
- [ ] Hogyan illeszthető a HAR az éjszakai ágens-VM-hez? (5. lecke)
- [ ] Mit **nem** bizonyít a verify? (6. lecke)
- [ ] A `--work-id` kapcsoló kipróbálása a launchnál (olvasható név a feladatnak)

## Források

- HAR repó: https://github.com/os-factory/har
- Dokumentáció: https://harproject.dev/
