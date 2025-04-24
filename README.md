# Mapswipe Backend
[![codecov](https://codecov.io/gh/mapswipe/mapswipe-backend/graph/badge.svg?token=5ZAYZ89DWF)](https://codecov.io/gh/mapswipe/mapswipe-backend)

## Local development

### Setup

**Clone repository**
```bash
git clone git@github.com:mapswipe/mapswipe-backend.git mapswipe-backend
cd mapswipe-backend
```

**Create a `.env` file**
> [!IMPORTANT]
> NOTE: Overwrite/set variables using .env
>
> Available options are defined in ./docker-compose.yaml:10 (environment) and ./main/settings.py:16 (env = environ.Env)

**Pull and build images**
```bash
docker compose pull
docker compose build
```

### Run

**Run Essentials**
```bash
docker compose up
```

**Run Web & Workers**
```bash
docker compose up web worker worker-beat
```

### Django migration commands

```bash
# Create new migrations if required
docker compose exec web ./manage.py makemigrations

# Show migrations status
docker compose exec web ./manage.py showmigrations

# Run latest migrations
docker compose exec web ./manage.py migrate
```

### User management commands

```bash
# Create new user
docker compose exec web ./manage.py createsuperuser

# Change existing user's password
docker compose exec web ./manage.py changepassword mapswipe-user-1
```

> https://docs.djangoproject.com/en/latest/ref/django-admin/#createsuperuser
>
> https://docs.djangoproject.com/en/5.1/ref/django-admin/#changepassword

### Generate latest GraphQl schema

```bash
docker compose run --rm web ./manage.py export_schema main.graphql.schema --path schema.graphql
# OR
docker compose exec web ./manage.py export_schema main.graphql.schema --path schema.graphql
```

### Run tests

```bash
docker compose run --rm web pytest
# OR
docker compose exec web pytest
```

## Tips
You can use django `run` command if there are no running instance for temporary commands

```bash
# If you want to generate latest GraphQl schema
# You can replace this command
docker compose exec web ./manage.py graphql_schema --out schema.graphql
# with this (Which will create a temporary container, run the command, and clean of the container)
docker compose run --rm web ./manage.py graphql_schema --out schema.graphql
```
