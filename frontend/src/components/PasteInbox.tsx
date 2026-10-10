interface PasteInboxProps {
  text: string
  onTextChange: (text: string) => void
  codeMode: boolean
  onCodeModeChange: (codeMode: boolean) => void
  onSubmit: () => void
  loading: boolean
}

export default function PasteInbox({
  text,
  onTextChange,
  codeMode,
  onCodeModeChange,
  onSubmit,
  loading,
}: PasteInboxProps) {
  return (
    <div className="space-y-4">
      <textarea
        value={text}
        onChange={(e) => onTextChange(e.target.value)}
        placeholder="Paste anything — Slack message, terminal error, code snippet, email, Jira ticket..."
        rows={10}
        spellCheck={!codeMode}
        className={`w-full resize-none rounded-xl border border-border bg-panel p-4 text-white outline-none focus:border-accent ${
          codeMode ? "font-mono text-sm" : ""
        }`}
      />
      <label className="flex w-fit cursor-pointer items-center gap-2 text-sm text-neutral-400">
        <input
          type="checkbox"
          checked={codeMode}
          onChange={(e) => onCodeModeChange(e.target.checked)}
          className="accent-accent"
        />
        Treat as code
        <span className="text-xs text-neutral-600">(code is usually detected automatically)</span>
      </label>
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
