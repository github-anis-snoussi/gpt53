import * as dotenv from 'dotenv';
import { openai } from '@ai-sdk/openai';
import { generateText } from 'ai';

dotenv.config();

const dns2 = require('dns2');
const { Packet } = dns2;

const CONFIG = {
  PORT: process.env.PORT ? parseInt(process.env.PORT) : 5333,
  HOST: process.env.HOST || '127.0.0.1',
  DEFAULT_TXT_RESPONSE: process.env.DEFAULT_TXT_RESPONSE || 'This wasn\'t supposed to happen… but here we are.',
  DNS_TTL: process.env.DNS_TTL ? parseInt(process.env.DNS_TTL) : 0,
  ENABLE_LOGGING: process.env.ENABLE_LOGGING !== 'false',
  API_KEY: process.env.API_KEY || '',
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || ''
};


const LLM_MODELS = [
  'gpt-4o',
  'gpt-4o-mini',
  'gpt-4-turbo',
  'gpt-4',
  'gpt-3.5-turbo',
  'gpt-3.5-turbo-16k',
  'o1-preview',
  'o1-mini',
  'gpt-4o-2024-08-06',
  'gpt-4-turbo-2024-04-09'
];

const log = (...args: any[]) => {
  if (CONFIG.ENABLE_LOGGING) {
    console.log(...args);
  }
};

const validateRequest = (queryPart: string): string | null => {
  if (queryPart.length < 11) {
    return 'ERROR: Invalid format. Expected: [10-char API key][1-char model index][prompt]';
  }
  return null;
};

const validateAuth = (providedApiKey: string): string | null => {
  if (!CONFIG.API_KEY) {
    return 'ERROR: Server API key not configured';
  }
  if (providedApiKey !== CONFIG.API_KEY) {
    log(`Authentication failed. Provided: ${providedApiKey}, Expected: ${CONFIG.API_KEY}`);
    return 'ERROR: Invalid API key';
  }
  return null;
};

const validateModel = (modelIndexNum: number): string | null => {
  if (isNaN(modelIndexNum) || modelIndexNum < 0 || modelIndexNum >= LLM_MODELS.length) {
    return `ERROR: Invalid model index. Use 0-${LLM_MODELS.length - 1}`;
  }
  return null;
};

const validatePrompt = (userPrompt: string): string | null => {
  if (!userPrompt || userPrompt.trim().length === 0) {
    return 'ERROR: No prompt provided';
  }
  if (!CONFIG.OPENAI_API_KEY) {
    return 'ERROR: OpenAI API key not configured';
  }
  return null;
};

const sanitizeResponse = (text: string): string => {
  const cleanedText = text
  // Remove problematic characters that don't work well in DNS
  .replace(/[""'']/g, '"')  // Replace smart quotes with regular quotes
  .replace(/[–—]/g, '-')    // Replace em/en dashes with regular dash
  .replace(/…/g, '...')     // Replace ellipsis character with three dots
  .replace(/[^\x20-\x7E]/g, '') // Remove non-ASCII characters
  .replace(/\s+/g, ' ')     // Collapse multiple spaces
  .trim();
  
  // Ensure DNS TXT record compatibility (max 255 characters)
  const maxLength = 240; // Leave some buffer for safety
  return cleanedText.length > maxLength ? 
    cleanedText.substring(0, maxLength - 3) + '...' : cleanedText;
};

const handleError = (error: any): string => {
  console.error('Error in getTxtResponse:', error);
  
  if (error instanceof Error) {
    switch (true) {
      case error.message.includes('API key'):
        return 'ERROR: Invalid OpenAI API key';
      case error.message.includes('model'):
        return 'ERROR: Model not available';
      case error.message.includes('rate limit'):
        return 'ERROR: Rate limit exceeded';
    }
  }
  
  return 'ERROR: Failed to generate response';
};

const getTxtResponse = async (domain: string): Promise<string> => {
  try {
    const queryPart = domain;
    
    switch (queryPart) {
      case 'PING':
        return 'PONG';
      case 'LIST':
        const modelList = LLM_MODELS.map((model, index) => `${index}:${model}`).join(' | ');
        return `Available models: ${modelList}`;
    }
    
    const validationError = validateRequest(queryPart);
    if (validationError) return validationError;
    
    const providedApiKey = queryPart.substring(0, 10);
    const modelIndex = queryPart.substring(10, 11);
    const userPrompt = queryPart.substring(11);
    
    const authError = validateAuth(providedApiKey);
    if (authError) return authError;
    
    const modelIndexNum = parseInt(modelIndex, 10);
    const modelError = validateModel(modelIndexNum);
    if (modelError) return modelError;
    
    const promptError = validatePrompt(userPrompt);
    if (promptError) return promptError;
    
    const selectedModel = LLM_MODELS[modelIndexNum];
    log(`Using model: ${selectedModel} for prompt: ${userPrompt.substring(0, 50)}${userPrompt.length > 50 ? '...' : ''}`);
    
    const { text } = await generateText({
      model: openai(selectedModel),
      system: "You are a helpful assistant. Keep responses concise and under 200 characters when possible. Use simple ASCII characters only.",
      prompt: userPrompt,
      maxOutputTokens: 200,
      temperature: 0.7,
    });
    
    const response = sanitizeResponse(text);
    log(`LLM Response: ${response.substring(0, 100)}${response.length > 100 ? '...' : ''}`);
    
    return response;
    
  } catch (error) {
    return handleError(error);
  }
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
  console.log('🚀 DNS Server with LLM Chat is running!');
  console.log(`📍 Listening on: ${CONFIG.HOST}:${CONFIG.PORT}`);
  console.log(`🔧 Configuration:`);
  console.log(`   - Default TXT Response: ${CONFIG.DEFAULT_TXT_RESPONSE}`);
  console.log(`   - TTL: ${CONFIG.DNS_TTL}s`);
  console.log(`   - Logging: ${CONFIG.ENABLE_LOGGING ? 'enabled' : 'disabled'}`);
  console.log(`   - API Key configured: ${CONFIG.API_KEY ? 'YES' : 'NO'}`);
  console.log(`   - OpenAI API Key configured: ${CONFIG.OPENAI_API_KEY ? 'YES' : 'NO'}`);
  console.log(`🤖 Available LLM Models:`);
  LLM_MODELS.forEach((model, index) => {
    console.log(`   ${index}: ${model}`);
  });
  console.log(`📋 Usage format: [10-char API key][model index 0-9][your prompt]`);
  console.log(`   Example: dig @${CONFIG.HOST} -p${CONFIG.PORT} TXT "myapikey123hello"`);
  console.log(`   Where "myapikey12" is API key, "3" selects gpt-4, "hello" is prompt`);
  console.log(`🔧 Test endpoints (no auth required):`);
  console.log(`   PING → PONG | LIST → Available models`);
  if (CONFIG.PORT === 53) {
    console.log('⚠️  Running on port 53 may require administrator privileges');
  }
  console.log('ℹ️  Only TXT record queries will be answered');
  console.log('🔄 Authenticated LLM chat via DNS TXT records');
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