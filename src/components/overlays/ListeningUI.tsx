import { motion } from "framer-motion";

export function ListeningUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className="flex items-center flex-grow justify-between pl-2.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <motion.span layoutId="status-label" className="text-[9px] tracking-[0.2em] text-[#00FFA3] uppercase font-bold animate-pulse">
          Lumi Ears
        </motion.span>
        <motion.span layoutId="status-text" className="text-sm font-medium text-white/80 mt-0.5 whitespace-nowrap">
          Listening for command...
        </motion.span>
      </div>
      <div className="flex gap-1 items-center h-5 pr-2">
        {[0.4, 0.9, 0.5, 1.1, 0.7, 0.3].map((heightFactor, i) => (
          <motion.div
            key={i}
            animate={{ scaleY: [0.2, heightFactor, 0.2] }}
            transition={{
              repeat: Infinity,
              duration: 0.6 + i * 0.1,
              ease: "easeInOut",
            }}
            className="w-[3px] h-full bg-[#00FFA3] rounded-full origin-center shadow-[0_0_8px_rgba(0,255,163,0.5)]"
          />
        ))}
      </div>
    </motion.div>
  );
}
