#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  SubscribeRequestSchema,
  UnsubscribeRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import express, { Application, Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createServer as createHttpServer } from 'http';
import { z } from 'zod';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface TransportConfig {
  type: 'stdio' | 'sse' | 'http';
  port?: number;
  host?: string;
}

// Define session configuration schema
export const configSchema = z.object({
  serverToken: z.string().optional().describe("Server access token"),
  caseSensitive: z.boolean().optional().default(false).describe("Whether character matching should be case sensitive"),
});

// Parse configuration from query parameters
function parseConfig(req: Request) {
  const configParam = req.query.config as string;
  if (configParam) {
    return JSON.parse(Buffer.from(configParam, 'base64').toString());
  }
  return {};
}

function validateServerAccess(serverToken?: string): boolean {
  // Validate server token - accepts any string including empty ones for demo
  // In a real app, you'd validate against your server's auth system
  return serverToken !== undefined && serverToken.trim().length > 0 ? true : true;
}

class EnhancedAutoGenServer {
  private server: Server;
  private pythonPath: string;
  private expressApp?: Application;
  private httpServer?: ReturnType<typeof createHttpServer>;  private sseTransports: Map<string, SSEServerTransport> = new Map();
  private subscribers: Set<string> = new Set();
  private progressTokens: Map<string, string> = new Map();
  private lastResourceUpdate?: Date;
  private lastPromptUpdate?: Date;
  private lastToolUpdate?: Date;

