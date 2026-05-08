# Plant Health Checker

## a) Título, descripción y equipo

**Producto:** *Plant Health Checker* — backend que clasifica imágenes de hojas
como `healthy` / `not_healthy` y guarda el historial por usuario autenticado.

**Problema:** detección manual de enfermedades en cultivos es lenta y depende
del criterio de un experto. **Solución:** un servicio HTTP que recibe una
foto, devuelve la etiqueta y la confianza, y persiste el historial por
usuario para seguimiento.

**Equipo y roles:**

| Integrante | Rol | Propiedad principal |
| --- | --- | --- |
| David Herencia | ML Engineer | `services/training/`, `services/classifier/app/inference.py` |
| Lucas Carranza | Backend Engineer | `services/auth/`, HTTP del `services/classifier/` |
| Marcelo Chincha | DevOps Engineer | Dockerfiles, `docker-compose`, CI, scripts, k8s |

---

## b) Justificación del tema

- **Contexto:** La detección de enfermedades en plantas es una aplicación muy útil de ML en agricultura, y permite a los agricultores identificar problemas en sus cultivos de manera temprana, sin necesidad de acuidir a un experto. Sin embargo, realizar esta tarea con modelos de deep learning entrenados en GPU puede ser costoso y complejo. En cambio, los descriptores hand-crafted como HOG o SIFT siguen siendo efectivos para tareas binarias con datasets pequeños, y son más fáciles de implementar y mantener en un entorno de backend estándar.
- **Motivación:** combinar el pipeline clásico de CV con un stack de backend
  estándar (FastAPI + Postgres) permite practicar **microservicios**, **JWT**,
  **persistencia** y **CI/CD** en un mismo proyecto, sin depender de un
  modelo deep learning entrenado en GPU.
- **Relevancia:** los descriptores hand-crafted siguen siendo competitivos
  en tareas binarias con datasets pequeños y son auditables — útil cuando un
  cliente exige trazabilidad de la decisión.

---

## Arquitectura y estructura del proyecto

```mermaid
flowchart LR
    Client["Cliente HTTP"]

    subgraph Public["Red public"]
      Auth["auth-service<br/>FastAPI :8001"]
      Classifier["classifier-service<br/>FastAPI :8002"]
    end

    subgraph Private["Red private"]
      DB[("Postgres 16<br/>users · predictions")]
      Training["training (job)<br/>train.py / evaluate.py"]
    end

    Artifacts[/"artifacts/<br/>model.joblib<br/>pipeline_config.json"/]

    SharedLib[["Shared CV libs<br/>pipeline · features<br/>processing · dataset"]]

    Client -- "register / login" --> Auth
    Client -- "Bearer JWT + imagen" --> Classifier
    Auth --> DB
    Classifier --> DB
    Training -- "produce" --> Artifacts
    Classifier -- "carga al startup" --> Artifacts
    Training -.->|usa| SharedLib
    Classifier -.->|usa| SharedLib

    CI["GitHub Actions<br/>pytest + docker build"] -. "valida cada push" .-> Public
```

**Decisión clave:** ambos servicios validan el JWT localmente con el mismo
`JWT_SECRET`. No hay llamada `classifier → auth` para validar tokens; eso
elimina el cuello de botella y mantiene los servicios independientes.

---

## c) Git con Conventional Commits

### ¿Qué son y por qué se usan?

Convención de mensajes con la forma `<tipo>(<scope>): <resumen>`. Habilita
**changelogs automáticos**, **bumps de versión semántica** y filtrado de
historial por tipo. Permite que los commits sean datos consultabes, y una fuente de verdad sobre la evolución del proyecto.

### Tipos usados en este repo

| Tipo | Cuándo |
| --- | --- |
| `feat` | Funcionalidad nueva visible al usuario o consumida por otro servicio. |
| `fix` | Corrección de un bug en código ya mergeado. |
| `test` | Tests nuevos o ajustes a tests existentes, sin cambiar código de producción. |
| `chore` | Andamiaje, configuración, limpieza — no toca lógica del producto. |
| `docs` | README, INFORME, comentarios extensos. |
| `ci` | Workflows, pipelines, automatización. |
| `refactor` | Reescritura sin cambio de comportamiento. |

