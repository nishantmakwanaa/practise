import type { ExecutionResult } from "../types"

interface ExecutionPanelProps {
  result: ExecutionResult | null
  isLoading: boolean
}

const ExecutionPanel = ({ result, isLoading }: ExecutionPanelProps) => {
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Executing Your Code...</p>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <p>Execute Your Code To See Results</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Execution Results</h2>

      <div className="p-4 bg-gray-800 text-white rounded-md font-mono text-sm whitespace-pre-wrap overflow-auto max-h-[400px]">
        {result.output || "No Output"}
      </div>

      {result.error && (
        <div className="p-4 bg-red-100 text-red-800 rounded-md font-mono text-sm whitespace-pre-wrap overflow-auto">
          <div className="font-bold mb-1">Error :</div>
          {result.error}
        </div>
      )}

      <div className="text-sm text-gray-500">Execution Time : {result.executionTime}ms</div>
    </div>
  )
}

export default ExecutionPanel
