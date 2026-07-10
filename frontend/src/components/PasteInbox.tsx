interface PasteInboxProps {
  text: string
  onTextChange: (text: string) => void
  onSubmit: () => void
  loading: boolean
}

export default function PasteInbox({ text, onTextChange, onSubmit, loading }: PasteInboxProps) {
  return (
    <div className="space-y-4">
      <textarea
        value={text}
        onChange={(e) => onTextChange(e.target.value)}
        placeholder="Paste anything — Slack message, terminal error, email, Jira ticket..."
        rows={10}
        className="w-full resize-none rounded-xl border border-border bg-panel p-4 text-white outline-none focus:border-accent"
      />
      <button
        type="button"
        onClick={onSubmit}
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-4 py-3 font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Analyzing...
          </>
        ) : (
          "Explain This"
        )}
      </button>
    </div>
  )
}
