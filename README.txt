Pour initialiser la base de données à partir du termimal, suivre les étapes suivantes :
    ./venv/Scripts/activate
    set FLASK_APP=app.py
    $env:FLASK_APP = "app.py"
    flask initialisation_bd

    SET FLASK_DEBUG=True "&" SET FLASK_APP=app.py "&" SET REDIS_URL=redis://localhost "&" SET DB_HOST=localhost "&" SET DB_USER=pUser "&" SET DB_PASSWORD=!2345 "&" SET DB_PORT=5432 "&" SET DB_NAME=api8inf349
    flask initialisation_bd
Ensuite pour lancer l'application, entrer la commande suivante :
    flask run
