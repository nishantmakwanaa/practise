import { useState } from "react"
import type { TestCase } from "../types"

interface TestCasesListProps {
  testCases: TestCase[]
}

const TestCasesList = ({ testCases }: TestCasesListProps) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)

  if (testCases.length === 0) {
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium mb-2">Generated Test Cases</h3>
        <p className="text-gray-500">No Test Cases Generated For Your Code.</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <h3 className="text-lg font-medium mb-2">Generated Test Cases ({testCases.length})</h3>
      <div className="space-y-3">
        {testCases.map((testCase, index) => (
          <div key={index} className="p-3 bg-white rounded border border-gray-200">
            <div
              className="flex justify-between items-center cursor-pointer"
              onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
            >
              <p className="font-medium">{testCase.name}</p>
              <button className="text-blue-600">{expandedIndex === index ? "Hide" : "Show"}</button>
            </div>

            {expandedIndex === index && (
              <div className="mt-3 space-y-3">
                <p className="text-sm text-gray-600">{testCase.description}</p>
                <div>
                  <div className="text-sm font-medium text-gray-500 mb-1">Test Code:</div>
                  <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">{testCase.code}</pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default TestCasesList
