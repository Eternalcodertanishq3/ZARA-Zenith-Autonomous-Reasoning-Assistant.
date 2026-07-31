import { motion } from "framer-motion";

export function ErrorUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex items-center flex-grow justify-between pl-3.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <span className="text-[9px] tracking-[0.2em] text-[#FF3366] uppercase font-bold">
          System Alert
        </span>
        <span className="text-sm font-semibold text-white/90 mt-0.5 whitespace-nowrap overflow-hidden text-ellipsis">
          Execution failed
        </span>
      </div>
      <div className="flex items-center pr-2">
        <div className="w-8 h-8 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center shadow-[0_0_12px_rgba(255,51,102,0.2)]">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#FF3366"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
      </div>
    </motion.div>
  );
}
