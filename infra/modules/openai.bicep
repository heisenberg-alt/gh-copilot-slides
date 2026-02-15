// Azure OpenAI Service

@description('Azure region')
param location string

@description('Environment name')
param environment string

@description('Deployment name for the model')
param deploymentName string

var openAiName = 'oai-slide-builder-${environment}'

resource openAi 'Microsoft.CognitiveServices/accounts@2023-10-01-preview' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
  tags: {
    application: 'slide-builder'
    environment: environment
  }
}

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-10-01-preview' = {
  parent: openAi
  name: deploymentName
  sku: {
    name: 'Standard'
    capacity: 30 // TPM (thousands of tokens per minute)
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-08-06'
    }
    raiPolicyName: 'Microsoft.Default'
  }
}

output endpoint string = openAi.properties.endpoint
output openAiName string = openAi.name
output deploymentName string = deployment.name
