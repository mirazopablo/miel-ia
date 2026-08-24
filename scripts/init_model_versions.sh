#!/bin/bash
# Initialize Model Versioning Structure

# 1. Create legacy directory
mkdir -p trained_models/v1.2/binary
mkdir -p trained_models/v1.2/classify

# 2. Move existing models (ignoring errors if already moved)
mv trained_models/binary/* trained_models/v1.2/binary/ 2>/dev/null || true
mv trained_models/classify/* trained_models/v1.2/classify/ 2>/dev/null || true

# 3. Create new v2.0 structure
mkdir -p trained_models/v2.0/binary/models
mkdir -p trained_models/v2.0/binary/scaler
mkdir -p trained_models/v2.0/binary/metrics

mkdir -p trained_models/v2.0/classify/models
mkdir -p trained_models/v2.0/classify/scaler
mkdir -p trained_models/v2.0/classify/metrics

echo "Version folders created successfully."
