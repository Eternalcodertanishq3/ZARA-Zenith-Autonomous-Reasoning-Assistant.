import { motion } from "framer-motion";

export function MessageSentUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex items-center flex-grow justify-between pl-3.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <span className="text-[9px] tracking-[0.2em] text-[#00FFA3] uppercase font-bold">
          Message Sent
        </span>
        <span className="text-sm font-semibold text-white/95 mt-0.5 whitespace-nowrap">
          Delivered successfully
        </span>
      </div>
      <div className="flex items-center pr-2">
        <div className="w-8 h-8 rounded-full bg-[#00FFA3]/20 border border-[#00FFA3]/40 flex items-center justify-center shadow-[0_0_12px_rgba(0,255,163,0.3)]">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#00FFA3"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
      </div>
    </motion.div>
  );
}