### Historial

- **Branching:** GitFlow — `feature/*` → PR → `develop`, y al final
  `develop` → `main`.

#### Muestra de 6 commits analizados

| # | Hash | Mensaje | Análisis |
| - | --- | --- | --- |
| 1 | `19b584b` | `chore(repo): bootstrap monorepo structure (services, infra, scripts, env)` | Andamiaje inicial: layout de `services/`, `infra/`, `.env.example`. Tipo `chore` correcto: no introduce lógica del producto. |
| 2 | `2f9924c` | `feat(training): add train.py with descriptor pipeline serialization` | Nueva funcionalidad de ML: produce los artefactos que consume el classifier. `feat` con scope `training` — el scope identifica el componente afectado. |
| 3 | `89ad149` | `test(ml): add unit tests for train, evaluate and inference` | Tests sintéticos sin red ni dataset real. Tipo `test` separado de `feat` para que el changelog distinga código nuevo de cobertura nueva. |
| 4 | `5a38449` | `feat(auth): add register, login, me endpoints with JWT and tests` | Implementa los 3 endpoints de auth + JWT firmado. Cumple el contrato compartido entre servicios (`sub = str(user.id)`). |
| 5 | `cf4334c` | `feat(docker): add Dockerfile per service and docker-compose orchestration` | Dockeriza los 3 servicios + Postgres. Scope `docker` aclara que el cambio es de infraestructura aunque sea `feat`. |
| 6 | `7fd3936` | `ci(github): add GitHub Actions workflow and Kubernetes manifest skeletons` | Agrega `.github/workflows/ci.yml` + manifests de k8s. `ci` separa este tipo de cambios de `feat`/`chore`. |

> *[Captura — Historial de commits (`git log --oneline`)]*
>
> ![git-log](docs/img/git-log.png)

### Pull Requests

12 PRs abiertos contra `develop` y mergeados antes del freeze:

| # | Branch | Tipo |
| - | --- | --- |
| 1 | `feature/training-train-script` | feat |
| 2 | `feature/training-evaluate` | feat |
| 3 | `feature/classifier-inference` | feat |
| 4 | `feature/ml-tests` | test |
| 5 | `feature/auth-models` | feat |
| 6 | `feature/auth-endpoints` | feat |
| 7 | `feature/classifier-predict` | feat |
| 8 | `feature/classifier-history` | feat |
| 9 | `feature/repo-bootstrap` | chore |
| 10 | `feature/automation-scripts` | ci |
| 11 | `feature/docker-compose` | feat |
| 12 | `feature/ci-and-k8s` | ci |

> *[Captura — Listado de PRs en GitHub]*
>
> ![pull-requests](docs/img/pull-requests.png)

---

## d) Pruebas unitarias

### Herramientas

`pytest` (suite, fixtures, parametrización), `fastapi.testclient.TestClient`
(integration HTTP), `unittest.mock.MagicMock` (stub del modelo).

### Cobertura

| Suite | Archivo | Tests |
| --- | --- | --- |
| Training | `services/training/tests/test_train.py` | 2 |
| Training | `services/training/tests/test_evaluate.py` | 1 |
| Classifier (inference) | `services/classifier/tests/test_inference.py` | 3 |
| Classifier (predict) | `services/classifier/tests/test_predict.py` | 4 |
| Classifier (history) | `services/classifier/tests/test_history.py` | 4 |
| Classifier (e2e) | `services/classifier/tests/test_e2e.py` | 1 |
| Auth (security) | `services/auth/tests/test_security.py` | 3 |
| Auth (endpoints) | `services/auth/tests/test_auth_endpoints.py` | 7 |
| **Total servicios** | | **25** |
| Shared CV libs | `tests/` | 96 |

### Ejemplos representativos

- `test_predict_with_token_persists_prediction` — POST con Bearer válido
  devuelve 200 y deja una fila en `predictions` con el `user_id` del JWT.
- `test_history_returns_only_own_predictions` — dos usuarios, una
  predicción cada uno; cada uno ve solo la suya. Test de aislamiento.
- `test_register_login_predict_history_round_trip` — flujo cross-service
  completo contra Postgres real.

