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
  SubscribeRequestSchema,
  UnsubscribeRequestSchema,
  ResourceUpdatedNotificationSchema,
  PromptListChangedNotificationSchema,
  ToolListChangedNotificationSchema,
  ProgressNotificationSchema,
  LoggingLevelSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import express, { Application, Request, Response } from 'express';
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
  private pythonPath: string;  private expressApp?: Application;
  private httpServer?: ReturnType<typeof createServer>;
  private sseTransports: Map<string, SSEServerTransport> = new Map();
  private subscribers: Set<string> = new Set();
  private progressTokens: Map<string, string> = new Map();
  private lastResourceUpdate: number = Date.now();
  private lastPromptUpdate: number = Date.now();
  private lastToolUpdate: number = Date.now();

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
        instructions: 'Enhanced AutoGen MCP Server with SSE support, real-time updates, and comprehensive MCP protocol implementation including streaming, subscriptions, progress notifications, and advanced workflow management.',
      }
    );

    this.pythonPath = process.env.PYTHON_PATH || 'python';

    // Set up request handlers
    this.setupHandlers();

    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      await this.cleanup();
      process.exit(0);
    });
    process.on('SIGTERM', async () => {
      await this.cleanup();
      process.exit(0);
    });
  }

  private async cleanup(): Promise<void> {
    console.error('Shutting down Enhanced AutoGen MCP Server...');
    
    // Close all SSE transports
    for (const transport of this.sseTransports.values()) {
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
    // Enhanced prompts with all capabilities
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
          {
            name: 'quality_checks',
            description: 'Enable multi-stage quality validation',
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
            description: 'Programming language (auto-detected if not specified)',
            required: false,
          },
          {
            name: 'focus_areas',
            description: 'Specific areas to focus on (security, performance, readability, testing)',
            required: false,
          },
          {
            name: 'severity_level',
            description: 'Review severity (basic, thorough, comprehensive)',
            required: false,
          },
          {
            name: 'live_feedback',
            description: 'Enable real-time streaming feedback',
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
            description: 'Analysis depth (basic, detailed, comprehensive, exhaustive)',
            required: false,
          },
          {
            name: 'sources',
            description: 'Preferred research sources',
            required: false,
          },
          {
            name: 'output_format',
            description: 'Output format (report, presentation, analysis, summary)',
            required: false,
          },
          {
            name: 'real_time_updates',
            description: 'Enable streaming progress updates',
            required: false,
          },
        ],
      },
      'creative-collaboration': {
        name: 'creative-collaboration',
        description: 'Set up creative agents for collaborative content generation',
        arguments: [
          {
            name: 'project_type',
            description: 'Type of creative project (story, article, script, marketing)',
            required: true,
          },
          {
            name: 'tone',
            description: 'Desired tone and style',
            required: false,
          },
          {
            name: 'target_audience',
            description: 'Target audience description',
            required: false,
          },
          {
            name: 'length',
            description: 'Desired length or scope',
            required: false,
          },
          {
            name: 'collaborative_editing',
            description: 'Enable real-time collaborative editing',
            required: false,
          },
        ],
      },
      'problem-solving': {
        name: 'problem-solving',
        description: 'Create a problem-solving team with specialized agents',
        arguments: [
          {
            name: 'problem_statement',
            description: 'Clear description of the problem to solve',
            required: true,
          },
          {
            name: 'domain',
            description: 'Problem domain (technical, business, creative, analytical)',
            required: false,
          },
          {
            name: 'constraints',
            description: 'Any constraints or limitations',
            required: false,
          },
          {
            name: 'solution_format',
            description: 'Desired solution format',
            required: false,
          },
          {
            name: 'brainstorming_mode',
            description: 'Enable real-time brainstorming with live updates',
            required: false,
          },
        ],
      },
    };

    // Enhanced resource templates
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
      'conversation-stream': {
        uriTemplate: 'autogen://conversations/{conversation_id}/stream',
        name: 'Conversation Stream',
        description: 'Live conversation updates and message flow',
        mimeType: 'text/event-stream',
      },
      'agent-memory': {
        uriTemplate: 'autogen://agents/{agent_id}/memory',
        name: 'Agent Memory State',
        description: 'Current memory and knowledge state of agents',
        mimeType: 'application/json',
      },
      'system-metrics': {
        uriTemplate: 'autogen://system/metrics',
        name: 'System Metrics',
        description: 'Real-time system performance and resource usage',
        mimeType: 'application/json',
      },
    };

    // List available prompts
    this.server.setRequestHandler(ListPromptsRequestSchema, async () => ({
      prompts: Object.values(PROMPTS),
    }));

    // Get specific prompt with enhanced template generation
    this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {
      const promptName = request.params.name;
      const args = request.params.arguments || {};

      if (promptName === 'autogen-workflow') {
        const taskDescription = args.task_description;
        const agentCount = args.agent_count || '3';        const workflowType = args.workflow_type || 'group_chat';
        const streaming = args.streaming === 'true' || Boolean(args.streaming);
        const qualityChecks = args.quality_checks === 'true' || Boolean(args.quality_checks);
        
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
- Quality Validation: ${qualityChecks ? 'enabled' : 'disabled'}

Requirements:
1. Create distinct agents with specialized roles and expertise
2. Configure intelligent agent interactions and routing
3. Set up workflow execution with error handling
4. ${streaming ? 'Enable real-time progress streaming' : 'Use standard execution mode'}
5. ${qualityChecks ? 'Implement multi-stage quality validation' : 'Use basic validation'}

Please provide a complete workflow configuration with agent definitions, interaction patterns, and execution flow.`,
              },
            },
          ],
        };
      }

      // Similar implementations for other prompts...
      throw new McpError(ErrorCode.InvalidRequest, `Unknown prompt: ${promptName}`);
    });

    // List available resources with enhanced capabilities
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: 'autogen://agents/list',
          name: 'Active Agents Registry',
          description: 'Real-time list of all active AutoGen agents with status and capabilities',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://workflows/templates',
          name: 'Workflow Templates Library',
          description: 'Comprehensive collection of workflow templates and configurations',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://conversations/active',
          name: 'Active Conversations',
          description: 'Currently running conversations and their real-time status',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://system/metrics',
          name: 'System Performance Metrics',
          description: 'Real-time system performance, resource usage, and health metrics',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://config/current',
          name: 'Current Configuration',
          description: 'Current server configuration and capability settings',
          mimeType: 'application/json',
        },
        {
          uri: 'autogen://subscriptions/list',
          name: 'Active Subscriptions',
          description: 'List of active resource subscriptions and their status',
          mimeType: 'application/json',
        },
      ],
    }));    // Enhanced resource reading with real-time data
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
          performance: {
            eventLoopDelay: process.hrtime(),
            cpuUsage: process.cpuUsage(),
          },
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

      // Delegate other resources to Python handler
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
    });    // Resource subscription management
    this.server.setRequestHandler(SubscribeRequestSchema, async (request) => {
      const uri = request.params.uri;
      this.subscribers.add(uri);
      
      // Send immediate update for subscribed resource
      await this.notifyResourceUpdate(uri);
      
      return {};
    });

    this.server.setRequestHandler(UnsubscribeRequestSchema, async (request) => {
      const uri = request.params.uri;
      this.subscribers.delete(uri);
      return {};
    });

    // Enhanced tools with progress tracking
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_streaming_workflow',
          description: 'Create a workflow with real-time streaming and progress updates',
          inputSchema: {
            type: 'object',
            properties: {
              workflow_name: { type: 'string', description: 'Name for the workflow' },
              workflow_type: { type: 'string', description: 'Type of workflow (sequential, group_chat, hierarchical, swarm, streaming)' },
              agents: { type: 'array', description: 'List of agent configurations' },
              streaming_config: { type: 'object', description: 'Streaming configuration and settings' },
              progress_token: { type: 'string', description: 'Token for progress notifications' },
              quality_gates: { type: 'boolean', description: 'Enable quality validation checkpoints' },
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
              max_turns: { type: 'number', description: 'Maximum conversation turns' },
              session_id: { type: 'string', description: 'Session identifier for tracking' },
            },
            required: ['agent_name', 'message'],
          },
        },
        {
          name: 'broadcast_resource_update',
          description: 'Broadcast a resource update to all subscribers',
          inputSchema: {
            type: 'object',
            properties: {
              uri: { type: 'string', description: 'Resource URI that was updated' },
              change_type: { type: 'string', description: 'Type of change (created, updated, deleted)' },
              data: { type: 'object', description: 'Updated resource data' },
            },
            required: ['uri', 'change_type'],
          },
        },
        // Include all original tools
        {
          name: 'create_agent',
          description: 'Create a new AutoGen agent with enhanced capabilities',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Unique name for the agent' },
              type: { type: 'string', description: 'Agent type (assistant, user_proxy, conversable, teachable, retrievable)' },
              system_message: { type: 'string', description: 'System message defining agent behavior' },
              llm_config: { type: 'object', description: 'LLM configuration for the agent' },
              streaming: { type: 'boolean', description: 'Enable real-time streaming for this agent' },
              progress_token: { type: 'string', description: 'Token for progress notifications' },
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
              workflow_name: { type: 'string', description: 'Name of the workflow to execute' },
              input_data: { type: 'object', description: 'Input data for the workflow' },
              streaming: { type: 'boolean', description: 'Enable real-time streaming' },
              progress_token: { type: 'string', description: 'Token for progress notifications' },
              output_format: { type: 'string', description: 'Desired output format' },
              quality_checks: { type: 'boolean', description: 'Enable quality validation' },
            },
            required: ['workflow_name', 'input_data'],
          },
        },
      ],
    }));    // Enhanced tool call handling with progress notifications
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const args = request.params.arguments || {};
      const progressToken = args.progress_token as string | undefined;

      try {
        // Send initial progress notification
        if (progressToken) {
          this.progressTokens.set(progressToken, toolName);
          await this.sendProgressNotification(progressToken, 0, `Starting ${toolName}...`);
        }

        // Handle streaming-specific tools
        if (toolName === 'create_streaming_workflow' || toolName === 'start_streaming_chat') {
          return await this.handleStreamingTool(toolName, args, progressToken);
        }

        if (toolName === 'broadcast_resource_update') {
          return await this.handleResourceBroadcast(args);
        }

        // Send progress update
        if (progressToken) {
          await this.sendProgressNotification(progressToken, 50, `Processing ${toolName}...`);
        }

        // Call Python handler for other tools
        const result = await this.callPythonHandler(toolName, args);

        // Send completion notification
        if (progressToken) {
          await this.sendProgressNotification(progressToken, 100, `Completed ${toolName}`);
          this.progressTokens.delete(progressToken);
        }

        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        if (progressToken) {
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
      // Send streaming updates to connected clients
      for (const transport of this.sseTransports.values()) {
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
      }
    }

    if (progressToken) {
      await this.sendProgressNotification(progressToken, 100, 'Streaming completed');
    }

    return result;
  }

  private async handleResourceBroadcast(args: any): Promise<any> {
    const { uri, change_type, data } = args;
    
    await this.notifyResourceUpdate(uri, data);
    this.lastResourceUpdate = Date.now();
    
    return {
      success: true,
      uri,
      change_type,
      subscribers: this.subscribers.size,
      timestamp: new Date().toISOString(),
    };
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
              data: data || await this.getResourceData(uri),
              timestamp: new Date().toISOString(),
            },
          });
        } catch (error) {
          console.error('Error sending resource update notification:', error);
        }
      }
    }
  }
  private async getResourceData(uri: string): Promise<any> {
    try {
      // For system metrics, return directly
      if (uri === 'autogen://system/metrics') {
        return {
          timestamp: new Date().toISOString(),
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          sseConnections: this.sseTransports.size,
          activeSubscriptions: this.subscribers.size,
          progressTokens: this.progressTokens.size,
        };
      }
      
      // For other resources, delegate to Python handler
      const result = await this.callPythonHandler('get_resource', { uri });
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return { error: errorMessage };
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
    
    // Security middleware
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
    
    // CORS configuration
    this.expressApp.use(cors({
      origin: true,
      credentials: true,
      methods: ['GET', 'POST', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization'],
    }));
    
    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 1000, // limit each IP to 1000 requests per windowMs
      message: 'Too many requests from this IP',
    });
    this.expressApp.use(limiter);
    
    this.expressApp.use(express.json({ limit: '10mb' }));
    
    // Health check endpoint
    this.expressApp.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        sseConnections: this.sseTransports.size,
        subscriptions: this.subscribers.size,
        memoryUsage: process.memoryUsage(),
      });
    });
    
    // SSE endpoint for MCP communication
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
      // POST endpoint for MCP messages
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
    
    // Static homepage
    this.expressApp.get('/', (req, res) => {
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

// CLI argument parsing
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

// Main execution
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
