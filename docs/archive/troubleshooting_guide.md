# 🔧 reVoAgent Troubleshooting Guide

## 🚨 Common Issues & Solutions

### **Issue 1: "Cannot connect to backend" / CORS Errors**

**Symptoms:**
- Frontend shows "🔴 Disconnected" status
- Browser console shows CORS errors
- API requests failing

**Solutions:**
```bash
# 1. Check if backend is running
curl http://localhost:8000/health

# 2. If not running, start the backend
python3 simple_dev_server.py

# 3. Check ports are correct
# Backend should be on 8000, Frontend on 12000

# 4. Verify environment variables
cat .env | grep -E "(VITE_API_URL|VITE_WS_URL)"
# Should show:
# VITE_API_URL=http://localhost:8000
# VITE_WS_URL=ws://localhost:8000
```

**Fix:**
- Make sure backend is running on port 8000
- Verify frontend proxy configuration in `vite.config.ts`
- Check CORS settings in backend allow frontend port

---

### **Issue 2: Python Import Errors**

**Symptoms:**
```
ImportError: No module named 'packages.ai.enhanced_local_model_manager'
ModuleNotFoundError: No module named 'packages'
```

**Solutions:**
```bash
# 1. Run the Python path fix script
python3 fix_python_paths.py

# 2. Install minimal requirements
pip install -r requirements-minimal.txt

# 3. Use the simplified backend instead
python3 simple_dev_server.py

# 4. If issues persist, create __init__.py files manually
touch packages/__init__.py
touch packages/ai/__init__.py
touch packages/core/__init__.py
```

**Fix:**
- Use the simplified `simple_dev_server.py` instead of complex backend
- This avoids AI model dependencies for basic development

---

### **Issue 3: Frontend Build/Start Errors**

**Symptoms:**
```
npm ERR! Error: ENOENT: no such file or directory
Module not found: Can't resolve '@/components/...'
```

**Solutions:**
```bash
# 1. Clean and reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# 2. Check if package.json is correct
cp package-fixed.json package.json

# 3. Verify vite.config.ts has correct aliases
cat vite.config.ts | grep -A 5 "alias"

# 4. Start with proper environment
npm run dev
```

**Fix:**
- Use the fixed package.json and vite.config.ts
- Ensure all frontend dependencies are installed
- Check that TypeScript paths are configured correctly

---

### **Issue 4: WebSocket Connection Failures**

**Symptoms:**
- Real-time features not working
- WebSocket connection errors in console
- Chat functionality not responding

**Solutions:**
```bash
# 1. Test WebSocket endpoint manually
wscat -c ws://localhost:8000/ws/chat

# 2. Check backend WebSocket handler
curl http://localhost:8000/health

# 3. Verify proxy configuration
grep -A 10 "proxy" frontend/vite.config.ts

# 4. Check firewall/network settings
netstat -an | grep 8000
```

**Fix:**
- Ensure backend WebSocket endpoint is working
- Verify Vite proxy configuration for WebSocket
- Check that no firewall is blocking connections

---

### **Issue 5: Missing Components/Routes**

**Symptoms:**
```
Error: Cannot resolve component 'EnhancedMainDashboard'
Component not found: ThreeEngineDashboard
```

**Solutions:**
```bash
# 1. Create missing component placeholders
mkdir -p frontend/src/components/missing

# 2. Create placeholder components
cat > frontend/src/components/missing/PlaceholderComponent.tsx << 'EOF'
import React from 'react';

interface PlaceholderProps {
  name: string;
}

export const PlaceholderComponent: React.FC<PlaceholderProps> = ({ name }) => (
  <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
    <div className="text-center">
      <h3 className="text-xl font-semibold text-gray-600">{name}</h3>
      <p className="text-gray-500 mt-2">Component under development</p>
    </div>
  </div>
);
EOF

# 3. Update imports to use placeholders
# Replace missing imports in App.tsx with PlaceholderComponent
```

