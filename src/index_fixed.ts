#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListResourceTemplatesRequestSchema,
  SubscribeRequestSchema,
  UnsubscribeRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createServer } from 'http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface TransportConfig {
  type: 'stdio' | 'sse';
  port?: number;
  host?: string;
}

class EnhancedAutoGenServer {
  private server: Server;
  private pythonPath: string;
  private expressApp?: express.Application;
  private httpServer?: ReturnType<typeof createServer>;
  private sseTransports: Map<string, SSEServerTransport> = new Map();
  private subscribers: Set<string> = new Set();
  private progressTokens: Map<string, string> = new Map();
  private lastResourceUpdate: number = Date.now();

  constructor() {
    this.server = new Server(
      {
        name: 'enhanced-autogen-mcp',
        version: '0.3.0',
      },
      {
        capabilities: {
          tools: {},
          prompts: {},
          resources: {
            subscribe: true,
            listChanged: true,
          },
          logging: {},
        },
        instructions: 'Enhanced AutoGen MCP Server with SSE support, real-time updates, and comprehensive MCP protocol implementation.',
      }
    );

    this.pythonPath = process.env.PYTHON_PATH || 'python';
    this.setupHandlers();

    this.server.onerror = (error) => console.error('[MCP Error]', error);
    
    process.on('SIGINT', async () => {
      await this.cleanup();
      process.exit(0);
    });
  }

  private async cleanup(): Promise<void> {
    console.error('Shutting down Enhanced AutoGen MCP Server...');
    
    for (const transport of this.sseTransports.values()) {
      await transport.close();
    }
    this.sseTransports.clear();
    
    if (this.httpServer) {
      this.httpServer.close();
    }
    
    await this.server.close();
  }

