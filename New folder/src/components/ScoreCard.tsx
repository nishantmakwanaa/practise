interface ScoreCardProps {
  label: string
  score: number
}

const ScoreCard = ({ label, score }: ScoreCardProps) => {
  const getColorClass = () => {
    if (score >= 80) return "bg-green-100 text-green-800"
    if (score >= 60) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  return (
    <div className={`p-3 rounded-lg ${getColorClass()}`}>
      <div className="text-sm font-medium">{label}</div>
      <div className="text-2xl font-bold">{score}</div>
    </div>
  )
}

export default ScoreCard
