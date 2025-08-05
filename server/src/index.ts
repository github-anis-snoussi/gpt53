import * as dotenv from 'dotenv';

dotenv.config();

const dns2 = require('dns2');
const { Packet } = dns2;

const CONFIG = {
  PORT: process.env.PORT ? parseInt(process.env.PORT) : 53,
  HOST: process.env.HOST || '127.0.0.1',
  DEFAULT_TXT_RESPONSE: process.env.DEFAULT_TXT_RESPONSE || 'This wasn\'t supposed to happen… but here we are.',
  DNS_TTL: process.env.DNS_TTL ? parseInt(process.env.DNS_TTL) : 300,
  ENABLE_LOGGING: process.env.ENABLE_LOGGING !== 'false'
};

const log = (...args: any[]) => {
  if (CONFIG.ENABLE_LOGGING) {
    console.log(...args);
  }
};

const getTxtResponse = async (domain: string): Promise<string> => {
  await new Promise(resolve => setTimeout(resolve, 10));
  
  return "Hello, world!";
};

const server = dns2.createServer({
  udp: true,
  tcp: true,
  handle: async (request: any, send: any, rinfo: any) => {
    log(`DNS Query received from ${rinfo.address}:${rinfo.port}`);
    
    const response = Packet.createResponseFromRequest(request);
    const [question] = request.questions;
    const { name, type } = question;
    
    log(`Query for: ${name}, Type: ${type}`);
    
    if (type === Packet.TYPE.TXT) {
      try {
        const txtResponse = await getTxtResponse(name);
        
        response.answers.push({
          name,
          type: Packet.TYPE.TXT,
          class: Packet.CLASS.IN,
          ttl: CONFIG.DNS_TTL,
          data: txtResponse
        });
        log(`Responded with TXT record: ${txtResponse}`);
      } catch (error) {
        console.error('Error generating TXT response:', error);
        response.answers.push({
          name,
          type: Packet.TYPE.TXT,
          class: Packet.CLASS.IN,
          ttl: CONFIG.DNS_TTL,
          data: CONFIG.DEFAULT_TXT_RESPONSE
        });
        log(`Error occurred, returned default TXT record: ${CONFIG.DEFAULT_TXT_RESPONSE}`);
      }
    } else {
      log(`Ignoring non-TXT query for ${name} (Type: ${type})`);
    }
    
    send(response);
  }
});

server.on('request', (request: any, response: any, rinfo: any) => {
  log(`Request ID: ${request.header.id}, Question: ${request.questions[0].name}`);
});

server.on('requestError', (error: any) => {
  console.error('Client sent an invalid request:', error);
});

server.on('listening', () => {
  console.log('🚀 DNS Server is running (TXT Records Only)!');
  console.log(`📍 Listening on: ${CONFIG.HOST}:${CONFIG.PORT}`);
  console.log(`🔧 Configuration:`);
  console.log(`   - Default TXT Response: ${CONFIG.DEFAULT_TXT_RESPONSE}`);
  console.log(`   - TTL: ${CONFIG.DNS_TTL}s`);
  console.log(`   - Logging: ${CONFIG.ENABLE_LOGGING ? 'enabled' : 'disabled'}`);
  console.log(`📋 Test with: dig @${CONFIG.HOST} -p${CONFIG.PORT} TXT example.com`);
  if (CONFIG.PORT === 53) {
    console.log('⚠️  Running on port 53 may require administrator privileges');
  }
  console.log('ℹ️  Only TXT record queries will be answered');
  console.log('🔄 Async handler enabled for dynamic responses');
});

server.on('close', () => {
  console.log('DNS server closed');
});

server.listen({
  udp: {
    port: CONFIG.PORT,
    address: CONFIG.HOST,
    type: "udp4"
  },
  tcp: {
    port: CONFIG.PORT,
    address: CONFIG.HOST
  }
});

process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down DNS server...');
  server.close();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Received SIGTERM, shutting down DNS server...');
  server.close();
  process.exit(0);
});

export default server; 