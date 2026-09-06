# NoiseDoseLab

Outil local d'analyse déterministe de l'exposition sonore professionnelle.

Cette application comporte deux services à laisser ouverts pendant l'utilisation :

- le backend Python, qui réalise l'analyse ;
- le frontend Next.js, accessible dans le navigateur.

## Préparation PowerShell habituelle

Ouvre `pwsh`, puis, si tu utilises ta configuration ARCHCode habituelle, exécute :

```powershell
& "C:\Users\Utilisateur\Documents\mARCHCode\.venv\Scripts\Activate.ps1"
Remove-Item Env:\ARCHCODE_LLM_MODEL -ErrorAction SilentlyContinue
$env:ARCHCODE_LLM_BACKEND = "stub"
Set-Alias pyv "C:\Users\Utilisateur\Documents\mARCHCode\.venv\Scripts\python.exe"
```

Cette préparation est personnelle à ton environnement ARCHCode. NoiseDoseLab utilise ensuite son propre environnement Python dans `backend\.venv`.

## Installation initiale

Depuis PowerShell :

```powershell
Set-Location "C:\Users\Utilisateur\Documents\Vercel-NoiseDoseLab"

py -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -e ".\backend[test]"

Set-Location frontend
npx --yes pnpm@10.17.1 install --frozen-lockfile

Set-Location ..
```

`npx` est utilisé afin de ne pas dépendre d'une installation globale de pnpm ou de Corepack.

## Lancer l'application

Ouvre deux fenêtres PowerShell et laisse-les ouvertes pendant l'utilisation.

### Terminal 1 — backend

```powershell
Set-Location "C:\Users\Utilisateur\Documents\Vercel-NoiseDoseLab"
& ".\backend\.venv\Scripts\Activate.ps1"
python -m uvicorn backend.main:app --reload --port 8000
```

### Terminal 2 — frontend

```powershell
Set-Location "C:\Users\Utilisateur\Documents\Vercel-NoiseDoseLab\frontend"
npx --yes pnpm@10.17.1 dev
```

Ouvre ensuite l'adresse affichée par le terminal frontend :

- habituellement `http://localhost:3000` ;
- `http://localhost:3001` si le port 3000 est déjà utilisé.

Pour arrêter un serveur, utilise `Ctrl + C` dans son terminal.

## Vérifier l'installation

Depuis la racine du dépôt :

```powershell
py -m unittest discover -s tests -v
py qa\triage_noisedoselab.py
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -v

Set-Location frontend
npx --yes pnpm@10.17.1 test
npx --yes pnpm@10.17.1 build
```

Les contrôles couvrent le moteur d'analyse, le comportement scientifique, l'API et l'interface.

## Limites

NoiseDoseLab est un outil de dépistage déterministe. Il ne constitue pas une évaluation réglementaire définitive de l'exposition sonore.
