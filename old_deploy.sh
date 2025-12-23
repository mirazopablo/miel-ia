#!/bin/bash

# Configuraciones básicas
IMAGE_NAME=mielia_api
CONTAINER_NAME=api-mielia
IMAGE_TAG=v1.0.0
RESOURCE_GROUP=miel-ia
LOCATION=eastus
ACR_NAME=apimielia  # sin mayúsculas
PORT_CONTAINER=8000

az login

az acr login --name $ACR_NAME

# Construcción y subida de imagen
docker build -t $IMAGE_NAME:$IMAGE_TAG .
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG

# Obtener credenciales del ACR
USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Desplegar en Azure Container Instance
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG \
  --cpu 1 \
  --memory 1 \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $USERNAME \
  --registry-password $PASSWORD \
  --dns-name-label mielia-api-$RANDOM \
  --ports $PORT_CONTAINER \
  --location $LOCATION