  constructor() {
    this.server = new Server(
      {
        name: 'enhanced-autogen-mcp',
        version: '0.2.0',
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
        instructions: `Enhanced AutoGen MCP Server with SSE support and all latest features.
        
Features:
- Real-time streaming with SSE
- Progress notifications
- Resource subscriptions  
- Advanced workflows
- Multi-agent conversations
- Template management
- Comprehensive logging

Use tools to create agents, execute workflows, and manage conversations.
Subscribe to resources for real-time updates.`,
      }
    );

    this.pythonPath = process.env.PYTHON_PATH || 'python';
    this.setupHandlers();
    this.setupErrorHandling();
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.cleanup();
      process.exit(0);
    });
  }

  private async cleanup(): Promise<void> {
    // Close all SSE transports
    const transports = Array.from(this.sseTransports.values());
    for (const transport of transports) {
      await transport.close();
    }
    this.sseTransports.clear();

    // Close HTTP server
    if (this.httpServer) {
      this.httpServer.close();
    }

    // Close MCP server
    await this.server.close();
  }

  private setupHandlers(): void {
    // Define enhanced prompts
    const PROMPTS = {
      'autogen-workflow': {
        name: 'autogen-workflow',
        description: 'Create a sophisticated multi-agent AutoGen workflow',
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
            description: 'Enable real-time streaming of results',
            required: false,
          },
        ],
      },
      'code-review': {
        name: 'code-review',
        description: 'Set up agents for comprehensive collaborative code review',
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
            name: 'focus_areas',
            description: 'Specific areas to focus on',
            required: false,
          },
        ],
      },
      'research-analysis': {
        name: 'research-analysis',
        description: 'Create advanced research and analysis workflow',
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

    // Enhanced prompt handlers
    this.server.setRequestHandler(ListPromptsRequestSchema, async () => ({
      prompts: Object.values(PROMPTS),
    }));

    this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {
      const promptName = request.params.name;
      const args = request.params.arguments || {};

      if (promptName === 'autogen-workflow') {
        const taskDescription = args.task_description as string;
        const agentCount = (args.agent_count as string) || '3';
        const workflowType = (args.workflow_type as string) || 'group_chat';
        const streaming = String(args.streaming) === 'true';
        
        return {
          messages: [
            {
              role: 'user' as const,
              content: {
                type: 'text' as const,
                text: `Create an enhanced AutoGen workflow for: ${taskDescription}

Configuration:
- Agent count: ${agentCount}
- Workflow type: ${workflowType}
- Streaming: ${streaming ? 'enabled' : 'disabled'}

Create specialized agents with distinct roles and configure advanced interactions.`,
              },
            },
          ],
        };
      }

      if (promptName === 'code-review') {
        const code = args.code as string;
        const language = (args.language as string) || 'auto-detect';
        const focusAreas = (args.focus_areas as string) || 'all areas';
        
        return {
          messages: [
            {
              role: 'user' as const,
              content: {
                type: 'text' as const,
                text: `Perform code review for:

\`\`\`${language}
${code}
\`\`\`

Focus areas: ${focusAreas}

Set up specialized reviewer agents for comprehensive analysis.`,
              },
            },
          ],
        };
      }

      if (promptName === 'research-analysis') {
        const topic = args.topic as string;
        const depth = (args.depth as string) || 'detailed';
        
        return {
          messages: [
            {
              role: 'user' as const,
              content: {
                type: 'text' as const,
                text: `Create ${depth} research and analysis for: ${topic}

Deploy specialized research agents for comprehensive coverage.`,
              },
            },
          ],
        };
      }

      throw new McpError(ErrorCode.InvalidRequest, `Unknown prompt: ${promptName}`);
    });

    // Enhanced resource handlers
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: 'autogen://agents/list',
          name: 'Active Agents',
          description: 'List of currently active AutoGen agents',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://workflows/templates',
          name: 'Workflow Templates',
          description: 'Available workflow templates',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://chat/history',
          name: 'Chat History',
          description: 'Recent agent conversation history',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://config/current',
          name: 'Current Configuration',
          description: 'Current AutoGen configuration settings',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://progress/status',
          name: 'Progress Status',
          description: 'Real-time progress of running tasks',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://metrics/performance',
          name: 'Performance Metrics',
          description: 'Server performance statistics',
          mimeType: 'application/json',
        },
      ],
    }));

    // Resource subscription handlers
    this.server.setRequestHandler(SubscribeRequestSchema, async (request) => {
      const uri = request.params.uri;
      this.subscribers.add(uri);
      return { success: true };
    });

    this.server.setRequestHandler(UnsubscribeRequestSchema, async (request) => {
      const uri = request.params.uri;
      this.subscribers.delete(uri);
      return { success: true };
    });

    // Enhanced resource reading
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const uri = request.params.uri;
      return this.handleResourceDirectly(uri);
    });

    // Tool definitions
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_streaming_workflow',
          description: 'Create a workflow with real-time streaming',
          inputSchema: {
            type: 'object',
            properties: {
              workflow_name: { type: 'string', description: 'Name for the workflow' },
              workflow_type: { type: 'string', description: 'Type of workflow' },
              agents: { type: 'array', description: 'List of agent configurations' },
              streaming: { type: 'boolean', description: 'Enable streaming' },
            },
            required: ['workflow_name', 'workflow_type', 'agents'],
          },
        },
        {
          name: 'start_streaming_chat',
          description: 'Start a streaming chat session',
          inputSchema: {
            type: 'object',
            properties: {
              agent_name: { type: 'string', description: 'Name of the agent' },
              message: { type: 'string', description: 'Initial message' },
              streaming: { type: 'boolean', description: 'Enable streaming' },
            },
            required: ['agent_name', 'message'],
          },
        },
        {
          name: 'create_agent',
          description: 'Create a new AutoGen agent',
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

    // Tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const args = request.params.arguments || {};
      const progressToken = request.params._meta?.progressToken;

      try {
        // Handle progress token
        if (progressToken && typeof progressToken === 'string') {
          this.progressTokens.set(progressToken, toolName);
          await this.sendProgressNotification(progressToken, 0, `Starting ${toolName}...`);
        }

        // Handle streaming tools
        if (toolName === 'create_streaming_workflow' || toolName === 'start_streaming_chat') {
          if (progressToken && typeof progressToken === 'string') {
            return await this.handleStreamingTool(toolName, args, progressToken);
          }
        }

        // Regular tool handling
        if (progressToken && typeof progressToken === 'string') {
          await this.sendProgressNotification(progressToken, 50, `Processing ${toolName}...`);
        }

        const result = await this.callPythonHandler(toolName, args);

        // Complete progress
        if (progressToken && typeof progressToken === 'string') {
          await this.sendProgressNotification(progressToken, 100, `Completed ${toolName}`);
          this.progressTokens.delete(progressToken);
        }

        return result;
      } catch (error) {
        if (progressToken && typeof progressToken === 'string') {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          await this.sendProgressNotification(progressToken, -1, `Error in ${toolName}: ${errorMessage}`);
          this.progressTokens.delete(progressToken);
        }
        throw error;
      }
    });
  }

  private async handleResourceDirectly(uri: string): Promise<any> {
    if (uri === 'autogen://agents/list') {
      try {
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
      } catch (error) {
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify({ error: 'Failed to fetch agents' }, null, 2),
            },
          ],
        };
      }
    }

    if (uri === 'autogen://progress/status') {
      const progressData = {
        active_tasks: Array.from(this.progressTokens.entries()).map(([token, tool]) => ({
          token,
          tool,
          timestamp: new Date().toISOString(),
        })),
        total_active: this.progressTokens.size,
        sse_connections: this.sseTransports.size,
      };

      return {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify(progressData, null, 2),
          },
        ],
      };
    }

    if (uri === 'autogen://metrics/performance') {
      const metrics = {
        uptime: process.uptime(),
        memory_usage: process.memoryUsage(),
        active_connections: this.sseTransports.size,
        subscribers: this.subscribers.size,
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

    // Fallback to Python handler
    try {
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
    } catch (error) {
      throw new McpError(ErrorCode.InvalidRequest, `Unknown resource: ${uri}`);
    }
  }

  private async handleStreamingTool(toolName: string, args: any, progressToken: string): Promise<any> {
    // Simulate streaming with progress updates
    const steps = 10;
    for (let i = 0; i <= steps; i++) {
      await this.sendProgressNotification(progressToken, (i / steps) * 100, `Step ${i}/${steps}`);
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Send streaming notifications to SSE clients
    const transports = Array.from(this.sseTransports.values());
    for (const transport of transports) {
      await transport.send({
        jsonrpc: '2.0',
        method: 'notifications/streaming_update',
        params: {
          tool: toolName,
          progress: 100,
          data: args,
        },
      });
    }

    return { streaming: true, completed: true, tool: toolName };
  }

  private async sendProgressNotification(token: string, progress: number, message: string): Promise<void> {
    const transports = Array.from(this.sseTransports.values());
    for (const transport of transports) {
      await transport.send({
        jsonrpc: '2.0',
        method: 'notifications/progress',
        params: {
          progressToken: token,
          progress,
          total: 100,
          message,
        },
      });
    }
  }

  private async sendResourceUpdateNotification(uri: string): Promise<void> {
    if (this.subscribers.has(uri)) {
      const transports = Array.from(this.sseTransports.values());
      for (const transport of transports) {
        await transport.send({
          jsonrpc: '2.0',
          method: 'notifications/resources/updated',
          params: { uri },
        });
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

  // SSE Transport setup
  async setupSSETransport(port: number = 3000, host: string = 'localhost'): Promise<void> {
    this.expressApp = express();
    
    // Security middleware
    this.expressApp.use(helmet());
    this.expressApp.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3001'],
      credentials: true,
    }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000,
      max: 100,
    });
    this.expressApp.use(limiter);

    this.expressApp.use(express.json({ limit: '10mb' }));
    this.expressApp.use(express.urlencoded({ extended: true }));    // SSE endpoint
    this.expressApp.get('/sse', async (req: Request, res: Response) => {
      try {
        const transport = new SSEServerTransport('/message', res);
        const sessionId = transport.sessionId;
        
        this.sseTransports.set(sessionId, transport);
        transport.onclose = () => {
          this.sseTransports.delete(sessionId);
        };

        await this.server.connect(transport);
      } catch (error) {
        console.error('SSE setup error:', error);
        if (!res.headersSent) {
          res.status(500).json({ error: 'Failed to setup SSE connection' });
        }
      }
    });

    // POST endpoint for MCP messages
    this.expressApp.post('/message', async (req: Request, res: Response) => {
      const sessionId = req.headers['x-session-id'] as string;
      const transport = this.sseTransports.get(sessionId);
      
      if (transport) {
        try {
          await transport.handlePostMessage(req, res, req.body);
        } catch (error) {
          console.error('Message handling error:', error);
          res.status(500).json({ error: 'Failed to handle message' });
        }
      } else {
        res.status(404).json({ error: 'Session not found' });
      }
    });

    // Health check endpoint
    this.expressApp.get('/', (req: Request, res: Response) => {
      res.json({
        name: 'Enhanced AutoGen MCP Server',
        version: '0.2.0',
        status: 'running',
        features: ['SSE', 'Streaming', 'Progress', 'Subscriptions'],
        connections: this.sseTransports.size,
        uptime: process.uptime(),
      });
    });

    // Start HTTP server
    this.httpServer = createHttpServer(this.expressApp);
    
    return new Promise((resolve, reject) => {      this.httpServer!.listen(port, host, () => {
        console.error(`🚀 Enhanced AutoGen MCP Server with SSE running on http://${host}:${port}`);
        console.error(`📡 SSE: http://${host}:${port}/sse`);
        console.error(`📨 Messages: http://${host}:${port}/message`);
        console.error(`🩺 Health: http://${host}:${port}/`);
        resolve();
      });

      this.httpServer!.on('error', reject);
    });
  }

  // HTTP Transport setup
  async setupHTTPTransport(port: number = 8081, host: string = 'localhost'): Promise<void> {
    this.expressApp = express();
    
    // CORS configuration for browser-based MCP clients
    this.expressApp.use(cors({
      origin: '*', // Configure appropriately for production
      exposedHeaders: ['Mcp-Session-Id', 'mcp-protocol-version'],
      allowedHeaders: ['Content-Type', 'mcp-session-id'],
    }));

    this.expressApp.use(express.json());

    // Handle MCP requests at /mcp endpoint
    this.expressApp.all('/mcp', async (req: Request, res: Response) => {
      try {
        // Parse configuration
        const rawConfig = parseConfig(req);
        
        // Validate and parse configuration
        const config = configSchema.parse({
          serverToken: rawConfig.serverToken || process.env.SERVER_TOKEN || undefined,
          caseSensitive: rawConfig.caseSensitive || false,
        });
        
        const server = createMCPServer({ config });
        const transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: undefined,
        });

        // Clean up on request close
        res.on('close', () => {
          transport.close();
          server.close();
        });

        await server.connect(transport);
        await transport.handleRequest(req, res, req.body);
      } catch (error) {
        console.error('Error handling MCP request:', error);
        if (!res.headersSent) {
          res.status(500).json({
            jsonrpc: '2.0',
            error: { code: -32603, message: 'Internal server error' },
            id: null,
          });
        }
      }
    });

    // Health check endpoint
    this.expressApp.get('/', (req: Request, res: Response) => {
      res.json({
        name: 'Enhanced AutoGen MCP Server',
        version: '0.2.0',
        status: 'running',
        features: ['HTTP', 'Streaming', 'Progress', 'Subscriptions'],
        uptime: process.uptime(),
      });
    });

    // Start HTTP server
    this.httpServer = createHttpServer(this.expressApp);
    
    return new Promise((resolve, reject) => {
      this.httpServer!.listen(port, host, () => {
        console.error(`🚀 Enhanced AutoGen MCP Server with HTTP running on http://${host}:${port}`);
        console.error(`📡 MCP: http://${host}:${port}/mcp`);
        console.error(`🩺 Health: http://${host}:${port}/`);
        resolve();
      });

      this.httpServer!.on('error', reject);
    });
  }

  async run(config: TransportConfig = { type: 'stdio' }): Promise<void> {
    if (config.type === 'http') {
      await this.setupHTTPTransport(config.port || parseInt(process.env.PORT || '8081'), config.host || 'localhost');
    } else if (config.type === 'sse') {
      await this.setupSSETransport(config.port || 3000, config.host || 'localhost');    } else {
      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      console.error('Enhanced AutoGen MCP server running on stdio');
    }
  }
}

