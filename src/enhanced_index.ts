#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express, { Request, Response } from "express";
import cors from "cors";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { z } from "zod";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 8081;

// CORS configuration for browser-based MCP clients
app.use(cors({
  origin: '*', // Configure appropriately for production
  exposedHeaders: ['Mcp-Session-Id', 'mcp-protocol-version'],
  allowedHeaders: ['Content-Type', 'mcp-session-id'],
}));

app.use(express.json());

// Define session configuration schema
export const configSchema = z.object({
  openaiApiKey: z.string().optional().describe("OpenAI API key for LLM usage"),
  pythonPath: z.string().optional().default("python").describe("Path to Python executable"),
  workingDirectory: z.string().optional().default("./workspace").describe("Working directory for code execution"),
  enableStreaming: z.boolean().optional().default(true).describe("Enable streaming responses"),
  maxAgents: z.number().optional().default(10).describe("Maximum number of concurrent agents"),
});

// Parse configuration from query parameters
function parseConfig(req: Request) {
  const configParam = req.query.config as string;
  if (configParam) {
    return JSON.parse(Buffer.from(configParam, 'base64').toString());
  }
  return {};
}

function validateServerAccess(apiKey?: string): boolean {
  // Validate API key - accepts any non-empty string for demo
  // In production, implement proper validation
  return apiKey !== undefined && apiKey.trim().length > 0;
}

