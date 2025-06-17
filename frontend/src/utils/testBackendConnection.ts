// Backend Connection Test Script
// Test script to validate backend integration

interface TestResult {
  name: string;
  success: boolean;
  message: string;
  responseTime?: number;
  data?: any;
}

class BackendConnectionTester {
  private baseUrl: string;

  constructor() {
    this.baseUrl = 'http://localhost:8000';
  }

  async runAllTests(): Promise<void> {
    console.log('🧪 Starting Backend Connection Tests...\n');
    
    const tests = [
      () => this.testHealthCheck(),
      () => this.testAIGeneration(),
      () => this.testTeamCoordinator(),
      () => this.testMonitoring(),
      () => this.testWebSocket()
    ];

    const results: TestResult[] = [];

    for (const test of tests) {
      try {
        const result = await test();
        results.push(result);
        this.logResult(result);
      } catch (error) {
        const errorResult: TestResult = {
          name: 'Unknown Test',
          success: false,
          message: `Test failed: ${error instanceof Error ? error.message : 'Unknown error'}`
        };
        results.push(errorResult);
        this.logResult(errorResult);
      }
    }

    this.printSummary(results);
  }

  private async testHealthCheck(): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/health/ping`);
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          name: '🏥 Health Check',
          success: true,
          message: 'Backend is online and responding',
          responseTime,
          data
        };
      } else {
        return {
          name: '🏥 Health Check',
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`,
          responseTime
        };
      }
    } catch (error) {
      return {
        name: '🏥 Health Check',
        success: false,
        message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  private async testAIGeneration(): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/ai/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: 'Say hello from the backend test!',
          max_tokens: 50,
          temperature: 0.7,
          force_local: true
        })
      });
      
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          name: '🤖 AI Generation',
          success: true,
          message: 'AI generation is working',
          responseTime,
          data: { content: data.content?.substring(0, 100) + '...' }
        };
      } else {
        return {
          name: '🤖 AI Generation',
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`,
          responseTime
        };
      }
    } catch (error) {
      return {
        name: '🤖 AI Generation',
        success: false,
        message: `AI generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  private async testTeamCoordinator(): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/team/status`);
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          name: '👥 Team Coordinator',
          success: true,
          message: 'Team coordinator is responding',
          responseTime,
          data: { 
            active_agents: data.active_agents || 0,
            total_agents: data.total_agents || 0
          }
        };
      } else {
        return {
          name: '👥 Team Coordinator',
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`,
          responseTime
        };
      }
    } catch (error) {
      return {
        name: '👥 Team Coordinator',
        success: false,
        message: `Team coordinator failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  private async testMonitoring(): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/monitoring/metrics`);
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        return {
          name: '📊 Monitoring',
          success: true,
          message: 'Monitoring system is active',
          responseTime,
          data: {
            agents: data.agents || {},
            workflows: data.workflows || {}
          }
        };
      } else {
        return {
          name: '📊 Monitoring',
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`,
          responseTime
        };
      }
    } catch (error) {
      return {
        name: '📊 Monitoring',
        success: false,
        message: `Monitoring failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  private async testWebSocket(): Promise<TestResult> {
    return new Promise((resolve) => {
      const startTime = Date.now();
      
      try {
        const ws = new WebSocket(`ws://localhost:8000/ws/monitoring`);
        
        const timeout = setTimeout(() => {
          ws.close();
          resolve({
            name: '🔌 WebSocket',
            success: false,
            message: 'WebSocket connection timeout',
            responseTime: Date.now() - startTime
          });
        }, 5000);
        
        ws.onopen = () => {
          clearTimeout(timeout);
          const responseTime = Date.now() - startTime;
          ws.close();
          resolve({
            name: '🔌 WebSocket',
            success: true,
            message: 'WebSocket connection successful',
            responseTime
          });
        };
        
        ws.onerror = (error) => {
          clearTimeout(timeout);
          resolve({
            name: '🔌 WebSocket',
            success: false,
            message: 'WebSocket connection failed',
            responseTime: Date.now() - startTime
          });
        };
        
      } catch (error) {
        resolve({
          name: '🔌 WebSocket',
          success: false,
          message: `WebSocket error: ${error instanceof Error ? error.message : 'Unknown error'}`
        });
      }
    });
  }

  private logResult(result: TestResult): void {
    const status = result.success ? '✅' : '❌';
    const time = result.responseTime ? ` (${result.responseTime}ms)` : '';
    console.log(`${status} ${result.name}: ${result.message}${time}`);
    
    if (result.data && result.success) {
      console.log(`   Data:`, result.data);
    }
    console.log('');
  }

  private printSummary(results: TestResult[]): void {
    const passed = results.filter(r => r.success).length;
    const total = results.length;
    
    console.log('📋 Test Summary:');
    console.log(`   Passed: ${passed}/${total}`);
    console.log(`   Success Rate: ${Math.round((passed / total) * 100)}%`);
    
    if (passed === total) {
      console.log('🎉 All tests passed! Backend integration is working correctly.');
    } else {
      console.log('⚠️  Some tests failed. Check backend server and configuration.');
    }
  }
}

// Export for use in components
export const testBackendConnection = async (): Promise<void> => {
  const tester = new BackendConnectionTester();
  await tester.runAllTests();
};

// Auto-run in development mode
if (import.meta.env.DEV) {
  console.log('🔧 Development mode detected. Backend connection test available.');
  console.log('Run testBackendConnection() in console to test backend integration.');
  
  // Make it available globally for easy testing
  (window as any).testBackendConnection = testBackendConnection;
}

export default BackendConnectionTester;