import { useLocation } from "react-router-dom"
import ReplyGenerator from "../components/ReplyGenerator.tsx"

interface ReplyLocationState {
  originalText?: string
  pasteId?: string
}

export default function Reply() {
  const location = useLocation()
  const state = (location.state as ReplyLocationState) ?? {}

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-semibold text-white">Reply Generator</h1>
      <ReplyGenerator originalText={state.originalText ?? ""} pasteId={state.pasteId} />
    </div>
  )
}
