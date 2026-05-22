module.exports = {
  apps: [
    {
      name: "soquete",
      script: "main.py",
      interpreter: "/home/pablo/repos/soquete/.venv/bin/python3",
      cwd: "/home/pablo/repos/soquete",
      autorestart: true,
      watch: false,
      max_memory_restart: "128M",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
    },
  ],
};