// Create MCP server with your tools
export default function createMCPServer({
  config,
}: {
  config: z.infer<typeof configSchema>;
}) {
  const server = new Server(
    {
      name: "Enhanced AutoGen MCP Server",
      version: "0.2.0",
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
    }
  );

  // Example tool implementation - keeping the existing structure
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: "create_agent",
        description: "Create a new AutoGen agent with enhanced capabilities",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Unique name for the agent" },
            type: { type: "string", description: "Agent type" },
            system_message: { type: "string", description: "System message" },
            llm_config: { type: "object", description: "LLM configuration" },
          },
          required: ["name", "type"],
        },
      },
      // Add other tools as needed...
    ],
  }));

  // Add a simple tool handler as example
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === "create_agent") {
      // Validate server access
      if (!validateServerAccess(config.serverToken)) {
        throw new Error("Server access validation failed. Please provide a valid serverToken.");
      }
      
      return {
        content: [
          { 
            type: "text", 
            text: `Agent "${request.params.arguments?.name}" created successfully.` 
          }
        ],
      };
    }

    throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
  });

  return server;
}

// Main function to start the server in the appropriate mode
async function main() {
  const transport = process.env.TRANSPORT || 'stdio';
  
  if (transport === 'http') {
    // Run in HTTP mode
    const port = parseInt(process.env.PORT || '8081');
    const server = new EnhancedAutoGenServer();
    await server.run({ type: 'http', port });
  } else {
    // Optional: if you need backward compatibility, add stdio transport
    const serverToken = process.env.SERVER_TOKEN;
    const caseSensitive = process.env.CASE_SENSITIVE === 'true';

    // Create server with configuration
    const server = createMCPServer({
      config: {
        serverToken,
        caseSensitive,
      },
    });

    // Start receiving messages on stdin and sending messages on stdout
    const stdioTransport = new StdioServerTransport();
    await server.connect(stdioTransport);
    console.error("MCP Server running in stdio mode");
  }
}

// CLI argument parsing
function parseArgs(): TransportConfig {
  const args = process.argv.slice(2);
  const config: TransportConfig = { type: 'stdio' };

  console.error('Parsing args:', args);

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--transport' && args[i + 1]) {
      config.type = args[i + 1] as 'stdio' | 'sse' | 'http';
      console.error('Set transport to:', config.type);
      i++;
    } else if (args[i] === '--port' && args[i + 1]) {
      config.port = parseInt(args[i + 1], 10);
      console.error('Set port to:', config.port);
      i++;
    } else if (args[i] === '--host' && args[i + 1]) {
      config.host = args[i + 1];
      console.error('Set host to:', config.host);
      i++;
    }
  }

  console.error('Final config:', config);
  return config;
}

// Start the server based on environment or CLI args
if (process.env.TRANSPORT) {
  // Use environment variable mode (for main() function)
  main().catch((error) => {
    console.error("Server error:", error);
    process.exit(1);
  });
} else {
  // Use CLI argument mode (for legacy compatibility)
  const config = parseArgs();
  const server = new EnhancedAutoGenServer();
  server.run(config).catch(console.error);
}
