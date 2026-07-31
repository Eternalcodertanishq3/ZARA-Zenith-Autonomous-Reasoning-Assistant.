import { motion } from "framer-motion";

export function CallEndedUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="flex items-center flex-grow justify-between pl-3.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <motion.span layoutId="call-name" className="text-[9px] tracking-[0.2em] text-white/70 uppercase font-bold">
          Communication
        </motion.span>
        <motion.span layoutId="call-status" className="text-sm font-bold text-[#FF3366] mt-0.5 uppercase tracking-widest">
          Call Ended
        </motion.span>
      </div>
      <div className="flex items-center pr-2">
        <div className="w-8 h-8 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#FF3366"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4 opacity-60 transform rotate-[135deg]"
          >
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
          </svg>
        </div>
      </div>
    </motion.div>
  );
}
