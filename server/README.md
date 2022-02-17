# MedPerf API Server 

Code is tested on latest python 3.9

## Install all dependencies

    pip install -r requirements.txt

## Create .env file with your environment settings

Sample .env.example is added to root. Rename `.env.example` to `.env` and modify with your env vars.

    cp .env.example .env

## Create tables and existing models

    python manage.py migrate

## Start the server

    python manage.py runserver
    
  
API Server is running at `http://127.0.0.1:8000/` by default. You can view and experiment Medperf API at `http://127.0.0.1:8000/swagger`
 

## Test MedPerf API
    
You can run  server script to verify a sample work. See [script](https://github.com/mlcommons/medperf/blob/main/server/seed.py) 
 
    pip install -r test-requirements.txt
    python seed.py
