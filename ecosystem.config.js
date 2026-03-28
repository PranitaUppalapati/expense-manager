module.exports = {
  apps: [
    {
      name: "dashboard",
      cwd: "./dashboard",
      script: "npm",
      args: "run dev",
    },
    {
      name: "n8n",
      script: "n8n",
      args: "start",
      env: {
        NODE_FUNCTION_ALLOW_BUILTIN: "child_process,fs,path",
      },
    },
    {
      name: "fswatch-trigger",
      script: "/bin/bash",
      args: [
        "-c",
        "fswatch -o /Users/uppal1/Downloads/SBI_Debit_statements/statements | xargs -n1 -I{} curl -X POST http://localhost:5678/webhook/process-statement",
      ],
      autorestart: true,
    },
  ],
};
