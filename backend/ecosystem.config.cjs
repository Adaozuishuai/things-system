module.exports = {
  apps: [
    {
      name: "api",
      cwd: "/home/system_/system_mvp/backend",
      script: "./venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8001",
      env: {}
    }
  ]
};
