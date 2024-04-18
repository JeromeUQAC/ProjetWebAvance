Pour initialiser la base de données à partir du termimal, suivre les étapes suivantes :
    ./venv/Scripts/activate
    set FLASK_APP=app.py
    $env:FLASK_APP = "app.py"


Pour l'initialisation Docker :
    docker compose up -d
    docker build -t api8inf349 .
    docker run -p 5000:5000 --name mon_api api8inf349
    flask initialisation_bd (dans Docker)
