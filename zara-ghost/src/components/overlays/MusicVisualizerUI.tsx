import { motion } from "framer-motion";
import { useState } from "react";

export function MusicVisualizerUI() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [songIndex, setSongIndex] = useState(0);

  const playlist = [
    { title: "Starboy", artist: "The Weeknd" },
    { title: "Blinding Lights", artist: "The Weeknd" },
    { title: "Save Your Tears", artist: "The Weeknd" },
    { title: "After Hours", artist: "The Weeknd" }
  ];

  const currentSong = playlist[songIndex];

  const handleNext = () => {
    setSongIndex((prev) => (prev + 1) % playlist.length);
  };

  const handlePrev = () => {
    setSongIndex((prev) => (prev - 1 + playlist.length) % playlist.length);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className="flex items-center flex-grow justify-between pl-3.5 pointer-events-auto w-full select-none"
    >
      <div className="flex flex-col items-start min-w-0 pr-2">
        <span className="text-[9px] tracking-[0.2em] text-[#FF9900] uppercase font-bold animate-pulse">
          Now Playing
        </span>
        <span className="text-sm font-bold text-white mt-0.5 whitespace-nowrap overflow-hidden text-ellipsis max-w-[130px]">
          {currentSong.title}
        </span>
        <span className="text-[10px] text-white/70 truncate max-w-[130px]">
          {currentSong.artist}
        </span>
      </div>
      
      <div className="flex items-center gap-3 pr-1">
        <div className="flex gap-1 items-center h-4.5 mr-1">
          {[0.5, 1.0, 0.7, 0.4].map((h, i) => (
            <motion.div
              key={i}
              animate={isPlaying ? { scaleY: [0.2, h, 0.2] } : { scaleY: 0.2 }}
              transition={isPlaying ? { repeat: Infinity, duration: 0.5 + i * 0.1, delay: i * 0.05 } : {}}
              className="w-[2.5px] h-full bg-[#FF9900] rounded-full origin-center shadow-[0_0_8px_rgba(255,153,0,0.4)]"
            />
          ))}
        </div>

        <button
          onClick={handlePrev}
          className="w-7 h-7 rounded-full bg-white/10 border border-white/20 hover:bg-white/20 active:scale-90 transition-all duration-150 cursor-pointer flex items-center justify-center pointer-events-auto"
          title="Previous Track"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-3.5 h-3.5 text-white/80 hover:text-white"
          >
            <polygon points="19 20 9 12 19 4 19 20"></polygon>
            <line x1="5" y1="19" x2="5" y2="5"></line>
          </svg>
        </button>

        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-8 h-8 rounded-full bg-[#FF9900]/10 border border-[#FF9900]/30 hover:bg-[#FF9900]/20 active:scale-90 transition-all duration-200 cursor-pointer flex items-center justify-center shadow-[0_0_10px_rgba(255,153,0,0.15)] hover:shadow-[0_0_15px_rgba(255,153,0,0.35)] pointer-events-auto"
          title={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-3.5 h-3.5 text-white"
            >
              <path fillRule="evenodd" d="M6.75 5.25a.75.75 0 0 1 .75-.75H9a.75.75 0 0 1 .75.75v13.5a.75.75 0 0 1-.75.75H7.5a.75.75 0 0 1-.75-.75V5.25Zm7.5 0A.75.75 0 0 1 15 4.5h1.5a.75.75 0 0 1 .75.75v13.5a.75.75 0 0 1-.75.75H15a.75.75 0 0 1-.75-.75V5.25Z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-3.5 h-3.5 text-white translate-x-[0.5px]"
            >
              <path fillRule="evenodd" d="M4.5 5.653c0-1.427 1.529-2.33 2.779-1.643l11.54 6.347c1.295.712 1.295 2.573 0 3.286L7.28 19.99c-1.25.687-2.779-.217-2.779-1.643V5.653Z" clipRule="evenodd" />
            </svg>
          )}
        </button>

        <button
          onClick={handleNext}
          className="w-7 h-7 rounded-full bg-white/10 border border-white/20 hover:bg-white/20 active:scale-90 transition-all duration-150 cursor-pointer flex items-center justify-center pointer-events-auto"
          title="Next Track"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-3.5 h-3.5 text-white/80 hover:text-white"
          >
            <polygon points="5 4 15 12 5 20 5 4"></polygon>
            <line x1="19" y1="5" x2="19" y2="19"></line>
          </svg>
        </button>
      </div>
    </motion.div>
  );
}
