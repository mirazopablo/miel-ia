# Miel-IA - Backend | Intelligent Medical Diagnosis API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.10-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)

> **High-performance RESTful API orchestrating an ensemble of Machine Learning models for the early detection of Guillain-Barré Syndrome via Electromyography (EMG) analysis.**

<div align="center">
  <h3>🔗 Frontend Repository</h3>
  <a href="https://github.com/mirazopablo/miel-ia-front">
    <img src="https://img.shields.io/badge/GO_TO_FRONTEND-2b3137?style=for-the-badge&logo=github&logoColor=white" alt="Frontend Repository" />
  </a>
</div>

---

## 🎓 Academic Context

<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/4/41/UM_logo.png" alt="Universidad de Mendoza Logo" width="150"/>
  <br/>
  <br/>
  <p>This project is part of the <strong>Final Integrative Project</strong> chair at the <strong>Universidad de Mendoza</strong> (School of Engineering).</p>
  <p>
    Developed under the supervision of <strong>Bio. Ignacio Bosch</strong>
    <br/>
    <a href="https://github.com/NachoBosch">
      <img src="https://img.shields.io/badge/GitHub-Supervisor-black?style=flat-square&logo=github" alt="Supervisor GitHub"/>
    </a>
  </p>
</div>

> [!NOTE]
> **Academic Repository**: This code is presented as part of an academic evaluation instance. For this reason, the repository does not accept external contributions (Pull Requests) and is maintained as a static reference of the work performed.

---

## 🌟 Technical Architecture

This backend is built on **Clean Architecture** principles, ensuring scalability, maintainability, and strict separation of concerns.

### Core Features
- **Saga Pattern Orchestration**: Manages the complex flow of ML analysis, ensuring data integrity across multiple processing stages.
- **Hybrid ML Ensemble**: A sophisticated voting system combining:
  - **Random Forest** (Scikit-Learn)
  - **XGBoost** (XGBoost Library)
  - **Logistic Regression** (TensorFlow/Keras)
- **Advanced Security**: 
  - **Argon2** hashing for credentials.
  - **JWT** (JSON Web Tokens) for stateless sessions.
  - **Check-Digit** logic for file integrity verification.

### Diagnosis Pipeline

```mermaid
graph TD
    User([ Client / Frontend]) -->|Uploads CSV| API[API Gateway]
    API -->|Validates Format| Svc[Diagnosis Service]

    subgraph " ML Saga Orchestrator"
        Svc -->|Preprocessing| Data{Data Valid?}
        Data -->|No| Err([Error 400])
        Data -->|Yes| Bin[ Binary Detection Phase]
        
        subgraph "Phase 1: Binary Ensemble"
            Bin --> RF1[Random Forest]
            Bin --> XGB1[XGBoost]
            Bin --> LR1[Log. Regression (Keras)]
        end

        RF1 & XGB1 & LR1 --> Vote1{Consensus?}
        Vote1 -->|Negative| ResNeg([Negative Result])
        Vote1 -->|Positive| Class[ Risk Classification Phase]

        subgraph "Phase 2: Classification Ensemble"
            Class --> RF2[Random Forest]
            Class --> XGB2[XGBoost]
            Class --> LR2[Log. Regression (Keras)]
        end

        RF2 & XGB2 & LR2 --> Vote2{Consensus?}
        Vote2 --> ResPos([Positive Result + Risk Level])
    end

    ResNeg & ResPos --> SHAP[SHAP Explainer Process]
    SHAP --> DB[(MySQL Database)]
    DB --> Resp[JSON Response]
```

---

## 🚀 Tech Stack

| Category | Technology | Details |
| :--- | :--- | :--- |
| **Framework** | **FastAPI** | High-performance, async Python framework. |
| **Language** | **Python 3.12** | Optimized for modern type hinting and concurrency. |
| **ML Engine** | **Scikit-Learn & XGBoost** | Traditional ML models implementation. |
| **Deep Learning** | **TensorFlow / Keras** | Used for the Logistic Regression neural component. |
| **Database** | **MySQL 8.0** | Primary relational data storage. |
| **ORM** | **SQLAlchemy** | Database abstraction and ORM. |
| **Migrations** | **Alembic** | Database schema version control. |
| **Auth** | **Python-Jose & Argon2** | Security standards for token generation and hashing. |
| **Container** | **Docker & Compose** | Full environment containerization. |

---

## 📂 Project Structure

```bash
miel-ia/
├── app/
│   ├── api/            # Routes and Controllers (Endpoints)
│   ├── core/           # Configuration, Security, and Global Specs
│   ├── infrastructure/ # DB Connection, Repositories, and Email Svc
│   ├── ml_pipeline/    # ML Models, Predictors, and Preprocessing
│   ├── services/       # Business Logic and Use Cases
│   └── main.py         # Application Entrypoint
├── alembic/            # Database Migrations
├── trained_models/     # Serialized ML Models (.pkl, .keras)
├── requirements.txt    # Python Dependencies
├── docker-compose.yml  # Container Orchestration
└── Dockerfile          # Image Definition
```

---

## ⚡ Installation and Deployment

### Option A: Docker (Recommended)

Ideally, run the full stack (including the database) via Docker Compose.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/mirazopablo/miel-ia
    cd miel-ia
    ```

2.  **Environment Setup**:
    ```bash
    cp .env-example .env
    # Edit .env with your specific configurations
    ```

3.  **Launch**:
    ```bash
    docker-compose up -d --build
    ```

### Option B: Local Execution

1.  **Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    # .venv\Scripts\activate   # Windows
    ```

2.  **Install Dependencies**:
    The project requires Python 3.12 specifically due to NumPy/TensorFlow compatibility.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Server**:
    start the server with hot-reload enabled.
    ```bash
    uvicorn app.main:app --reload
    ```

---

## 👨‍💻 Author

**Mirazo Pablo**
- 🔭 Computer Engineering Student
- 🐱 [GitHub Profile](https://github.com/mirazopablo)

---

<p align="center">
  Built with ❤️ for Medical Innovation
</p>
