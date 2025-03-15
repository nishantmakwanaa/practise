"use client"

import type React from "react"
import { useRef, useState, useEffect } from "react"
import * as monaco from "monaco-editor"
import { Editor } from "@monaco-editor/react"

interface CodeEditorProps {
  code: string
  setCode: (code: string) => void
  language: string
  userId?: string
}

const CodeEditor = ({ code, setCode, language, userId }: CodeEditorProps) => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)
  const [selectionPosition, setSelectionPosition] = useState<{ top: number; left: number } | null>(null)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedText, setSelectedText] = useState("")
  const [feedback, setFeedback] = useState<{ message: string; type: "success" | "error" | null }>({
    message: "",
    type: null,
  })

  const handleEditorDidMount = (editor: monaco.editor.IStandaloneCodeEditor) => {
    editorRef.current = editor

    editor.onDidChangeCursorSelection(() => {
      const selection = editor.getSelection()
      if (selection && !selection.isEmpty()) {
        const selectedText = editor.getModel()?.getValueInRange(selection) || ""
        setSelectedText(selectedText)

        const domNode = editor.getDomNode()
        if (domNode) {
          const endLineNumber = selection.endLineNumber
          const endColumn = selection.endColumn

          const position = editor.getScrolledVisiblePosition({ lineNumber: endLineNumber, column: endColumn })
          const rect = domNode.getBoundingClientRect()

          if (position) {
            const top = rect.top + position.top
            const left = rect.left + position.left + 10

            setSelectionPosition({ top, left })
            setIsMenuOpen(false)
          }
        }
      } else {
        setSelectionPosition(null)
        setSelectedText("")
      }
    })

    return () => {
      document.removeEventListener("click", handleClickOutside)
    }
  }

  const handleClickOutside = (e: MouseEvent) => {
    const target = e.target as HTMLElement
    if (!target.closest(".menu-trigger") && !target.closest(".menu-dropdown")) {
      setIsMenuOpen(false)
    }
  }

  useEffect(() => {
    document.addEventListener("click", handleClickOutside)
    return () => {
      document.removeEventListener("click", handleClickOutside)
    }
  }, [])

  const getMonacoLanguage = (lang: string) => {
    const languageMap: Record<string, string> = {
      javascript: "javascript",
      python: "python",
      java: "java",
      php: "php",
      cpp: "cpp",
      csharp: "csharp",
    }
    return languageMap[lang] || "plaintext"
  }

  const toggleMenu = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsMenuOpen(!isMenuOpen)
  }

  const showFeedback = (message: string, type: "success" | "error") => {
    setFeedback({ message, type })
    setTimeout(() => {
      setFeedback({ message: "", type: null })
    }, 5000)
  }

  const handleApiCall = async (endpoint: string, action: string) => {
    if (!editorRef.current || !selectedText) return

    setIsLoading(true)
    setIsMenuOpen(false)

    try {
      const selection = editorRef.current.getSelection()
      if (!selection) {
        setIsLoading(false)
        return
      }

      const fullCode = editorRef.current.getValue()

      const response = await fetch(`http://localhost:5000/api/${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          code: selectedText,
          fullCode,
          language,
          userId,
        }),
      })

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`)
      }

      const data = await response.json()

      if (endpoint === "fix-issues" && data.modifiedCode) {
        const model = editorRef.current.getModel()
        if (model && selection) {
          editorRef.current.executeEdits("api-edit", [
            {
              range: selection,
              text: data.modifiedCode,
              forceMoveMarkers: true,
            },
          ])
          showFeedback("Code successfully fixed!", "success")
        }
      } else if (endpoint === "generate-test-cases" && data.testCases) {
        const model = editorRef.current.getModel()
        if (model && selection) {
          const position = {
            lineNumber: selection.endLineNumber + 1,
            column: 1,
          }

          const Range = monaco.Range
          editorRef.current.executeEdits("api-edit", [
            {
              range: new Range(position.lineNumber, position.column, position.lineNumber, position.column),
              text: `\n\n${data.testCases}\n`,
              forceMoveMarkers: true,
            },
          ])
          showFeedback("Test cases generated successfully!", "success")
        }
      } else if (endpoint === "analyze-code") {
        showFeedback(`Analysis complete: ${data.summary || "Code analyzed successfully"}`, "success")
        console.log("Analysis results:", data)
      }

      if (data.message) {
        console.log(data.message)
      }
    } catch (error) {
      console.error(`Error in ${action}:`, error)
      showFeedback(`Error during ${action}: ${error instanceof Error ? error.message : "Unknown error"}`, "error")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative h-[500px] border border-gray-300 rounded-md overflow-hidden">
      <Editor
        height="100%"
        language={getMonacoLanguage(language)}
        value={code}
        onChange={(value) => setCode(value || "")}
        onMount={handleEditorDidMount}
        options={{
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          automaticLayout: true,
          wordWrap: "on",
          tabSize: 2,
          lineNumbers: "on",
        }}
        theme="vs-dark"
      />
      {selectionPosition && (
        <div
          className="absolute z-10 menu-trigger"
          style={{
            top: `${selectionPosition.top - 10}px`,
            left: `${selectionPosition.left}px`,
          }}
        >
          <button
            title="Toggle Menu"
            onClick={toggleMenu}
            className="flex items-center justify-center w-8 h-8 bg-gray-800 hover:bg-gray-700 text-white rounded-full shadow-lg transition-all duration-150 focus:outline-none border-2 border-gray-600"
            disabled={isLoading}
          >
            {isLoading ? (
              <svg
                className="animate-spin h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <circle cx="10" cy="6" r="2" />
                <circle cx="10" cy="10" r="2" />
                <circle cx="10" cy="14" r="2" />
              </svg>
            )}
          </button>

          {isMenuOpen && (
            <div className="absolute mt-2 right-0 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 menu-dropdown ring-1 ring-black ring-opacity-5 focus:outline-none z-20">
              <div className="py-1">
                <button
                  onClick={() => handleApiCall("analyze-code", "Enhance Code")}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 w-full text-left"
                  disabled={isLoading}
                >
                  <svg
                    className="mr-2 h-4 w-4 text-blue-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    ></path>
                  </svg>
                  Enhance Code
                </button>
                <button
                  onClick={() => handleApiCall("generate-test-cases", "Generate Test Cases")}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 w-full text-left"
                  disabled={isLoading}
                >
                  <svg
                    className="mr-2 h-4 w-4 text-green-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                    ></path>
                  </svg>
                  Generate Test Cases
                </button>
                <button
                  onClick={() => handleApiCall("fix-issues", "Fix Issues")}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 w-full text-left"
                  disabled={isLoading}
                >
                  <svg
                    className="mr-2 h-4 w-4 text-yellow-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                    ></path>
                  </svg>
                  Fix Issues
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {feedback.message && (
        <div
          className={`absolute bottom-0 left-0 right-0 p-2 text-sm text-white ${feedback.type === "success" ? "bg-green-600" : "bg-red-600"}`}
        >
          {feedback.message}
        </div>
      )}
    </div>
  )
}

export default CodeEditor
