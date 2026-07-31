import { motion } from "framer-motion";

export function MessageSendingUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex items-center flex-grow justify-between pl-3.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <span className="text-[9px] tracking-[0.2em] text-sky-400 uppercase font-bold animate-pulse">
          Message Hub
        </span>
        <span className="text-sm font-medium text-white/80 mt-0.5 whitespace-nowrap">
          Delivering response...
        </span>
      </div>
      <div className="flex items-center pr-2">
        <div className="w-8 h-8 rounded-full bg-sky-500/10 border border-sky-500/20 flex items-center justify-center">
          <motion.svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#38bdf8"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4"
            animate={{ x: [-1.5, 1.5, -1.5], y: [1.5, -1.5, 1.5] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </motion.svg>
        </div>
      </div>
    </motion.div>
  );
}
