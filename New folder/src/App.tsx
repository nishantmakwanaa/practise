import { useState } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import CodeEditor from "./components/CodeEditor";
import LanguageSelector from "./components/LanguageSelector";
import ResultsPanel from "./components/ResultsPanel";
import Navbar from "./components/Navbar";
import ExecutionPanel from "./components/ExecutionPanel";
import LoginPage from "./components/Login";
import SignUpPage from "./components/SignUp";
import ForgotPasswordPage from "./components/ForgotPassword";
import type { AnalysisResult, ExecutionResult } from "./utils/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";

function App() {
  const [code, setCode] = useState<string>("");
  const [language, setLanguage] = useState<string>("javascript");
  const [results, setResults] = useState<AnalysisResult | null>(null);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("analyze");
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    () => !!localStorage.getItem('userId')
  );

  const handleLogin = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      localStorage.setItem('userId', data.userId);
      setIsAuthenticated(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('userId');
    setIsAuthenticated(false);
  };

  const analyzeCode = async () => {
    if (!code.trim()) {
      setError("Please Enter Some Code To Analyze...");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5000/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code, language }),
      });

      if (!response.ok) {
        throw new Error("Failed To Analyze Code...");
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An Unknown Error Occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  const executeCode = async () => {
    if (!code.trim()) {
      setError("Please Enter Some Code To Execute.");
      return;
    }

    setIsExecuting(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5000/api/execute", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code, language }),
      });

      if (!response.ok) {
        throw new Error("Failed To Execute Code.");
      }

      const data = await response.json();
      setExecutionResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An Unknown Error Occurred.");
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {isAuthenticated && <Navbar onLogout={handleLogout} />}
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route
              path="/"
              element={
                isAuthenticated ? (
                  <div>
                    <h1 className="text-2xl font-bold mb-6">Code Quality Analyzer & Test Generator</h1>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div className="bg-white rounded-lg shadow p-4">
                        <div className="mb-4">
                          <LanguageSelector language={language} setLanguage={setLanguage} />
                        </div>
                        <CodeEditor code={code} setCode={setCode} language={language} />
                        <div className="mt-4 flex gap-2">
                          <button
                            onClick={executeCode}
                            disabled={isExecuting}
                            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded disabled:opacity-50"
                          >
                            {isExecuting ? "Executing..." : "Execute Code"}
                          </button>
                        </div>
                        {error && <p className="text-red-500 mt-2">{error}</p>}
                      </div>

                      <div className="bg-white rounded-lg shadow p-4">
                        <Tabs defaultValue="analyze" value={activeTab} onValueChange={setActiveTab}>
                          <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="execute">Execution Results</TabsTrigger>
                          </TabsList>
                          <TabsContent value="analyze">
                            <ResultsPanel results={results} isLoading={isLoading} />
                          </TabsContent>
                          <TabsContent value="execute">
                            <ExecutionPanel result={executionResult} isLoading={isExecuting} />
                          </TabsContent>
                        </Tabs>
                      </div>
                    </div>
                  </div>
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
            <Route
              path="/login"
              element={
                isAuthenticated ? (
                  <Navigate to="/" replace />
                ) : (
                  <LoginPage onLogin={handleLogin} error={error} loading={isLoading} />
                )
              }
            />
            <Route
              path="/signup"
              element={isAuthenticated ? <Navigate to="/" replace /> : <SignUpPage />}
            />
            <Route
              path="/forgot-password"
              element={isAuthenticated ? <Navigate to="/" replace /> : <ForgotPasswordPage />}
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