### Ejecución

```bash
pytest -v                                    # toda la suite
pytest services/auth/tests services/classifier/tests   # solo backend
```

> *[Captura — Output de `pytest -v` en verde]*
>
> ![pytest](docs/img/pytest.png)

---

## e) Automatización en scripts bash

Cuatro scripts en `scripts/`, todos ejecutables desde la raíz del repo:

| Script | Propósito |
| --- | --- |
| `scripts/clone.sh [dest]` | Clona el repo, hace checkout de `develop`. URL override con `REPO_URL=...`. |
| `scripts/test.sh` | Crea `.venv`, instala dependencias raíz + por servicio, corre `pytest`. `SKIP_INTEGRATION=1` salta los tests que necesitan Postgres. |
| `scripts/run-local.sh [up\|down\|logs]` | Levanta / baja el stack `docker compose`. Crea `.env` desde `.env.example` la primera vez. |
| `scripts/train.sh` | Corre el contenedor de training contra `DATASET_PATH`. |

```bash
./scripts/clone.sh ~/work/plant_health
./scripts/test.sh
./scripts/run-local.sh up
```

> *[Captura — Salida del script `test.sh`]*
>
> ![scripts](docs/img/scripts.png)

---

## f) Dockerización

### Estructura

- Un `Dockerfile` por servicio: `services/auth/Dockerfile`,
  `services/classifier/Dockerfile`, `services/training/Dockerfile`.
- Imagen base: `python:3.11-slim`. Cada servicio instala únicamente sus
  propias `requirements.txt` para reducir la superficie de la imagen.
- `docker-compose.yml` orquesta **4 servicios**: `postgres`, `auth`,
  `classifier`, `training` (este último bajo el profile `training` para
  que no arranque por defecto).

### Redes

| Red | Quién la usa |
| --- | --- |
| `private` | postgres ↔ auth, classifier, training |
| `public` | auth, classifier (expuestos en `:8001` y `:8002`) |

Postgres no expone puertos al host por defecto en producción; en local sí
para facilitar inspección.

### Run

```bash
cp .env.example .env
docker compose up --build           # postgres + auth + classifier
docker compose --profile training run --rm training python train.py \
    --dataset /datasets/PlantVillage
```

> *[Captura — `docker compose ps` con todos los servicios `healthy`]*
>
> ![docker-ps](docs/img/docker-ps.png)

> *[Captura — `curl` contra `localhost:8001/auth/register` y luego
> `localhost:8002/classifier/predict`]*
>
> ![curl-flow](docs/img/curl-flow.png)

---

## g) Conclusiones preliminares

- **Conventional Commits** dieron trazabilidad real al monorepo: el
  changelog se lee de un vistazo, los PRs heredan el título del commit y el
  scope (`auth`, `classifier`, `training`, `docker`, `ci`) localiza cada
  cambio sin abrir el diff.
- **Tests unitarios** detectaron tres regresiones durante el desarrollo
  (incompatibilidad `passlib` ↔ `bcrypt` 4.1, falta de `httpx` para
  `TestClient` en CI, dependencia oculta `matplotlib`). Sin la suite, esas
  fallas habrían aparecido en el demo.
- **Docker + compose** convirtieron "funciona en mi máquina" en "funciona
  con `docker compose up`". CI usa exactamente el mismo `Dockerfile` que
  desarrollo, lo que cierra la brecha entre lo que se prueba y lo que se
  despliega. Los esqueletos de Kubernetes en `infra/k8s/` dejan el camino
  abierto al deploy en cluster sin refactor de código.

---

## Anexos

### Variables de entorno (extracto de `.env.example`)

```
DATABASE_URL=postgresql+psycopg2://leaf_app:leaf_app@postgres:5432/leaf_app
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
ARTIFACTS_DIR=/app/artifacts
DATASET_PATH=./datasets/PlantVillage
```

### Cómo levantar el proyecto

```bash
git clone https://github.com/marcelochincha/plant_health_checker.git
cd plant_health_checker
cp .env.example .env
docker compose up --build
```

### Cómo ejecutar las pruebas

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install pytest
pytest -v
```
