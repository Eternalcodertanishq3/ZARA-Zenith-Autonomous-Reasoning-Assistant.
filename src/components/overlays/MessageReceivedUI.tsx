import { motion } from "framer-motion";

export function MessageReceivedUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex items-center flex-grow justify-between pl-3.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <span className="text-[9px] tracking-[0.2em] text-[#00FFA3] uppercase font-bold">
          New Message
        </span>
        <span className="text-sm font-semibold text-white/90 mt-0.5 whitespace-nowrap overflow-hidden text-ellipsis">
          Message from Rudra
        </span>
      </div>
      <div className="flex items-center pr-2">
        <div className="w-8 h-8 rounded-full bg-[#00FFA3]/10 border border-[#00FFA3]/30 flex items-center justify-center shadow-[0_0_12px_rgba(0,255,163,0.2)]">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#00FFA3"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4"
          >
            <rect width="20" height="16" x="2" y="4" rx="2" />
            <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
          </svg>
        </div>
      </div>
    </motion.div>
  );
}
