import type { CodeIssue } from "../types"

interface IssuesListProps {
  issues: CodeIssue[]
}

const IssuesList = ({ issues }: IssuesListProps) => {
  if (issues.length === 0) {
    return (
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium mb-2">Issues</h3>
        <p className="text-gray-500">No Issues Found In Your Code !</p>
      </div>
    )
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "error":
        return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">Error</span>
      case "warning":
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">Warning</span>
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">Info</span>
    }
  }

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "security":
        return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">Security</span>
      case "performance":
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">Performance</span>
      case "readability":
        return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Readability</span>
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">Syntax</span>
    }
  }

  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <h3 className="text-lg font-medium mb-2">Issues ({issues.length})</h3>
      <div className="space-y-3">
        {issues.map((issue, index) => (
          <div key={index} className="p-3 bg-white rounded border border-gray-200">
            <div className="flex justify-between items-start">
              <div className="flex space-x-2">
                {getSeverityBadge(issue.severity)}
                {getTypeBadge(issue.type)}
              </div>
              <div className="text-sm text-gray-500">Line {issue.line}</div>
            </div>
            <p className="mt-2 text-sm">{issue.message}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default IssuesList
