import { motion } from "framer-motion";

interface IncomingCallUIProps {
  onAccept: () => void;
  onDecline: () => void;
}

export function IncomingCallUI({ onAccept, onDecline }: IncomingCallUIProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="flex items-center flex-grow justify-between pl-3.5 pointer-events-auto w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <motion.span layoutId="call-status" className="text-[9px] tracking-[0.2em] text-[#00FFA3] uppercase font-bold animate-pulse">
          Incoming Call
        </motion.span>
        <motion.span layoutId="call-name" className="text-base font-bold tracking-tight text-white mt-0.5 whitespace-nowrap overflow-hidden text-ellipsis max-w-[140px]">
          Rudra Gohil
        </motion.span>
      </div>
      
      <div className="flex gap-3 pr-1">
        <button
          onClick={onDecline}
          className="w-9 h-9 rounded-full bg-red-500/20 border border-red-500/40 hover:bg-red-500/35 active:scale-90 transition-all duration-200 cursor-pointer flex items-center justify-center shadow-[0_0_12px_rgba(239,68,68,0.25)] hover:shadow-[0_0_20px_rgba(239,68,68,0.5)] pointer-events-auto"
          title="Decline Call"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4 text-white transform rotate-[135deg]"
          >
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
          </svg>
        </button>

        <button
          onClick={onAccept}
          className="w-9 h-9 rounded-full bg-[#00FFA3]/20 border border-[#00FFA3]/40 hover:bg-[#00FFA3]/35 active:scale-90 transition-all duration-200 cursor-pointer flex items-center justify-center shadow-[0_0_12px_rgba(0,255,163,0.25)] hover:shadow-[0_0_20px_rgba(0,255,163,0.5)] pointer-events-auto"
          title="Accept Call"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-4 h-4 text-white"
          >
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
          </svg>
        </button>
      </div>
    </motion.div>
  );
}
