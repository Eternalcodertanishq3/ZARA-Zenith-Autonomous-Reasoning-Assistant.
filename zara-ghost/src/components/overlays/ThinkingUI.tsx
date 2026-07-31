import { motion } from "framer-motion";

export function ThinkingUI() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className="flex items-center flex-grow justify-between pl-2.5 w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <motion.span layoutId="status-label" className="text-[9px] tracking-[0.2em] text-[#9D4EDD] uppercase font-bold animate-pulse whitespace-nowrap">
          Cognitive Engine
        </motion.span>
        <motion.span layoutId="status-text" className="text-sm font-medium text-white/80 mt-0.5 whitespace-nowrap">
          Synthesizing thoughts...
        </motion.span>
      </div>
      <div className="flex gap-1.5 items-center h-5 pr-2">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            animate={{ 
              scale: [1, 1.5, 1],
              opacity: [0.4, 1, 0.4]
            }}
            transition={{
              repeat: Infinity,
              duration: 1.2,
              delay: i * 0.2,
              ease: "easeInOut",
            }}
            className="w-1.5 h-1.5 rounded-full bg-[#9D4EDD] shadow-[0_0_8px_rgba(157,78,221,0.8)]"
          />
        ))}
      </div>
    </motion.div>
  );
}
