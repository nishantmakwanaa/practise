import type { AnalysisResult } from "../types"
import IssuesList from "./IssuesList"
import SuggestionsList from "./SuggestionsList"
import TestCasesList from "./TestCasesList"
import ScoreCard from "./ScoreCard"

interface ResultsPanelProps {
  results: AnalysisResult | null
  isLoading: boolean
}

const ResultsPanel = ({ results, isLoading }: ResultsPanelProps) => {
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing Your Code...</p>
        </div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <p>Submit Your Code To See Analysis Results</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Analysis Results</h2>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <ScoreCard label="Readability" score={results.metrics.readabilityScore} />
        <ScoreCard label="Security" score={results.metrics.securityScore} />
        <ScoreCard label="Performance" score={results.metrics.performanceScore} />
        <ScoreCard label="Overall" score={results.metrics.overallScore} />
      </div>

      <div className="space-y-6">
        <IssuesList issues={results.issues} />
        <SuggestionsList suggestions={results.suggestions} />
        <TestCasesList testCases={results.testCases} />
      </div>
    </div>
  )
}

export default ResultsPanel
