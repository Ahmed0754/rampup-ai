import { NavLink, Outlet } from "react-router-dom"
import { useAuth } from "../lib/auth.tsx"

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/inbox", label: "Explain This" },
  { to: "/reply", label: "Reply Generator" },
  { to: "/progress", label: "Progress Tracker" },
  { to: "/resume", label: "Resume Bullets" },
]

export default function Layout() {
  const { session, signOut } = useAuth()

  return (
    <div className="flex min-h-screen bg-base text-white">
      <aside className="flex w-64 flex-shrink-0 flex-col border-r border-border bg-panel p-4">
        <div className="mb-8 px-2 text-lg font-semibold text-white">RampUp AI</div>
        <nav className="flex flex-1 flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm transition ${
                  isActive
                    ? "bg-accent font-medium text-white"
                    : "text-neutral-400 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-4 border-t border-border pt-4">
          <p className="mb-2 truncate px-2 text-xs text-neutral-500">{session?.user.email}</p>
          <button
            onClick={() => signOut()}
            className="w-full rounded-lg px-3 py-2 text-left text-sm text-neutral-400 transition hover:bg-white/5 hover:text-white"
          >
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  )
}
