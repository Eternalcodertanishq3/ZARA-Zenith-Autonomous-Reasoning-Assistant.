import { motion } from "framer-motion";

export function TaskUI() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      className="w-full mt-2 flex flex-col text-white"
    >
      <div className="border-b border-white/[0.15] pb-2 w-full flex justify-between items-center">
        <span className="font-semibold text-[10px] tracking-widest text-white/80 uppercase">Task Manager</span>
        <span className="text-[9px] bg-[#00FFA3]/15 text-[#00FFA3] px-2 py-0.5 rounded-full border border-[#00FFA3]/20 font-medium">
          Running
        </span>
      </div>
      
      <div className="flex flex-col mt-2">
        <motion.span layoutId="status-text" className="text-base font-bold tracking-tight text-white/95">Processing Context</motion.span>
        <motion.span layoutId="status-label" className="text-xs text-[#00FFA3] font-medium mt-0.5">Model Context Protocol</motion.span>
      </div>

      {/* Action Logs */}
      <div className="flex flex-col gap-2 mt-3 text-[11px] text-white/80 font-mono">
        <div className="flex items-center gap-2">
          <span className="text-[#00FFA3]">✔</span>
          <span>Initiated local environment</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[#00FFA3]">✔</span>
          <span>Indexed workspace references</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[#00FFA3] animate-pulse">●</span>
          <span className="text-white/80">Querying semantic endpoints...</span>
        </div>
      </div>

      {/* Glowing Segmented Progress Bar */}
      <div className="mt-4">
        <div className="flex justify-between items-center mb-1.5 text-[10px] text-white/80">
          <span>Overall Progress</span>
          <span className="font-mono text-white">68%</span>
        </div>
        <div className="flex gap-[2px] items-center w-full h-2">
          {Array.from({ length: 25 }).map((_, i) => {
            const isFilled = i < 17; // 17 / 25 = 68%
            return (
              <motion.div 
                key={i}
                initial={{ 
                  backgroundColor: "rgba(255, 255, 255, 0.1)", 
                  boxShadow: "0px 0px 0px rgba(0,255,163,0)" 
                }}
                animate={{ 
                  backgroundColor: isFilled ? "#00FFA3" : "rgba(255, 255, 255, 0.1)",
                  boxShadow: isFilled ? "0px 0px 6px rgba(0,255,163,0.4)" : "0px 0px 0px rgba(0,255,163,0)"
                }}
                transition={{ delay: isFilled ? i * 0.04 : 0, duration: 0.3 }}
                className="h-full flex-1 rounded-[1px]" 
              />
            )
          })}
        </div>
      </div>
    </motion.div>
  );
}
