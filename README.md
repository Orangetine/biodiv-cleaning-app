1. Cloner le repo
```
git clone git@github.com:Orangetine/biodiv-cleaning-app.git biodiv_cleaning_app
```
2. Installer poetry
```
curl -sSL https://install.python-poetry.org | python3 -
```

3. A la fin du votre .bashrc ajouter poetry à votre path
```
cd   # home
sudo nano .bashrc
```

```
# poetry
export PATH="$HOME/.local/bin:$PATH"
```

```
cd   # home
source .bashrc
```

```
cd /var/www/biodiv_cleaning_app # racine du projet
```

4. Verifier l'install
```
poetry --version
```
5. Autoriser la création d'un environnement virtuel
```
poetry config virtualenvs.in-project true
```
6. Installer l'environnement virtuel
```
poetry install
```
7. Installer l'application
```
./install_app.sh
```