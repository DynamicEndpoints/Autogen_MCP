#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class AutoGenServer {
  private server: Server;
  private pythonPath: string;

  constructor() {
    this.server = new Server(
      {
        name: 'autogen-mcp',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.pythonPath = process.env.PYTHON_PATH || 'python';

    // Set up request handlers
    this.setupHandlers();

    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_agent',
          description: 'Create a new AutoGen agent',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Agent name' },
              type: { type: 'string', enum: ['assistant', 'user'], description: 'Agent type' },
              description: { type: 'string', description: 'Agent description' },
              system_message: { type: 'string', description: 'System message for the agent' },
              llm_config: { type: 'object', description: 'LLM configuration' },
              code_execution_config: { type: 'object', description: 'Code execution settings' },
            },
            required: ['name', 'type'],
          },
        },
        {
          name: 'execute_chat',
          description: 'Execute a chat between two agents',
          inputSchema: {
            type: 'object',
            properties: {
              initiator: { type: 'string', description: 'Name of the initiating agent' },
              responder: { type: 'string', description: 'Name of the responding agent' },
              message: { type: 'string', description: 'Initial message' },
              llm_config: { type: 'object', description: 'Override default LLM settings' },
            },
            required: ['initiator', 'responder', 'message'],
          },
        },
        {
          name: 'execute_group_chat',
          description: 'Execute a group chat with multiple agents',
          inputSchema: {
            type: 'object',
            properties: {
              agent_names: { type: 'array', items: { type: 'string' }, description: 'List of agent names' },
              initiator: { type: 'string', description: 'Name of the initiating agent' },
              message: { type: 'string', description: 'Initial message' },
              max_round: { type: 'number', description: 'Maximum conversation rounds' },
              llm_config: { type: 'object', description: 'Override default LLM settings' },
            },
            required: ['agent_names', 'initiator', 'message'],
          },
        },
        {
          name: 'execute_workflow',
          description: 'Execute a predefined workflow',
          inputSchema: {
            type: 'object',
            properties: {
              workflow_name: { type: 'string', enum: ['code_generation', 'research'], description: 'Workflow to execute' },
              input_data: { type: 'object', description: 'Workflow-specific input data' },
              llm_config: { type: 'object', description: 'Override default LLM settings' },
            },
            required: ['workflow_name', 'input_data'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const scriptPath = join(__dirname, 'autogen_mcp', 'server.py');
      const args = [scriptPath, request.params.name, JSON.stringify(request.params.arguments)];

      return new Promise((resolve, reject) => {
        const process = spawn(this.pythonPath, args);
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
    });
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('AutoGen MCP server running on stdio');
  }
}

const server = new AutoGenServer();
server.run().catch(console.error);
