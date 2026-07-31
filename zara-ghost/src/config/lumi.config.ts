// src/config/lumi.config.ts

export type LumiState = 
  | "boot" | "idle" | "sleep" | "waking" | "locked" | "admin_override" | "shutting_down"
  | "listening" | "listening_loud" | "thinking" | "speaking" | "dictating"
  | "incoming_call" | "active_call" | "call_ended" | "message_received" | "message_sending" | "message_sent"
  | "task" | "task_bg" | "compiling" | "fetching_data" | "deploying" | "success" | "error" | "warning"
  | "music_playing" | "music_paused" | "muted" | "dnd_mode"
  | "hover" | "clicked" | "file_dropped"
  | "analyzing_vision" | "reading_screen" | "writing_code" | "generating_media"
  | "network_offline" | "battery_low" | "syncing_cloud" | "focus_mode";

export interface PhysicsTarget {
  intensity: number;
  speed: number;
  colorMode: number; 
}

export const LumiPhysics: Record<LumiState, PhysicsTarget> = {
  // Category 1: Power & Core System
  boot:             { intensity: 1.5, speed: 6.0, colorMode: 0.0 },
  idle:             { intensity: 0.0, speed: 1.0, colorMode: 0.0 },
  sleep:            { intensity: -0.2, speed: 0.1, colorMode: 4.0 }, // Deep Blue, barely moving
  waking:           { intensity: 1.2, speed: 3.0, colorMode: 0.0 },
  locked:           { intensity: 0.5, speed: 0.0, colorMode: 5.0 }, // Solid Amber, frozen
  admin_override:   { intensity: 2.5, speed: 4.0, colorMode: 6.0 }, // Red Corona, White Core
  shutting_down:    { intensity: 3.0, speed: 8.0, colorMode: 0.0 },

  // Category 2: Voice & Intelligence
  listening:        { intensity: 0.5, speed: 1.6, colorMode: 0.0 },
  listening_loud:   { intensity: 1.2, speed: 4.0, colorMode: 0.0 },
  thinking:         { intensity: 0.8, speed: 0.5, colorMode: 0.0 },
  speaking:         { intensity: 1.8, speed: 3.8, colorMode: 0.0 },
  dictating:        { intensity: 0.8, speed: 1.5, colorMode: 1.0 }, // Steady Mint

  // Category 3: Communications
  incoming_call:    { intensity: 1.2, speed: 4.0, colorMode: 0.5 }, // Green/Violet pulse
  active_call:      { intensity: 1.0, speed: 2.5, colorMode: 0.0 },
  call_ended:       { intensity: 2.0, speed: 6.0, colorMode: 2.0 }, // Rapid Crimson flash
  message_received: { intensity: 1.5, speed: 4.0, colorMode: 0.0 },
  message_sending:  { intensity: 0.8, speed: 4.0, colorMode: 0.0 },
  message_sent:     { intensity: 1.5, speed: 3.0, colorMode: 1.0 }, // Mint flash

  // Category 4: Development & Task Execution
  task:             { intensity: 0.6, speed: 2.0, colorMode: 0.0 },
  task_bg:          { intensity: 0.3, speed: 1.2, colorMode: 0.0 }, // Dimmer, unobtrusive
  compiling:        { intensity: 2.0, speed: 5.0, colorMode: 0.0 }, // High frequency
  fetching_data:    { intensity: 0.6, speed: 3.0, colorMode: 0.0 },
  deploying:        { intensity: 2.5, speed: 0.5, colorMode: 1.0 }, // Building pressure
  success:          { intensity: 1.5, speed: 3.0, colorMode: 1.0 },
  error:            { intensity: 2.0, speed: 5.0, colorMode: 2.0 },
  warning:          { intensity: 1.0, speed: 2.0, colorMode: 5.0 }, // Amber pulse

  // Category 5: Media & Ambient
  music_playing:    { intensity: 1.2, speed: 2.5, colorMode: 3.0 }, // Sunset/Gold
  music_paused:     { intensity: 0.2, speed: 0.2, colorMode: 4.0 }, // Desaturated/Sleep
  muted:            { intensity: -0.1, speed: 0.5, colorMode: 0.0 },
  dnd_mode:         { intensity: -0.3, speed: 0.2, colorMode: 4.0 },

  // Category 6: Micro-Interactions
  hover:            { intensity: 0.3, speed: 1.5, colorMode: 0.0 },
  clicked:          { intensity: 1.5, speed: 5.0, colorMode: 0.0 },
  file_dropped:     { intensity: 2.5, speed: 4.0, colorMode: 6.0 }, // White flash
  
  // Category 7: Advanced AI Contexts
  analyzing_vision: { intensity: 1.5, speed: 4.0, colorMode: 0.5 }, // Green/Violet scanner
  reading_screen:   { intensity: 0.8, speed: 6.0, colorMode: 0.0 }, // Fast blue parsing
  writing_code:     { intensity: 2.5, speed: 8.0, colorMode: 1.0 }, // Matrix green, high speed
  generating_media: { intensity: 2.0, speed: 3.0, colorMode: 3.0 }, // Swirling sunset
  
  // Category 8: System Overrides
  network_offline:  { intensity: 1.0, speed: 1.0, colorMode: 2.0 }, // Red slow pulse
  battery_low:      { intensity: 0.5, speed: 0.5, colorMode: 5.0 }, // Amber slow pulse
  syncing_cloud:    { intensity: 1.2, speed: 3.0, colorMode: 0.0 }, 
  focus_mode:       { intensity: -0.1, speed: 0.5, colorMode: 7.0 }, // Deep purple, slow breathing
};
