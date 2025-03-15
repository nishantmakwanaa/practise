interface LanguageSelectorProps {
  language: string
  setLanguage: (language: string) => void
}

const LanguageSelector = ({ language, setLanguage }: LanguageSelectorProps) => {
  const languages = [
    { value: "javascript", label: "JavaScript" },
    { value: "python", label: "Python" },
    { value: "java", label: "Java" },
    { value: "php", label: "PHP" },
    { value: "cpp", label: "C++" },
    { value: "csharp", label: "C#" },
  ]

  return (
    <div>
      <label htmlFor="language-select" className="block text-sm font-medium text-gray-700 mb-1">
        Select Language
      </label>
      <select
        id="language-select"
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {languages.map((lang) => (
          <option key={lang.value} value={lang.value}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default LanguageSelector