  private setupHandlers(): void {
    const PROMPTS = {
      'autogen-workflow': {
        name: 'autogen-workflow',
        description: 'Create a sophisticated multi-agent AutoGen workflow with real-time progress tracking',
        arguments: [
          {
            name: 'task_description',
            description: 'Detailed description of the task to accomplish',
            required: true,
          },
          {
            name: 'agent_count',
            description: 'Number of agents to create (2-10)',
            required: false,
          },
          {
            name: 'workflow_type',
            description: 'Type of workflow (sequential, group_chat, hierarchical, swarm)',
            required: false,
          },
          {
            name: 'streaming',
            description: 'Enable real-time streaming of agent conversations',
            required: false,
          },
        ],
      },
      'code-review': {
        name: 'code-review',
        description: 'Set up agents for collaborative code review with streaming feedback',
        arguments: [
          {
            name: 'code',
            description: 'Code to review',
            required: true,
          },
          {
            name: 'language',
            description: 'Programming language',
            required: false,
          },
          {
            name: 'severity_level',
            description: 'Review severity (basic, thorough, comprehensive)',
            required: false,
          },
        ],
      },
      'research-analysis': {
        name: 'research-analysis',
        description: 'Create research and analysis workflow with streaming progress updates',
        arguments: [
          {
            name: 'topic',
            description: 'Research topic or question',
            required: true,
          },
          {
            name: 'depth',
            description: 'Analysis depth (basic, detailed, comprehensive)',
            required: false,
          },
        ],
      },
    };

    const RESOURCE_TEMPLATES = {
      'agent-performance': {
        uriTemplate: 'autogen://agents/{agent_id}/performance',
        name: 'Agent Performance Metrics',
        description: 'Real-time performance metrics for specific agents',
        mimeType: 'application/json',
      },
      'workflow-status': {
        uriTemplate: 'autogen://workflows/{workflow_id}/status',
        name: 'Workflow Status',
        description: 'Real-time workflow execution status and progress',
        mimeType: 'application/json',
      },
    };

    this.server.setRequestHandler(ListPromptsRequestSchema, async () => ({
      prompts: Object.values(PROMPTS),
    }));

    this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {
      const promptName = request.params.name;
      const args = request.params.arguments || {};

      if (promptName === 'autogen-workflow') {
        const taskDescription = args.task_description || '';
        const agentCount = args.agent_count || '3';
        const workflowType = args.workflow_type || 'group_chat';
        const streaming = Boolean(args.streaming);
        
        return {
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: `Create an enhanced AutoGen workflow for: ${taskDescription}

Configuration:
- Agents: ${agentCount} specialized agents
- Workflow Type: ${workflowType}
- Real-time Streaming: ${streaming ? 'enabled' : 'disabled'}

Please provide a complete workflow configuration.`,
              },
            },
          ],
        };
      }

      throw new McpError(ErrorCode.InvalidRequest, `Unknown prompt: ${promptName}`);
    });

    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: 'autogen://agents/list',
          name: 'Active Agents Registry',
          description: 'Real-time list of all active AutoGen agents',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://system/metrics',
          name: 'System Performance Metrics',
          description: 'Real-time system performance and health metrics',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://subscriptions/list',
          name: 'Active Subscriptions',
          description: 'List of active resource subscriptions',
          mimeType: 'application/json',
        },
      ],
    }));

    this.server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => ({
      resourceTemplates: Object.values(RESOURCE_TEMPLATES),
    }));

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const uri = request.params.uri;

      if (uri === 'autogen://system/metrics') {
        const metrics = {
          timestamp: new Date().toISOString(),
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          sseConnections: this.sseTransports.size,
          activeSubscriptions: this.subscribers.size,
          progressTokens: this.progressTokens.size,
          lastResourceUpdate: new Date(this.lastResourceUpdate).toISOString(),
        };

        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(metrics, null, 2),
            },
          ],
        };
      }

      if (uri === 'autogen://subscriptions/list') {
        const subscriptions = {
          active: Array.from(this.subscribers),
          count: this.subscribers.size,
          sseTransports: this.sseTransports.size,
          lastUpdated: new Date().toISOString(),
        };

        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(subscriptions, null, 2),
            },
          ],
        };
      }

      // Delegate to Python handler
      const result = await this.callPythonHandler('get_resource', { uri });
      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    });

    this.server.setRequestHandler(SubscribeRequestSchema, async (request) => {
      const uri = request.params.uri;
      this.subscribers.add(uri);
      await this.notifyResourceUpdate(uri);
      return {};
    });

    this.server.setRequestHandler(UnsubscribeRequestSchema, async (request) => {
      const uri = request.params.uri;
      this.subscribers.delete(uri);
      return {};
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_streaming_workflow',
          description: 'Create a workflow with real-time streaming and progress updates',
          inputSchema: {
            type: 'object',
            properties: {
              workflow_name: { type: 'string', description: 'Name for the workflow' },
              workflow_type: { type: 'string', description: 'Type of workflow' },
              agents: { type: 'array', description: 'List of agent configurations' },
              streaming: { type: 'boolean', description: 'Enable streaming' },
              progress_token: { type: 'string', description: 'Progress token' },
            },
            required: ['workflow_name', 'workflow_type', 'agents'],
          },
        },
        {
          name: 'start_streaming_chat',
          description: 'Start a streaming chat session with real-time updates',
          inputSchema: {
            type: 'object',
            properties: {
              agent_name: { type: 'string', description: 'Name of the agent to chat with' },
              message: { type: 'string', description: 'Initial message' },
              streaming: { type: 'boolean', description: 'Enable real-time streaming' },
              progress_token: { type: 'string', description: 'Token for progress notifications' },
            },
            required: ['agent_name', 'message'],
          },
        },
        {
          name: 'create_agent',
          description: 'Create a new AutoGen agent with enhanced capabilities',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Unique name for the agent' },
              type: { type: 'string', description: 'Agent type' },
              system_message: { type: 'string', description: 'System message' },
              llm_config: { type: 'object', description: 'LLM configuration' },
            },
            required: ['name', 'type'],
          },
        },
        {
          name: 'execute_workflow',
          description: 'Execute a workflow with streaming support',
          inputSchema: {
            type: 'object',
            properties: {
              workflow_name: { type: 'string', description: 'Workflow name' },
              input_data: { type: 'object', description: 'Input data' },
              streaming: { type: 'boolean', description: 'Enable streaming' },
            },
            required: ['workflow_name', 'input_data'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const args = request.params.arguments || {};
      const progressToken = typeof args.progress_token === 'string' ? args.progress_token : undefined;

      try {
        if (progressToken) {
          this.progressTokens.set(progressToken, toolName);
          await this.sendProgressNotification(progressToken, 0, `Starting ${toolName}...`);
        }

        if (toolName === 'create_streaming_workflow' || toolName === 'start_streaming_chat') {
          return await this.handleStreamingTool(toolName, args, progressToken);
        }

        if (progressToken) {
          await this.sendProgressNotification(progressToken, 50, `Processing ${toolName}...`);
        }

        const result = await this.callPythonHandler(toolName, args);

        if (progressToken) {
          await this.sendProgressNotification(progressToken, 100, `Completed ${toolName}`);
          this.progressTokens.delete(progressToken);
        }

        return result;
      } catch (error) {
        if (progressToken) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          await this.sendProgressNotification(progressToken, -1, `Error in ${toolName}: ${errorMessage}`);
          this.progressTokens.delete(progressToken);
        }
        throw error;
      }
    });
  }

  private async handleStreamingTool(toolName: string, args: any, progressToken?: string): Promise<any> {
    if (progressToken) {
      await this.sendProgressNotification(progressToken, 25, 'Initializing streaming...');
    }

    const result = await this.callPythonHandler(toolName, args);

    if (args.streaming && this.sseTransports.size > 0) {
      for (const transport of this.sseTransports.values()) {
        try {
          await transport.send({
            jsonrpc: '2.0',
            method: 'notifications/progress',
            params: {
              progressToken: progressToken || 'streaming',
              progress: 75,
              message: 'Streaming updates...',
              data: result,
            },
          });
        } catch (error) {
          console.error('Error sending streaming update:', error);
        }
      }
    }

    if (progressToken) {
      await this.sendProgressNotification(progressToken, 100, 'Streaming completed');
    }

    return result;
  }

  private async sendProgressNotification(progressToken: string, progress: number, message: string): Promise<void> {
    for (const transport of this.sseTransports.values()) {
      try {
        await transport.send({
          jsonrpc: '2.0',
          method: 'notifications/progress',
          params: {
            progressToken,
            progress,
            message,
            timestamp: new Date().toISOString(),
          },
        });
      } catch (error) {
        console.error('Error sending progress notification:', error);
      }
    }
  }

  private async notifyResourceUpdate(uri: string, data?: any): Promise<void> {
    if (this.subscribers.has(uri)) {
      for (const transport of this.sseTransports.values()) {
        try {
          await transport.send({
            jsonrpc: '2.0',
            method: 'notifications/resource_updated',
            params: {
              uri,
              data: data || { updated: new Date().toISOString() },
              timestamp: new Date().toISOString(),
            },
          });
        } catch (error) {
          console.error('Error sending resource update notification:', error);
        }
      }
    }
  }

  private async callPythonHandler(toolName: string, args: any = {}): Promise<any> {
    const scriptPath = join(__dirname, 'autogen_mcp', 'server.py');
    const pythonArgs = [scriptPath, toolName, JSON.stringify(args)];

    return new Promise((resolve, reject) => {
      const process = spawn(this.pythonPath, pythonArgs);
      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        if (code !== 0) {
          reject(new McpError(ErrorCode.InternalError, stderr || 'Python process failed'));
          return;
        }

        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (error) {
          reject(new McpError(ErrorCode.InternalError, 'Invalid JSON response from Python'));
        }
      });

      process.on('error', (error) => {
        reject(new McpError(ErrorCode.InternalError, error.message));
      });
    });
  }

  async runWithStdio(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Enhanced AutoGen MCP server running on stdio');
  }

  async runWithSSE(config: { port: number; host?: string }): Promise<void> {
    const { port, host = 'localhost' } = config;
    
    this.expressApp = express();
    
    this.expressApp.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'", "'unsafe-inline'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          connectSrc: ["'self'"],
        },
      },
    }));
    
    this.expressApp.use(cors({
      origin: true,
      credentials: true,
      methods: ['GET', 'POST', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization'],
    }));
    
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000,
      max: 1000,
      message: 'Too many requests from this IP',
    });
    this.expressApp.use(limiter);
    
    this.expressApp.use(express.json({ limit: '10mb' }));
    
    this.expressApp.get('/health', (_req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        sseConnections: this.sseTransports.size,
        subscriptions: this.subscribers.size,
        memoryUsage: process.memoryUsage(),
      });
    });
    
    this.expressApp.get('/sse', async (req, res) => {
      const sessionId = req.query.sessionId as string || `session_${Date.now()}`;
      
      try {
        const transport = new SSEServerTransport('/message', res);
        this.sseTransports.set(sessionId, transport);
        
        transport.onclose = () => {
          this.sseTransports.delete(sessionId);
          console.error(`SSE transport closed for session: ${sessionId}`);
        };
        
        transport.onerror = (error) => {
          console.error(`SSE transport error for session ${sessionId}:`, error);
          this.sseTransports.delete(sessionId);
        };
        
        await this.server.connect(transport);
        await transport.start();
        
        console.error(`SSE transport started for session: ${sessionId}`);
      } catch (error) {
        console.error('Error setting up SSE transport:', error);
        res.status(500).json({ error: 'Failed to establish SSE connection' });
      }
    });
    
    this.expressApp.post('/message', async (req, res) => {
      const sessionId = req.query.sessionId as string;
      
      if (!sessionId || !this.sseTransports.has(sessionId)) {
        res.status(400).json({ error: 'Invalid or missing session ID' });
        return;
      }
      
      const transport = this.sseTransports.get(sessionId)!;
      
      try {
        await transport.handlePostMessage(req, res, req.body);
      } catch (error) {
        console.error('Error handling POST message:', error);
        res.status(500).json({ error: 'Failed to process message' });
      }
    });
    
    this.expressApp.get('/', (_req, res) => {
      res.send(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Enhanced AutoGen MCP Server</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
            h1 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
            .feature { margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #007acc; }
            .endpoint { background: #e9ecef; padding: 10px; border-radius: 4px; margin: 10px 0; }
            code { background: #f1f3f4; padding: 2px 6px; border-radius: 3px; }
            .status { color: #28a745; font-weight: bold; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>🚀 Enhanced AutoGen MCP Server</h1>
            <p class="status">✅ Server running with SSE support!</p>
            
            <div class="feature">
              <h3>🔗 SSE Connection</h3>
              <div class="endpoint">GET <code>/sse?sessionId=your-session-id</code></div>
              <p>Establish Server-Sent Events connection for real-time updates</p>
            </div>
            
            <div class="feature">
              <h3>📨 Message Endpoint</h3>
              <div class="endpoint">POST <code>/message?sessionId=your-session-id</code></div>
              <p>Send MCP messages to the server</p>
            </div>
            
            <div class="feature">
              <h3>🩺 Health Check</h3>
              <div class="endpoint">GET <code>/health</code></div>
              <p>Server health and metrics</p>
            </div>
            
            <div class="feature">
              <h3>✨ Enhanced Features</h3>
              <ul>
                <li>🌊 Real-time streaming with SSE</li>
                <li>📡 Resource subscriptions</li>
                <li>📊 Progress notifications</li>
                <li>🤖 Advanced agent workflows</li>
                <li>🔄 Dynamic templates</li>
                <li>📈 Performance monitoring</li>
              </ul>
            </div>
            
            <p><em>Running on port ${port} - ${new Date().toISOString()}</em></p>
          </div>
        </body>
        </html>
      `);
    });
    
    this.httpServer = createServer(this.expressApp);
    
    this.httpServer.listen(port, host, () => {
      console.error(`🚀 Enhanced AutoGen MCP Server with SSE running on http://${host}:${port}`);
      console.error(`📡 SSE: http://${host}:${port}/sse`);
      console.error(`📨 Messages: http://${host}:${port}/message`);
      console.error(`🩺 Health: http://${host}:${port}/health`);
    });
  }
}

function parseArgs(): TransportConfig {
  const args = process.argv.slice(2);
  const config: TransportConfig = { type: 'stdio' };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--transport' && i + 1 < args.length) {
      const transport = args[i + 1];
      if (transport === 'sse' || transport === 'stdio') {
        config.type = transport;
      }
      i++;
    } else if (arg === '--port' && i + 1 < args.length) {
      config.port = parseInt(args[i + 1], 10);
      i++;
    } else if (arg === '--host' && i + 1 < args.length) {
      config.host = args[i + 1];
      i++;
    }
  }
  
  return config;
}

async function main() {
  const config = parseArgs();
  const server = new EnhancedAutoGenServer();
  
  try {
    if (config.type === 'sse') {
      const port = config.port || 3000;
      const host = config.host || 'localhost';
      await server.runWithSSE({ port, host });
    } else {
      await server.runWithStdio();
    }
  } catch (error) {
    console.error('Failed to start Enhanced AutoGen MCP Server:', error);
    process.exit(1);
  }
}

main().catch(console.error);
