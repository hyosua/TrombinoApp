# trombiMaker - Assistant de Création de Trombinoscopes 

Une application de bureau simple pour créer rapidement des trombinoscopes (organigrammes de visages) à partir d'une liste Excel et d'un dossier de photos.

Ce projet a été conçu pour résoudre un problème courant : associer une liste de noms (ex: étudiants, employés) à un lot de photos dont les noms de fichiers ne correspondent pas (ex: `IMG_1024.jpg`). L'application guide l'utilisateur à travers un processus simple en 5 étapes, de l'importation à l'exportation en document Word.

Vous pouvez telecharger une version executable (.exe) dans l'onglet Release pour tester l'application.
---

##  Fonctionnalités Clés

* **Gestion de Projet :** Créez et nommez différents trombinoscopes (par classe, année, etc.).
* **Import Excel :** Importation facile de listes d'étudiants (`.xlsx`).
* **Import Photos :** Importation par lot de photos (JPG, PNG, BMP...).
* **Traitement Automatique :** Redimensionnement (ex: < 200Ko) et **rognage (crop) carré** automatiques et invisibles pour des vignettes uniformes.
* **Workflow Intuitif :** Interface "Wizard" (assistant) qui guide l'utilisateur étape par étape.
* **Association "Drag & Drop" :** L'étape critique consiste à glisser un nom depuis la liste et à le déposer sur la photo correspondante.
* **Export Word :** Exportation du trombinoscope finalisé au format `.docx` avec plusieurs options de mise en page (3x4, 4x5...).

---

##  Pile Technique (Stack)

* **Langage :** Python 3.8+
* **Interface Graphique :** PySide6 (liaisons officielles de Qt pour Python)
* **Gestion des Paquets :** `uv` (par Astral)
* **Traitement d'Image :** `Pillow` (PIL)
* **Lecture Excel :** `openpyxl`
* **Écriture Word :** `python-docx`
* **Compilation :** `Nuitka`

---

## Workflow de l'Application

L'application est conçue comme un assistant linéaire pour minimiser les clics :

1.  **Démarrer :** L'utilisateur lance l'application et choisit "Créer un Nouveau Trombinoscope".
2.  **Importer la Liste :** L'utilisateur importe le fichier Excel. Un aperçu de la liste s'affiche.
3.  **Importer les Photos :** L'utilisateur glisse et dépose toutes les photos dans la zone dédiée. Le traitement (redimensionnement, rognage) se fait en arrière-plan.
4.  **Associer (Étape Critique) :** L'utilisateur voit la liste de noms d'un côté et la grille de photos de l'autre. Il glisse chaque nom sur la bonne photo.
5.  **Exporter :** L'utilisateur choisit la mise en page (ex: 3x4) et clique sur "Exporter" pour générer le fichier `.docx`.

---

##  Installation (Pour les Développeurs)

Instructions pour configurer l'environnement de développement à partir de zéro en utilisant `uv`.

1.  **Cloner le dépôt**
    ```bash
    git clone https://github.com/hyosua/TrombinoApp.git
    cd trombiMaker
    ```

2.  **Installer `uv`** (s'il n'est pas déjà présent)
    ```bash
    # Windows (PowerShell)
    irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex
    # macOS/Linux
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    ```

3.  **Créer l'environnement virtuel**
    ```bash
    uv venv
    ```

4.  **Activer l'environnement**
    ```bash
    # Windows
    .\.venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

5.  **Installer les dépendances** (vous pouvez aussi ajouter `qdarkstyle` pour le thème sombre)
    ```bash
    uv pip install PySide6 openpyxl Pillow python-docx
    ```

6.  **Lancer l'application**
    ```bash
    python main.py
    ```

---

##  Compilation en Exécutable (`.exe`)

Ce projet est configuré pour être compilé avec **Nuitka** en un seul fichier exécutable.

1.  **Installer Nuitka** (et `zstandard` pour une meilleure compression)
    ```bash
    uv pip install nuitka zstandard
    ```

2.  **Installer un Compilateur C++**
    Nuitka compile le Python en C, vous avez donc besoin d'un compilateur.

    * **Option A (Droits Admin) :** Installez les [Visual Studio Build Tools](https://visualstudio.microsoft.com/fr/downloads/) (choisir la charge de travail "Développement Desktop en C++").
    * **Option B (Sans Droits Admin) :** Téléchargez et extrayez [WinLibs GCC](https://github.com/brechtsanders/winlibs_mingw/releases) (version `posix-seh`) dans un dossier simple (ex: `C:\MonCompilateur`).

3.  **Configurer le Terminal (Option B uniquement)**
    Si vous utilisez l'Option B, vous devez indiquer à votre terminal où se trouve le compilateur (à faire **à chaque ouverture** du terminal) :
    ```powershell
    # PowerShell
    $env:PATH = "C:\MonCompilateur\mingw64\bin;" + $env:PATH
    ```

4.  **Lancer la Compilation**
    Exécutez cette commande depuis la racine de votre projet :
    ```bash
    nuitka --onefile --windows-disable-console --enable-plugin=pyside6 --output-dir=dist main.py
    ```
    Pour créer un fichier executable sur linux lancer:
    ```bash
    nuitka --onefile --disable-console --enable-plugin=pyside6 --output-dir=dist main.py
    ```

Votre exécutable final (`main.exe`) se trouvera dans le dossier `dist`.
