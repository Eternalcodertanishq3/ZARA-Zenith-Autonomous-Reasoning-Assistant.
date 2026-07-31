import { motion } from "framer-motion";

export function DeployingUI() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      className="w-full mt-2 flex flex-col text-white"
    >
      <div className="border-b border-white/[0.15] pb-2 w-full flex justify-between items-center">
        <span className="font-semibold text-[10px] tracking-widest text-[#00FFA3] uppercase">Deployment</span>
        <span className="text-[9px] bg-[#00FFA3]/15 text-[#00FFA3] px-2 py-0.5 rounded-full border border-[#00FFA3]/20 font-medium">
          Building
        </span>
      </div>
      
      <div className="flex flex-col mt-2">
        <motion.span layoutId="status-text" className="text-base font-bold tracking-tight text-white/95">Deploying Production bundle</motion.span>
        <motion.span layoutId="status-label" className="text-xs text-white/70 mt-0.5">Vercel Platform</motion.span>
      </div>

      <div className="flex flex-col gap-2 mt-3 text-[11px] text-white/80 font-mono">
        <div className="flex items-center gap-2">
          <span className="text-[#00FFA3]">✔</span>
          <span>Configured target assets</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[#00FFA3]">✔</span>
          <span>Created edge function bundle</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[#00FFA3] animate-pulse">●</span>
          <span className="text-white/80">Uploading assets to CDN (45%)...</span>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex justify-between items-center mb-1.5 text-[10px] text-white/80">
          <span>Upload progress</span>
          <span className="font-mono text-[#00FFA3]">45%</span>
        </div>
        <div className="flex gap-[2px] items-center w-full h-2">
          {Array.from({ length: 25 }).map((_, i) => {
            const isFilled = i < 11;
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