**Fix:**
- Use placeholder components for missing ones
- Gradually implement real components
- Start with basic functionality first

---

### **Issue 6: Database/Memory Integration Errors**

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
Redis connection failed
Memory integration not working
```

**Solutions:**
```bash
# 1. Skip memory features for development
export ENABLE_MOCK_DATA=true

# 2. Use simplified backend without memory
python3 simple_dev_server.py

# 3. If you need database, install PostgreSQL
# For Mac: brew install postgresql
# For Ubuntu: sudo apt-get install postgresql

# 4. Use SQLite for development
pip install sqlalchemy sqlite3
```

**Fix:**
- Start without memory/database features
- Use mock data for development
- Add memory features later once basic app works

---

### **Issue 7: AI Model Dependencies**

**Symptoms:**
```
torch not found
transformers module missing
CUDA errors
Model loading failures
```

**Solutions:**
```bash
# 1. Use mock AI responses for development
export ENABLE_MOCK_DATA=true

# 2. Install minimal AI dependencies
pip install transformers torch --index-url https://download.pytorch.org/whl/cpu

# 3. Use cloud APIs instead of local models
export OPENAI_API_KEY=your-key-here

# 4. Skip AI features temporarily
# Use the simplified backend with mock responses
```

**Fix:**
- Start with mock AI responses
- Add real AI models later
- Use cloud APIs for initial development

---

## 🔧 Quick Fix Commands

### **Complete Reset & Fresh Start**
```bash
# Stop all services
./stop_revoagent_dev.sh 2>/dev/null || true

# Clean everything
rm -rf frontend/node_modules frontend/package-lock.json
rm -rf logs/
killall -9 python3 node 2>/dev/null || true

# Fresh setup
./start_revoagent_dev.sh
```

### **Test Backend Only**
```bash
# Start just the backend
python3 simple_dev_server.py &

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/dashboard/stats
```

### **Test Frontend Only**
```bash
# Start with API mocking
cd frontend
VITE_ENABLE_MOCK_DATA=true npm run dev
```

---

## 🎯 Development Workflow

### **Recommended Development Approach:**

1. **Start Simple**: Use `simple_dev_server.py` and basic frontend
2. **Test Connection**: Verify frontend can connect to backend
3. **Add Features Gradually**: Implement one component at a time
4. **Mock Everything**: Use mock data instead of real AI/DB initially
5. **Incremental Enhancement**: Add real features once basic app works

### **Development Checklist:**
- [ ] Backend running on port 8000
- [ ] Frontend running on port 12000
- [ ] Health check returns 200 OK
- [ ] Frontend shows "🟢 Connected" status
- [ ] Basic navigation works
- [ ] API calls return data (even if mocked)
- [ ] No console errors

---

## 📞 Getting Help

If you're still stuck after trying these solutions:

1. **Check the logs:**
   ```bash
   tail -f logs/backend.log
   tail -f logs/frontend.log
   ```

2. **Verify your setup:**
   ```bash
   # Check versions
   python3 --version  # Should be 3.9+
   node --version     # Should be 18+
   npm --version
   
   # Check processes
   ps aux | grep -E "(python|node)"
   
   # Check ports
   lsof -i :8000
   lsof -i :12000
   ```

3. **Test individual components:**
   ```bash
   # Test backend health
   curl -v http://localhost:8000/health
   
   # Test frontend build
   cd frontend && npm run build
   ```

4. **Use browser developer tools:**
   - Open browser DevTools (F12)
   - Check Console tab for JavaScript errors
   - Check Network tab for failed API calls
   - Check Application tab for WebSocket connections

---

## 🚀 Success Indicators

You'll know everything is working when:

- ✅ Backend health check returns `{"status": "healthy"}`
- ✅ Frontend shows "🟢 Connected" in top-right corner
- ✅ Dashboard loads without errors
- ✅ Browser console shows no red errors
- ✅ API calls in Network tab return 200 OK
- ✅ You can navigate between different sections

Happy coding! 🎉