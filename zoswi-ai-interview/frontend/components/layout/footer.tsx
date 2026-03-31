export function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-800/80 py-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-6 text-sm text-slate-400 md:flex-row md:items-center md:justify-between">
        <p>(c) {new Date().getFullYear()} ZoSwi. Career intelligence platform.</p>
        <p>Privacy-aware interview orchestration for candidate and recruiter readiness.</p>
      </div>
    </footer>
  );
}
