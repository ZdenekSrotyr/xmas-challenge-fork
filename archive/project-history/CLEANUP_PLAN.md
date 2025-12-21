# Plán Úklidu a Dokončení Systému

**Datum:** 2025-12-16
**Status:** READY TO EXECUTE

---

## 🎯 Cíle

1. Uzavřít vyřešené issues
2. Zkontrolovat a opravit generátory
3. Vyčistit repozitář od obsolete souborů
4. Opravit learning dashboard
5. Přidat web link do README
6. Reverse engineer pluginy zpět do docs
7. Otestovat celý systém

---

## ✅ ÚKOL 1: Zavřít Vyřešené Issues

### Issues k zavření:
- **#25**: TS-001 HTTP Method Error → ✅ Vyřešeno PR #45
- **#26**: TS-002 Incremental Loads → ✅ Vyřešeno PR #50

### Akce:
```bash
gh issue close 25 --comment "✅ Vyřešeno v PR #45. Dokumentace opravena - Storage API export nyní správně používá POST metodu."
gh issue close 26 --comment "✅ Vyřešeno v PR #50. Přidána dokumentace pro incremental writes a primary keys."
```

---

## 🔍 ÚKOL 2: Zkontrolovat Gemini Generátor

### Zjištění:
- ✅ `gemini_generator.py` existuje
- ✅ Je volán z workflow
- ✅ PRka obsahují změny v `gemini/keboola-core/skill.yaml`

### Problém:
Zkontrolovat, jestli generátor OPRAVDU generuje, nebo jen kopíruje/nechává prázdné.

### Akce:
1. Spustit generátor manuálně
2. Ověřit, že output odpovídá vstupním docs
3. Pokud ne, opravit generátor

```bash
python automation/scripts/generators/gemini_generator.py \
  --input docs/keboola/ \
  --output gemini/keboola-core/skill.yaml

# Zkontrolovat diff
git diff gemini/keboola-core/skill.yaml
```

---

## 🧹 ÚKOL 3: Vyčistit Repozitář

### Kandidáti na smazání:

#### A) Obsolete test files a reporty
```
test-results/TS-*.md           # Ponechat jako dokumentaci? Nebo archivovat?
POC-README.md                  # Je to ještě relevantní?
IMPLEMENTATION_SUMMARY.md      # Obsolete?
TEST_REPORT_*.md               # Obsolete?
```

#### B) Duplicitní nebo nepoužívané workflows
```
.github/workflows/validate-examples.yml  # Funguje? Používá se?
.github/workflows/auto-triage.yml        # Testováno?
```

#### C) Stará struktura
```
plugins/                       # Je označené jako obsolete v README
```

### Rozhodnutí:
1. **PONECHAT**:
   - `test-results/` - dokumentace testů
   - Všechny workflows (jsou používané)

2. **SMAZAT**:
   - `POC-README.md` → Přesunout info do main README
   - `IMPLEMENTATION_SUMMARY.md` → Obsolete
   - `TEST_REPORT_*.md` → Obsolete (info je v test-results/)
   - `plugins/` → Obsolete (pokud je info migrované)

3. **PŘESUNOUT**:
   - Test reporty do `docs/testing/` jako archiv

### Akce:
```bash
# Archivovat test reporty
mkdir -p docs/testing/archive
mv TEST_REPORT_*.md docs/testing/archive/ 2>/dev/null || true
mv IMPLEMENTATION_SUMMARY.md docs/testing/archive/ 2>/dev/null || true

# Smazat obsolete
rm -f POC-README.md

# Plugins - rozhodnout po reverse engineering
```

---

## 🐛 ÚKOL 4: Opravit Learning Dashboard

### Problém:
- Data JSOU v `automation/web/data/learnings.json` (2 learnings)
- Dashboard zobrazuje "No learnings found"

### Možné příčiny:
1. Bug v `automation/web/js/learning.js`
2. Nesprávná cesta k JSON
3. CORS issues při local development
4. GitHub Pages nedostává aktualizovaný JSON

### Akce:
1. Zkontrolovat `learning.js` - správně načítá data?
2. Zkontrolovat `deploy-ui.yml` - exportuje learnings?
3. Ověřit na live webu, že JSON je dostupný
4. Opravit bug v JS

```bash
# Zkontrolovat, jestli je export_learnings.py volán
grep -r "export_learnings" .github/workflows/
```

---

## 📝 ÚKOL 5: Přidat Web Link do README

### Současný stav:
README nemá link na web nahoře.

### Požadovaný stav:
```markdown
# Keboola Xmas Challenge - Self-Learning AI Knowledge System

> 🌐 **Live Dashboard**: https://zdeneksrotyr.github.io/xmas-challenge-fork/

A self-healing knowledge system for Claude Code that learns from its mistakes...
```

### Akce:
Přidat badge/link na začátek README hned po nadpisu.

---

## 🔄 ÚKOL 6: Reverse Engineer Pluginy → Docs

### Kontext:
Máme existující pluginy v `claude/component-developer/`, `claude/dataapp-developer/`, které obsahují znalosti, ale nejsou v `docs/`.

### Cíl:
Vytvořit source docs z těchto pluginů, aby byly součástí single source of truth.

### Strategie:

