// Slide Builder v2 - Azure Infrastructure
// Deploy with: az deployment sub create --location eastus2 --template-file main.bicep

targetScope = 'subscription'

@description('Environment name (dev, staging, prod)')
param environment string = 'prod'

@description('Azure region for resources')
param location string = 'eastus2'

@description('Azure OpenAI model deployment name')
param openAiDeploymentName string = 'gpt-4o'

@description('Azure AD tenant ID for authentication')
param tenantId string

@description('Azure AD client ID for the app registration')
param clientId string

// Resource group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'rg-slide-builder-${environment}'
  location: location
  tags: {
    application: 'slide-builder'
    environment: environment
  }
}

// Deploy modules
module storage 'modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    location: location
    environment: environment
  }
}

module containerApps 'modules/container-apps.bicep' = {
  name: 'containerApps'
  scope: rg
  params: {
    location: location
    environment: environment
    storageAccountName: storage.outputs.storageAccountName
    keyVaultName: keyVault.outputs.keyVaultName
    openAiEndpoint: openAi.outputs.endpoint
  }
}

module staticWebApp 'modules/static-web-app.bicep' = {
  name: 'staticWebApp'
  scope: rg
  params: {
    location: location
    environment: environment
    apiUrl: containerApps.outputs.apiUrl
  }
}

module openAi 'modules/openai.bicep' = {
  name: 'openAi'
  scope: rg
  params: {
    location: location
    environment: environment
    deploymentName: openAiDeploymentName
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyVault'
  scope: rg
  params: {
    location: location
    environment: environment
    tenantId: tenantId
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    environment: environment
  }
}

// Outputs
output resourceGroupName string = rg.name
output storageAccountName string = storage.outputs.storageAccountName
output containerAppUrl string = containerApps.outputs.apiUrl
output staticWebAppUrl string = staticWebApp.outputs.url
output openAiEndpoint string = openAi.outputs.endpoint
output keyVaultName string = keyVault.outputs.keyVaultName
