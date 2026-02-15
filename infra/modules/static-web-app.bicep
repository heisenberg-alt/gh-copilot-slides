// Azure Static Web Apps for the Next.js frontend

@description('Azure region')
param location string

@description('Environment name')
param environment string

@description('API URL for the backend')
param apiUrl string

var staticWebAppName = 'swa-slide-builder-${environment}'

resource staticWebApp 'Microsoft.Web/staticSites@2022-03-01' = {
  name: staticWebAppName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    buildProperties: {
      appLocation: 'apps/web'
      outputLocation: '.next'
    }
  }
  tags: {
    application: 'slide-builder'
    environment: environment
  }
}

resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2022-03-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    NEXT_PUBLIC_API_URL: apiUrl
  }
}

output url string = 'https://${staticWebApp.properties.defaultHostname}'
output staticWebAppName string = staticWebApp.name
