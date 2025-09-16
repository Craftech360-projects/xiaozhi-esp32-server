@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

@description('Application name prefix')
param appName string = 'xiaozhi'

// Variables
var resourcePrefix = '${appName}-${environment}'
var appServicePlanName = '${resourcePrefix}-plan'
var managerApiName = '${resourcePrefix}-manager-api'
var managerWebName = '${resourcePrefix}-manager-web'
var mqttGatewayName = '${resourcePrefix}-mqtt-gateway'
var storageAccountName = '${replace(resourcePrefix, '-', '')}storage'
var databaseServerName = '${resourcePrefix}-mysql'

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'B2'
    tier: 'Basic'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// Manager API (Java App Service)
resource managerApi 'Microsoft.Web/sites@2022-03-01' = {
  name: managerApiName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'JAVA|17-java17'
      appSettings: [
        {
          name: 'SPRING_PROFILES_ACTIVE'
          value: environment
        }
        {
          name: 'SERVER_PORT'
          value: '8080'
        }
        {
          name: 'JAVA_OPTS'
          value: '-Xms512m -Xmx1g'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
      ]
      javaVersion: '17'
    }
    httpsOnly: true
  }
}

// Manager Web (Static Web App or App Service)
resource managerWeb 'Microsoft.Web/sites@2022-03-01' = {
  name: managerWebName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      appSettings: [
        {
          name: 'NODE_ENV'
          value: environment
        }
        {
          name: 'PORT'
          value: '8081'
        }
      ]
      appCommandLine: 'npx serve -s dist -l 8081'
    }
    httpsOnly: true
  }
}

// MQTT Gateway (Node.js App Service)
resource mqttGateway 'Microsoft.Web/sites@2022-03-01' = {
  name: mqttGatewayName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      appSettings: [
        {
          name: 'NODE_ENV'
          value: environment
        }
        {
          name: 'MQTT_PORT'
          value: '1883'
        }
        {
          name: 'HTTP_PORT'
          value: '8884'
        }
        {
          name: 'PORT'
          value: '8884'
        }
      ]
      appCommandLine: 'node app.js'
    }
    httpsOnly: true
  }
}

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: true
  }
}

// MySQL Database (if needed)
resource databaseServer 'Microsoft.DBforMySQL/flexibleServers@2021-12-01-preview' = {
  name: databaseServerName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: 'xiaozhi_admin'
    administratorLoginPassword: 'XiaoZhi2024!' // Change this!
    version: '8.0.21'
    storage: {
      storageSizeGB: 20
      iops: 360
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

// Database firewall rules
resource databaseFirewallRule 'Microsoft.DBforMySQL/flexibleServers/firewallRules@2021-12-01-preview' = {
  parent: databaseServer
  name: 'AllowAllAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Output URLs
output managerApiUrl string = 'https://${managerApi.properties.defaultHostName}'
output managerWebUrl string = 'https://${managerWeb.properties.defaultHostName}'
output mqttGatewayUrl string = 'https://${mqttGateway.properties.defaultHostName}'
output storageAccountName string = storageAccount.name
output databaseServerName string = databaseServer.properties.fullyQualifiedDomainName