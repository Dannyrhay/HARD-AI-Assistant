const {defineConfig}=require('@playwright/test');
module.exports=defineConfig({testDir:'tests',testMatch:'*.spec.cjs',workers:1,fullyParallel:false,timeout:30000,use:{baseURL:'http://127.0.0.1:5291',trace:'retain-on-failure'},webServer:{command:'".desktop-venv\\Scripts\\python.exe" tests/browser_server.py',url:'http://127.0.0.1:5291',reuseExistingServer:false,timeout:30000}});
