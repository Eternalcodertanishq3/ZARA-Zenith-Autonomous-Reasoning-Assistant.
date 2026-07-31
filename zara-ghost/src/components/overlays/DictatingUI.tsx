import { motion } from "framer-motion";

export function DictatingUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex items-center flex-grow justify-between pl-3.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <motion.span layoutId="status-label" className="text-[9px] tracking-[0.2em] text-violet-400 uppercase font-bold animate-pulse">
          Lumi Dictate
        </motion.span>
        <motion.span layoutId="status-text" className="text-sm font-medium text-white/80 mt-0.5 whitespace-nowrap">
          Transcribing voice...
        </motion.span>
      </div>
      <div className="flex items-center pr-2">
        <div className="w-8 h-8 rounded-full bg-violet-500/10 border border-violet-500/30 flex items-center justify-center shadow-[0_0_12px_rgba(167,139,250,0.2)]">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#A78BFA"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4 animate-pulse"
          >
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
          </svg>
        </div>
      </div>
    </motion.div>
  );
}