// Create MCP server with AutoGen tools
export default function createServer({
  config,
}: {
  config: z.infer<typeof configSchema>;
}) {
  const server = new McpServer({
    name: "Enhanced AutoGen MCP",
    version: "0.3.0",
  });

  // Enhanced tool for creating AutoGen agents using latest standards
  server.registerTool("create_autogen_agent", {
    description: "Create a new AutoGen agent using the latest Core architecture",
    inputSchema: {
      name: z.string().describe("Unique name for the agent"),
      type: z.enum(["assistant", "user_proxy", "conversable", "workbench"]).describe("Type of agent to create"),
      system_message: z.string().optional().describe("System message for the agent"),
      model_client: z.object({
        model: z.string().default("gpt-4o"),
        base_url: z.string().optional(),
        api_key: z.string().optional(),
      }).optional().describe("Model client configuration"),
      tools: z.array(z.string()).optional().describe("List of tools to enable"),
      streaming: z.boolean().optional().default(true).describe("Enable streaming responses"),
    },
  },
    async ({ name, type, system_message, model_client, tools, streaming }) => {
      // Validate server access
      if (!validateServerAccess(config.openaiApiKey)) {
        throw new Error("Server access validation failed. Please provide a valid OpenAI API key.");
      }

      try {
        const agentConfig = {
          name,
          type,
          system_message: system_message || "You are a helpful AI assistant using AutoGen Core.",
          model_client: {
            model: model_client?.model || "gpt-4o",
            api_key: config.openaiApiKey,
            ...model_client,
          },
          tools: tools || [],
          streaming: streaming ?? true,
        };

        const result = await callPythonHandler("create_agent", agentConfig);

        return {
          content: [
            { 
              type: "text", 
              text: `Successfully created AutoGen agent '${name}' of type '${type}' using latest Core architecture.\n\nConfiguration:\n${JSON.stringify(agentConfig, null, 2)}\n\nResult:\n${JSON.stringify(result, null, 2)}` 
            }
          ],
        };
      } catch (error) {
        throw new Error(`Failed to create agent: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  );

  // Enhanced workflow execution with streaming
  server.registerTool("execute_autogen_workflow", {
    description: "Execute a multi-agent workflow using latest AutoGen patterns",
    inputSchema: {
      workflow_type: z.enum(["sequential", "group_chat", "handoffs", "mixture_of_agents", "reflection"]).describe("Type of workflow pattern"),
      agents: z.array(z.object({
        name: z.string(),
        type: z.string(),
        role: z.string().optional(),
      })).describe("Agents to include in the workflow"),
      task: z.string().describe("Task description for the workflow"),
      max_rounds: z.number().optional().default(10).describe("Maximum conversation rounds"),
      streaming: z.boolean().optional().default(true).describe("Enable streaming responses"),
    },
  },
    async ({ workflow_type, agents, task, max_rounds, streaming }) => {
      if (!validateServerAccess(config.openaiApiKey)) {
        throw new Error("Server access validation failed. Please provide a valid OpenAI API key.");
      }

      try {
        const workflowConfig = {
          workflow_type,
          agents,
          task,
          max_rounds: max_rounds || 10,
          streaming: streaming ?? true,
          api_key: config.openaiApiKey,
        };

        const result = await callPythonHandler("execute_workflow", workflowConfig);

        return {
          content: [
            { 
              type: "text", 
              text: `Workflow '${workflow_type}' executed successfully!\n\nTask: ${task}\n\nAgents: ${agents.map(a => a.name).join(', ')}\n\nResult:\n${JSON.stringify(result, null, 2)}` 
            }
          ],
        };
      } catch (error) {
        throw new Error(`Failed to execute workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  );

  // MCP Workbench integration tool
  server.registerTool("create_mcp_workbench", {
    description: "Create an AutoGen workbench with MCP server integration",
    inputSchema: {
      mcp_servers: z.array(z.object({
        name: z.string(),
        command: z.string(),
        args: z.array(z.string()).optional(),
        env: z.record(z.string()).optional(),
      })).describe("MCP servers to integrate"),
      agent_name: z.string().describe("Name of the workbench agent"),
      model: z.string().optional().default("gpt-4o").describe("Model to use"),
    },
  },
    async ({ mcp_servers, agent_name, model }) => {
      if (!validateServerAccess(config.openaiApiKey)) {
        throw new Error("Server access validation failed. Please provide a valid OpenAI API key.");
      }

      try {
        const workbenchConfig = {
          mcp_servers,
          agent_name,
          model: model || "gpt-4o",
          api_key: config.openaiApiKey,
        };

        const result = await callPythonHandler("create_mcp_workbench", workbenchConfig);

        return {
          content: [
            { 
              type: "text", 
              text: `MCP Workbench '${agent_name}' created successfully!\n\nIntegrated MCP Servers: ${mcp_servers.map(s => s.name).join(', ')}\n\nResult:\n${JSON.stringify(result, null, 2)}` 
            }
          ],
        };
      } catch (error) {
        throw new Error(`Failed to create MCP workbench: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  );

  // Enhanced agent status tool
  server.registerTool("get_agent_status", {
    description: "Get detailed status and metrics for AutoGen agents",
    inputSchema: {
      agent_name: z.string().optional().describe("Specific agent name (optional)"),
      include_metrics: z.boolean().optional().default(true).describe("Include performance metrics"),
      include_memory: z.boolean().optional().default(true).describe("Include memory information"),
    },
  },
    async ({ agent_name, include_metrics, include_memory }) => {
      try {
        const statusConfig = {
          agent_name,
          include_metrics: include_metrics ?? true,
          include_memory: include_memory ?? true,
        };

        const result = await callPythonHandler("get_agent_status", statusConfig);

        return {
          content: [
            { 
              type: "text", 
              text: `Agent Status Report:\n\n${JSON.stringify(result, null, 2)}` 
            }
          ],
        };
      } catch (error) {
        throw new Error(`Failed to get agent status: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  );

  // Tool for managing agent memory and teachability
  server.registerTool("manage_agent_memory", {
    description: "Manage agent memory and teachability features",
    inputSchema: {
      agent_name: z.string().describe("Name of the agent"),
      action: z.enum(["save", "load", "clear", "query", "teach"]).describe("Memory action to perform"),
      data: z.any().optional().describe("Data for the action"),
      query: z.string().optional().describe("Query string for memory search"),
    },
  },
    async ({ agent_name, action, data, query }) => {
      try {
        const memoryConfig = {
          agent_name,
          action,
          data,
          query,
        };

        const result = await callPythonHandler("manage_agent_memory", memoryConfig);

        return {
          content: [
            { 
              type: "text", 
              text: `Memory action '${action}' for agent '${agent_name}':\n\n${JSON.stringify(result, null, 2)}` 
            }
          ],
        };
      } catch (error) {
        throw new Error(`Failed to manage agent memory: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
  );

  return server.server;
}

// Python handler function
async function callPythonHandler(toolName: string, args: any = {}): Promise<any> {
  const scriptPath = join(__dirname, 'autogen_mcp', 'server.py');
  const pythonPath = process.env.PYTHON_PATH || 'python';
  const pythonArgs = [scriptPath, toolName, JSON.stringify(args)];

  return new Promise((resolve, reject) => {
    const pythonProcess = spawn(pythonPath, pythonArgs);
    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || 'Python process failed'));
        return;
      }

      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (error) {
        reject(new Error('Invalid JSON response from Python'));
      }
    });

    pythonProcess.on('error', (error) => {
      reject(new Error(error.message));
    });
  });
}

// Handle MCP requests at /mcp endpoint
app.all('/mcp', async (req: Request, res: Response) => {
  try {
    // Parse configuration
    const rawConfig = parseConfig(req);
    
    // Validate and parse configuration
    const config = configSchema.parse({
      openaiApiKey: rawConfig.openaiApiKey || process.env.OPENAI_API_KEY || undefined,
      pythonPath: rawConfig.pythonPath || process.env.PYTHON_PATH || "python",
      workingDirectory: rawConfig.workingDirectory || "./workspace",
      enableStreaming: rawConfig.enableStreaming ?? true,
      maxAgents: rawConfig.maxAgents || 10,
    });
    
    const server = createServer({ config });
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
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    name: 'Enhanced AutoGen MCP Server',
    version: '0.3.0',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memoryUsage: process.memoryUsage(),
  });
});

// Main function to start the server in the appropriate mode
async function main() {
  // Parse command line arguments
  const args = process.argv.slice(2);
  const transportArg = args.find(arg => arg.includes('--transport'));
  const portArg = args.find(arg => arg.includes('--port'));
  
  const transport = transportArg ? transportArg.split('=')[1] : process.env.TRANSPORT || 'stdio';
  const port = portArg ? parseInt(portArg.split('=')[1]) : parseInt(process.env.PORT || '3001');
  
  if (transport === 'http') {
    // Run in HTTP mode
    app.listen(port, () => {
      console.log(`Enhanced AutoGen MCP Server listening on port ${port}`);
      console.log(`HTTP endpoint: http://localhost:${port}/mcp`);
      console.log(`Health check: http://localhost:${port}/health`);
    });
  } else {
    // Optional: if you need backward compatibility, add stdio transport
    const openaiApiKey = process.env.OPENAI_API_KEY;
    const pythonPath = process.env.PYTHON_PATH || "python";
    const enableStreaming = process.env.ENABLE_STREAMING !== 'false';

    // Create server with configuration
    const server = createServer({
      config: {
        openaiApiKey,
        pythonPath,
        workingDirectory: "./workspace",
        enableStreaming,
        maxAgents: 10,
      },
    });

    // Start receiving messages on stdin and sending messages on stdout
    const stdioTransport = new StdioServerTransport();
    await server.connect(stdioTransport);
    console.error("Enhanced AutoGen MCP Server running in stdio mode");
  }
}

// Start the server
main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
