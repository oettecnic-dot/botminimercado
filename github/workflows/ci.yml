name: CI Bot Minimercado

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Copiar código del repositorio
      uses: actions/checkout@v4

    - name: Configurar Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Instalar dependencias
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Ejecutar pruebas unitarias
      run: |
        python test_bot.py
