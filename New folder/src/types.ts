export interface CodeIssue {
  line: number
  message: string
  severity: "error" | "warning" | "info"
  type: "security" | "performance" | "readability" | "syntax"
}

export interface Suggestion {
  description: string
  originalCode?: string
  improvedCode?: string
}

export interface TestCase {
  name: string
  code: string
  description: string
}

export interface AnalysisResult {
  issues: CodeIssue[]
  suggestions: Suggestion[]
  testCases: TestCase[]
  metrics: {
    readabilityScore: number
    securityScore: number
    performanceScore: number
    overallScore: number
  }
}

export interface ExecutionResult {
  output: string
  error: string | null
  executionTime: number
}

export interface User {
  id: number
  username: string
  email: string
  role: "user" | "admin"
}

export interface SavedAnalysis {
  id: number
  userId: number
  language: string
  code: string
  result: AnalysisResult
  createdAt: string
}

