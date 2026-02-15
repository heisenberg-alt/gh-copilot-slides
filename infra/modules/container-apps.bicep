// Azure Container Apps for the FastAPI backend

@description('Azure region')
param location string

@description('Environment name')
param environment string

@description('Storage account name')
param storageAccountName string

@description('Key Vault name')
param keyVaultName string

@description('Azure OpenAI endpoint')
param openAiEndpoint string

var containerAppEnvName = 'cae-slide-builder-${environment}'
var containerAppName = 'ca-slide-builder-api-${environment}'
var logAnalyticsName = 'log-slide-builder-${environment}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
  tags: {
    application: 'slide-builder'
    environment: environment
  }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
  tags: {
    application: 'slide-builder'
    environment: environment
  }
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        corsPolicy: {
          allowedOrigins: [
            'https://*.azurestaticapps.net'
            'http://localhost:3000'
          ]
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: true
        }
      }
      secrets: [
        {
          name: 'azure-openai-key'
          keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/azure-openai-key'
          identity: 'system'
        }
        {
          name: 'storage-connection-string'
          keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/storage-connection-string'
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder, updated by CI/CD
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
            }
            {
              name: 'SLIDE_LLM_PROVIDER'
              value: 'azure'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 5
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
  tags: {
    application: 'slide-builder'
    environment: environment
  }
}

output apiUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerAppName string = containerApp.name
output managedIdentityId string = containerApp.identity.principalId
