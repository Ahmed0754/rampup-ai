import toast from "react-hot-toast"

interface ResumeBulletProps {
  bullet: string
}

export default function ResumeBullet({ bullet }: ResumeBulletProps) {
  async function handleCopy() {
    await navigator.clipboard.writeText(bullet)
    toast.success("Copied to clipboard")
  }

  return (
    <li className="flex items-start justify-between gap-3 rounded-xl border border-border bg-panel p-4">
      <span className="text-sm text-white">{bullet}</span>
      <button
        type="button"
        onClick={handleCopy}
        className="flex-shrink-0 rounded-lg border border-border px-3 py-1 text-xs text-neutral-300 hover:text-white"
      >
        Copy
      </button>
    </li>
  )
}
