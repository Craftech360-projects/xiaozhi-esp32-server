// EMQX Client - Connects mqtt-gateway to EMQX broker to receive messages from all devices
const mqtt = require('mqtt');
const debugModule = require('debug');
const debug = debugModule('emqx-client');
const { EventEmitter } = require('events');

class EMQXClient extends EventEmitter {
  constructor(config) {
    super();
    this.config = {
      host: config.host || 'localhost',
      port: config.port || 1884,
      clientId: config.clientId || 'mqtt-gateway-client',
      username: config.username || '',
      password: config.password || '',
      topics: config.topics || ['device-server', 'devices/+/+', 'internal/server-ingest'],
      ...config
    };
    this.client = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
  }

  connect() {
    const connectUrl = `mqtt://${this.config.host}:${this.config.port}`;
    
    debug(`Connecting to EMQX broker: ${connectUrl}`);
    
    this.client = mqtt.connect(connectUrl, {
      clientId: this.config.clientId,
      username: this.config.username,
      password: this.config.password,
      keepalive: 60,
      connectTimeout: 10000,
      reconnectPeriod: 5000,
      clean: true
    });

    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.client.on('connect', () => {
      debug('Connected to EMQX broker');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      
      // Subscribe to device topics
      this.config.topics.forEach(topic => {
        console.log(`🔄 Attempting to subscribe to topic: ${topic}`);
        this.client.subscribe(topic, (err) => {
          if (err) {
            console.error(`❌ Failed to subscribe to ${topic}:`, err);
            debug(`Failed to subscribe to ${topic}:`, err);
          } else {
            console.log(`✅ Successfully subscribed to topic: ${topic}`);
            debug(`Subscribed to topic: ${topic}`);
          }
        });
      });

      this.emit('connected');
    });

    this.client.on('message', (topic, message) => {
      console.log(`🔔 EMQX Message Received on topic: ${topic}`);
      console.log(`📨 Raw message: ${message.toString()}`);
      
      try {
        const payload = JSON.parse(message.toString());
        debug(`Received message on ${topic}:`, payload);
        console.log(`✅ Parsed JSON payload:`, JSON.stringify(payload, null, 2));
        
        // Emit message event with topic and parsed payload
        this.emit('message', { topic, payload });
      } catch (error) {
        debug(`Failed to parse message from ${topic}:`, error);
        console.log(`⚠️ Non-JSON message on ${topic}: ${message.toString()}`);
        // Still emit for non-JSON messages
        this.emit('message', { topic, payload: message.toString() });
      }
    });

    this.client.on('error', (error) => {
      debug('EMQX connection error:', error);
      this.emit('error', error);
    });

    this.client.on('close', () => {
      debug('Disconnected from EMQX broker');
      this.isConnected = false;
      this.emit('disconnected');
    });

    this.client.on('offline', () => {
      debug('EMQX client went offline');
      this.isConnected = false;
    });

    this.client.on('reconnect', () => {
      this.reconnectAttempts++;
      debug(`Attempting to reconnect to EMQX (attempt ${this.reconnectAttempts})`);
      
      if (this.reconnectAttempts > this.maxReconnectAttempts) {
        debug('Max reconnection attempts reached, giving up');
        this.disconnect();
      }
    });
  }

  publish(topic, message, options = {}) {
    if (!this.isConnected) {
      debug('Cannot publish: not connected to EMQX');
      return false;
    }

    const payload = typeof message === 'object' ? JSON.stringify(message) : message;
    
    this.client.publish(topic, payload, {
      qos: options.qos || 0,
      retain: options.retain || false
    }, (err) => {
      if (err) {
        debug(`Failed to publish to ${topic}:`, err);
      } else {
        debug(`Published message to ${topic}`);
      }
    });
    
    return true;
  }

  disconnect() {
    if (this.client) {
      debug('Disconnecting from EMQX broker');
      this.client.end();
      this.client = null;
      this.isConnected = false;
    }
  }

  getConnectionStatus() {
    return {
      connected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

module.exports = { EMQXClient };