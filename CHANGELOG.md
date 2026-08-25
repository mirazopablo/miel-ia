## v3.1.1 (2026-08-24)

### Fix

- **setup**: fix CORS middleware initialization and allowed origins

## v3.1.0 (2026-08-24)

### Feat

- **explainer**: implement natural language summaries and decouple reference stats

### Fix

- **models**: resolve model loading path discrepancy

## v3.0.0 (2026-08-24)

### BREAKING CHANGE

- predict_binary and predict_classify now strictly require scaled data

### Feat

- **models**: add v2.0 multiclass classification models and metrics

### Fix

- **ml-pipeline**: implement v2.0 inference pipeline with dynamic standard scaling

### Refactor

- **api**: remove deprecated test endpoints for binary and multiclass

## v2.0.0 (2026-08-24)

### BREAKING CHANGE

- The inference architecture has been entirely replaced by v2.0 models. Legacy v1.2 models have been
moved to deprecation folders. All new inference requests must conform to the new v2.0 scaler and
feature mapping logic through diagnose.py.

### Feat

- **ml-pipeline**: v2.0 classification models and deprecate legacy endpoint
- **ml-pipeline**: implement real-time logging and verbosity for training endpoints
- **ml-data**: add stable datasets and methodology bitacora

### Fix

- **ml-infrastructure**: resolve absolute import module errors in architectures init
- **api-routes**: bind training endpoints to correct scripts and fix missing scaler in test routes

### Refactor

- **ml-pipeline**: enforce isolated test sets for honest metric evaluation
- add version refactor script
- **gitignore**: approve scripts folder
- **ml-pipeline**: migrate legacy models to v1.2 versioning structure
- **ml-architecture**: refactor ml models to support dynamic input dimensions and versioning

## v1.2.0 (2026-08-22)

### Feat

- **auth**: include role names instead of IDs in JWT
- **api**: implement global RequestValidationError handler
- **config**: add FRONTEND_URL setting to Pydantic config and CORS origins
- **email**: improve email sending utility and static file serving

### Fix

- **dto**: allow spaces in user name validation
- **ml-pipeline**: defer tensorflow import and implement lazy model loading to prevent sigill on non-avx cpus
- **core**: prevent uvicorn restart loop by adding static dir creation and pre-flight module import check
- **deploy**: disable CUDA initialization and silence TensorFlow C++ logs

### Perf

- **deploy**: optimize memory limits and thread allocation for intel celeron g5925 hardware

## v1.1.0 (2026-03-23)

### BREAKING CHANGE

- fix
- feat

### Feat

- **ml**: Enhance ML model explanations with electrode and metric parsing
- **auth**: Add current user dependency to user registration
- **#18 email recovery**: sistema de recuracion de contraseña v1.0
- adios CI/CD

### Fix

- **services**: Fix role validation and add ML results decryption
- **docker**: explicitly mount emails_out as rw and increase deploy timeout
- **intento de arreglar docker**: intento de sacar el flag :ro
- **#8 deploy**: intento de arreglar el deploy numero 40404
- **#8 deploy**: intento de arreglar el deploy y los secrets
- **#8 deploy intento 5**: intento de arreglar el deploy ahora con un runner
- **#8 deploy**: intento de arreglo del deploy
- **arreglos y cambios en logs para auth**: descripciones loguru

### Refactor

- **database**: Migrate database from MySQL to PostgreSQL
- **.env-example**: new Env example for new database mysql

## v1.0 (2025-09-04)

### Feat

- **auth**: Introduce AuthService for user authentication and authorization (#17)
- Implement user authentication and registration (#17)

### Fix

- **repositories**: Refine data access layer with type corrections and optimizations (#17)
- **services**: Address critical bugs and integrate authentication across core services (#17)
- **dtos**: Resolve authentication/registration bugs and enable multi-role user creation (#17, #15)
- Enhance security and refine core API endpoints (#17)

### Refactor

- **models**: Transition to UUID primary keys and introduce base model (#15)
- Update security config and enhance debugging in config.py (#17)