#### Existující pluginy:
```
claude/component-developer/
  ├── SKILL.md
  └── guides/
      └── component-builder/
          ├── running-and-testing.md
          ├── datadir-structure.md
          └── ...

claude/dataapp-developer/
  └── SKILL.md
```

#### Cílová struktura docs:
```
docs/keboola/
  ├── 01-core-concepts.md          # Existuje
  ├── 02-storage-api.md             # Existuje
  ├── 03-common-pitfalls.md         # Existuje
  ├── 04-component-development.md   # NOVÝ - z component-developer
  ├── 05-dataapp-development.md     # NOVÝ - z dataapp-developer
```

### Akce:
1. **Extrahovat znalosti z component-developer**:
   - Přečíst `claude/component-developer/SKILL.md`
   - Vytvořit `docs/keboola/04-component-development.md`
   - Zahrnout: datadir structure, configuration patterns, testing

2. **Extrahovat znalosti z dataapp-developer**:
   - Přečíst `claude/dataapp-developer/SKILL.md`
   - Vytvořit `docs/keboola/05-dataapp-development.md`

3. **Regenerovat claude/ a gemini/**:
   ```bash
   python automation/scripts/generators/claude_generator.py --input docs/keboola/ --output claude/keboola-core/SKILL.md
   python automation/scripts/generators/gemini_generator.py --input docs/keboola/ --output gemini/keboola-core/skill.yaml
   ```

4. **Rozhodnout o component-developer a dataapp-developer**:
   - Ponechat jako samostatné pluginy? (jsou to specializované nástroje)
   - Nebo integrovat do keboola-core?

**Doporučení**: Ponechat jako samostatné pluginy, protože:
- component-developer má vlastní commands (/review, /fix)
- dataapp-developer je specifický workflow
- keboola-core je knowledge base, tyto jsou tools

---

## 🧪 ÚKOL 7: Otestovat Celý Systém End-to-End

### Test Scénář:

#### 1. Test Issue Creation
```bash
# Vytvořit testovací issue manuálně
gh issue create --title "[Test] Missing Stack URL documentation" \
  --body "Stack URL není vysvětleno v docs" \
  --label "auto-report,needs-triage"
```

#### 2. Test Auto-Triage
- Zkontrolovat, že auto-triage workflow proběhl
- Ověřit, že issue dostalo správnou kategorii

#### 3. Test Propose-Fix
```bash
# Spustit propose-fix pro test issue
gh workflow run propose-fix.yml \
  --field issue_number=<TEST_ISSUE> \
  --field category=outdated-docs
```

#### 4. Test Generování PRka
- Zkontrolovat, že PR:
  - Upravuje `docs/keboola/*.md`
  - Regeneruje `claude/keboola-core/SKILL.md`
  - Regeneruje `gemini/keboola-core/skill.yaml`
  - Má správný "docs:" prefix

#### 5. Test Merge
- Mergnut PR
- Ověřit, že:
  - Graph DB se aktualizoval
  - UI se zregeneroval
  - Learnings se zachytily

#### 6. Test Learning Dashboard
- Otevřít https://zdeneksrotyr.github.io/xmas-challenge-fork/
- Zkontrolovat, že:
  - Learnings jsou vidět
  - Graf je aktuální
  - Timeline zobrazuje změny

---

## 📋 EXECUTION ORDER

### Fáze 1: Cleanup (30 min)
1. Zavřít issues #25, #26
2. Archivovat obsolete soubory
3. Přidat web link do README
4. Commit: "chore: Clean up obsolete files and update README"

### Fáze 2: Fix Learning Dashboard (45 min)
1. Debugovat learning.js
2. Opravit bug
3. Zkontrolovat export workflow
4. Deploy na GitHub Pages
5. Commit: "fix: Learning dashboard not displaying data"

### Fáze 3: Reverse Engineer Plugins (60 min)
1. Vytvořit `docs/keboola/04-component-development.md`
2. Vytvořit `docs/keboola/05-dataapp-development.md`
3. Regenerovat claude/gemini
4. Commit: "docs: Add component and dataapp development documentation"

### Fáze 4: Test Everything (45 min)
1. Vytvořit test issue
2. Spustit celý workflow
3. Ověřit všechny kroky
4. Dokumentovat výsledky

### Fáze 5: Final Polish (30 min)
1. Update README s finálními linky
2. Zkontrolovat všechny workflows
3. Final commit: "chore: Complete system cleanup and testing"

---

## ⚠️ DEPENDENCIES

- **ANTHROPIC_API_KEY** musí být v secrets
- **GITHUB_TOKEN** permissions musí být správné
- Branch protection není nutná (auto-merge nefunguje bez ní, ale manual merge OK)

---

## 🎯 SUCCESS CRITERIA

✅ Issues #25, #26 jsou zavřené
✅ Repozitář je čistý (žádné obsolete soubory)
✅ Learning dashboard funguje
✅ Web link je v README nahoře
✅ Component a DataApp docs jsou v docs/
✅ End-to-end test proběhl úspěšně
✅ Vše je zdokumentované

---

## 🚀 EXECUTION

Použít agenty:
- **Agent 1**: Cleanup + README update
- **Agent 2**: Fix learning dashboard
- **Agent 3**: Reverse engineer plugins
- **Agent 4**: End-to-end testing

Paralelně kde možné, sekvenčně kde nutné.
