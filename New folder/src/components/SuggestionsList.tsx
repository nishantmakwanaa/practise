import { useState } from "react"
import type { Suggestion } from "../types"

interface SuggestionsListProps {
  suggestions: Suggestion[]
}

const SuggestionsList = ({ suggestions }: SuggestionsListProps) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)

  if (suggestions.length === 0) {
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium mb-2">Improvement Suggestions</h3>
        <p className="text-gray-500">No Suggestions Available For Your Code.</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <h3 className="text-lg font-medium mb-2">Improvement Suggestions ({suggestions.length})</h3>
      <div className="space-y-3">
        {suggestions.map((suggestion, index) => (
          <div key={index} className="p-3 bg-white rounded border border-gray-200">
            <div
              className="flex justify-between items-center cursor-pointer"
              onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
            >
              <p className="font-medium">{suggestion.description}</p>
              <button className="text-blue-600">{expandedIndex === index ? "Hide" : "Show"}</button>
            </div>

            {expandedIndex === index && suggestion.originalCode && suggestion.improvedCode && (
              <div className="mt-3 space-y-3">
                <div>
                  <div className="text-sm font-medium text-gray-500 mb-1">Original Code:</div>
                  <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">{suggestion.originalCode}</pre>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-500 mb-1">Improved Code:</div>
                  <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">{suggestion.improvedCode}</pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default SuggestionsList
