"""
ZARA Native Desktop Dashboard
Ultra-Advanced PyQt6 Application - No Browser Required
Runs completely offline on your laptop
"""
import sys
import os
import math
import time
import threading
import logging
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("ZARA_NATIVE")

# Lazy imports
PyQt6 = None
QApplication = None
QMainWindow = None
QWidget = None
QVBoxLayout = None
QHBoxLayout = None
QGridLayout = None
QLabel = None
QFrame = None
QPushButton = None
QTextEdit = None
QLineEdit = None
QProgressBar = None
QTimer = None
Qt = None
QColor = None
QPainter = None
QBrush = None
QPen = None
QFont = None
QPixmap = None
QImage = None
QOpenGLWidget = None

def _lazy_load():
    global PyQt6, QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
    global QGridLayout, QLabel, QFrame, QPushButton, QTextEdit, QLineEdit
    global QProgressBar, QTimer, Qt, QColor, QPainter, QBrush, QPen, QFont
    global QPixmap, QImage, QOpenGLWidget
    
    if QApplication is None:
        try:
            from PyQt6.QtWidgets import (
                QApplication as _QApplication,
                QMainWindow as _QMainWindow,
                QWidget as _QWidget,
                QVBoxLayout as _QVBoxLayout,
                QHBoxLayout as _QHBoxLayout,
                QGridLayout as _QGridLayout,
                QLabel as _QLabel,
                QFrame as _QFrame,
                QPushButton as _QPushButton,
                QTextEdit as _QTextEdit,
                QLineEdit as _QLineEdit,
                QProgressBar as _QProgressBar,
                QSizePolicy,
            )
            from PyQt6.QtCore import (
                QTimer as _QTimer,
                Qt as _Qt,
            )
            from PyQt6.QtGui import (
                QColor as _QColor,
                QPainter as _QPainter,
                QBrush as _QBrush,
                QPen as _QPen,
                QFont as _QFont,
                QPixmap as _QPixmap,
                QImage as _QImage,
            )
            from PyQt6.QtOpenGLWidgets import QOpenGLWidget as _QOpenGLWidget
            
            QApplication = _QApplication
            QMainWindow = _QMainWindow
            QWidget = _QWidget
            QVBoxLayout = _QVBoxLayout
            QHBoxLayout = _QHBoxLayout
            QGridLayout = _QGridLayout
            QLabel = _QLabel
            QFrame = _QFrame
            QPushButton = _QPushButton
            QTextEdit = _QTextEdit
            QLineEdit = _QLineEdit
            QProgressBar = _QProgressBar
            QTimer = _QTimer
            Qt = _Qt
            QColor = _QColor
            QPainter = _QPainter
            QBrush = _QBrush
            QPen = _QPen
            QFont = _QFont
            QPixmap = _QPixmap
            QImage = _QImage
            QOpenGLWidget = _QOpenGLWidget
            
        except ImportError as e:
            logger.error(f"PyQt6 not installed: {e}")
            logger.error("Run: pip install PyQt6 PyOpenGL")
            raise

# Load PyQt6 at import time so classes can inherit from QWidget
try:
    _lazy_load()
except ImportError:
    # PyQt6 not available - classes will fail to define but that's OK
    # The module can still be imported without PyQt6
    pass


# Custom dark theme stylesheet
DARK_STYLESHEET = """
QMainWindow {
    background-color: #0a0a0f;
}

QWidget {
    background-color: transparent;
    color: #ffffff;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

QFrame {
    background-color: rgba(15, 15, 25, 200);
    border: 1px solid rgba(100, 100, 150, 50);
    border-radius: 12px;
}

QLabel {
    background-color: transparent;
    color: #ffffff;
    border: none;
}

QPushButton {
    background-color: rgba(99, 102, 241, 50);
    color: #ffffff;
    border: 1px solid rgba(99, 102, 241, 100);
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(99, 102, 241, 100);
}

QPushButton:pressed {
    background-color: rgba(99, 102, 241, 150);
}

QLineEdit {
    background-color: rgba(255, 255, 255, 10);
    color: #ffffff;
    border: 1px solid rgba(100, 100, 150, 80);
    border-radius: 8px;
    padding: 10px 15px;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid rgba(99, 102, 241, 200);
}

QTextEdit {
    background-color: rgba(15, 15, 25, 150);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
}

QProgressBar {
    background-color: rgba(255, 255, 255, 20);
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #06b6d4);
    border-radius: 3px;
}
"""


class ParticleGlobeWidget(QWidget):
    """
    OpenGL-like particle globe rendered with QPainter.
    Voice-reactive animation with 3D sphere of particles.
    """
    
    def __init__(self, parent=None):
        _lazy_load()
        super().__init__(parent)
        
        self.setMinimumSize(300, 300)
        
        # Particle system
        self.particle_count = 500
        self.particles = []
        self.sphere_radius = 100
        
        # Animation state
        self.voice_amplitude = 0.0
        self.target_amplitude = 0.0
        self.is_speaking = False
        self.rotation = 0.0
        self.time = 0.0
        
        # Colors
        self.primary_color = QColor(99, 102, 241)    # Purple
        self.secondary_color = QColor(6, 182, 212)  # Cyan
        self.accent_color = QColor(236, 72, 153)    # Pink
        
        # Initialize particles
        self._init_particles()
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)  # ~60fps
    
    def _init_particles(self):
        """Create particles distributed on a sphere."""
        self.particles = []
        
        for i in range(self.particle_count):
            # Fibonacci sphere distribution
            phi = math.acos(1 - 2 * (i + 0.5) / self.particle_count)
            theta = math.pi * (1 + math.sqrt(5)) * (i + 0.5)
            
            x = math.sin(phi) * math.cos(theta)
            y = math.sin(phi) * math.sin(theta)
            z = math.cos(phi)
            
            # Random color selection
            if i % 3 == 0:
                color = self.primary_color
            elif i % 3 == 1:
                color = self.secondary_color
            else:
                color = self.accent_color
            
            self.particles.append({
                'x': x, 'y': y, 'z': z,
                'ox': x, 'oy': y, 'oz': z,  # Original positions
                'color': color,
                'size': 2 + (i % 3),
            })
    
    def update_voice(self, amplitude: float, is_speaking: bool):
        """Update voice amplitude for animation."""
        self.target_amplitude = amplitude
        self.is_speaking = is_speaking
    
    def set_mood(self, mood: str):
        """Change colors based on mood."""
        mood_colors = {
            'happy': (QColor(34, 197, 94), QColor(6, 182, 212)),
            'sad': (QColor(99, 102, 241), QColor(59, 130, 246)),
            'excited': (QColor(249, 115, 22), QColor(236, 72, 153)),
            'thinking': (QColor(168, 85, 247), QColor(99, 102, 241)),
            'speaking': (QColor(236, 72, 153), QColor(139, 92, 246)),
            'neutral': (QColor(99, 102, 241), QColor(6, 182, 212)),
        }
        
        colors = mood_colors.get(mood.lower(), mood_colors['neutral'])
        self.primary_color = colors[0]
        self.secondary_color = colors[1]
        
        # Update particle colors
        for i, p in enumerate(self.particles):
            if i % 2 == 0:
                p['color'] = self.primary_color
            else:
                p['color'] = self.secondary_color
    
    def _animate(self):
        """Animation tick."""
        self.time += 0.02
        self.rotation += 0.01
        
        # Smooth amplitude transition
        self.voice_amplitude += (self.target_amplitude - self.voice_amplitude) * 0.1
        
        # Update particles
        for p in self.particles:
            # Wave effect
            wave = math.sin(self.time * 2 + p['oy'] * 3) * 0.05
            
            # Voice reactive
            voice_wave = 0
            if self.is_speaking:
                voice_wave = math.sin(self.time * 10 + p['oz'] * 5) * self.voice_amplitude * 0.3
            
            # Breathing when idle
            breathe = math.sin(self.time * 0.5) * 0.02
            
            # Apply displacement
            scale = 1 + wave + voice_wave + breathe
            p['x'] = p['ox'] * scale
            p['y'] = p['oy'] * scale
            p['z'] = p['oz'] * scale
        
        self.update()
    
    def paintEvent(self, event):
        """Render particles."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Center of widget
        cx = self.width() // 2
        cy = self.height() // 2
        
        # Sort particles by z for depth
        sorted_particles = sorted(self.particles, key=lambda p: 
            p['x'] * math.sin(self.rotation) + p['z'] * math.cos(self.rotation))
        
        for p in sorted_particles:
            # 3D rotation around Y axis
            x = p['x'] * math.cos(self.rotation) - p['z'] * math.sin(self.rotation)
            z = p['x'] * math.sin(self.rotation) + p['z'] * math.cos(self.rotation)
            y = p['y']
            
            # Project to 2D
            scale = 1 / (1 - z * 0.3)  # Perspective
            sx = int(cx + x * self.sphere_radius * scale)
            sy = int(cy + y * self.sphere_radius * scale)
            
            # Size based on depth
            size = int(p['size'] * scale)
            
            # Alpha based on depth
            alpha = int(100 + z * 100)
            color = QColor(p['color'])
            color.setAlpha(min(255, max(50, alpha)))
            
            # Draw particle
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(sx - size, sy - size, size * 2, size * 2)
        
        # Draw glow ring
        pen = QPen(QColor(99, 102, 241, 30))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(cx - self.sphere_radius - 20, cy - self.sphere_radius - 20,
                           (self.sphere_radius + 20) * 2, (self.sphere_radius + 20) * 2)


class MetricBar(QWidget):
    """Custom metric bar with label and progress."""
    
    def __init__(self, label: str, parent=None):
        _lazy_load()
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Label
        self.label = QLabel(label)
        self.label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px;")
        layout.addWidget(self.label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        layout.addWidget(self.progress)
        
        # Value label
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("color: #06b6d4; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.value_label)
    
    def set_value(self, value: float, text: str = None):
        self.progress.setValue(int(min(100, max(0, value))))
        if text:
            self.value_label.setText(text)


class ZaraNativeWindow(QMainWindow):
    """
    ZARA's Native Desktop Dashboard.
    Ultra-advanced UI with particle globe, camera, transcript, and metrics.
    No browser required - runs completely offline.
    """
    
    def __init__(self, zara=None):
        _lazy_load()
        super().__init__()
        
        self.zara = zara
        self.is_running = True
        
        self.setWindowTitle("ZARA AI - Command Center")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(DARK_STYLESHEET)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Header
        self._create_header(main_layout)
        
        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        # Left panel - Camera
        self._create_camera_panel(content_layout)
        
        # Center panel - Globe
        self._create_globe_panel(content_layout)
        
        # Right panel - Transcript
        self._create_transcript_panel(content_layout)
        
        main_layout.addLayout(content_layout, 1)
        
        # Metrics bar
        self._create_metrics_bar(main_layout)
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_state)
        self.update_timer.start(100)  # 10 FPS for state updates
    
    def _create_header(self, parent_layout):
        """Create header with logo and tabs."""
        header = QFrame()
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo
        logo = QLabel("⬡ ZARA")
        logo.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6366f1, stop:1 #06b6d4);
        """)
        header_layout.addWidget(logo)
        
        # Tabs
        tabs = ["DASHBOARD", "CONTACTS", "NOTES", "PHONE", "CALLS"]
        for i, tab in enumerate(tabs):
            btn = QPushButton(tab)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: rgba(255,255,255,0.6);
                    font-size: 11px;
                    font-weight: 600;
                    padding: 8px 16px;
                    letter-spacing: 1px;
                }
                QPushButton:hover {
                    color: rgba(255,255,255,1);
                }
            """ if i > 0 else """
                QPushButton {
                    background-color: rgba(99, 102, 241, 0.2);
                    border: 1px solid rgba(99, 102, 241, 0.5);
                    color: #06b6d4;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 8px 16px;
                    letter-spacing: 1px;
                    border-radius: 8px;
                }
            """)
            header_layout.addWidget(btn)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #22c55e; font-size: 14px;")
        header_layout.addWidget(self.status_dot)
        
        self.status_text = QLabel("ONLINE")
        self.status_text.setStyleSheet("color: #22c55e; font-size: 11px; font-weight: 600;")
        header_layout.addWidget(self.status_text)
        
        # Time
        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 14px; margin-left: 20px;")
        header_layout.addWidget(self.time_label)
        
        parent_layout.addWidget(header)
    
    def _create_camera_panel(self, parent_layout):
        """Create camera/vision panel."""
        panel = QFrame()
        panel.setFixedWidth(280)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("👁 VISUAL INPUT")
        header.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px; font-weight: 600; letter-spacing: 1.5px;")
        panel_layout.addWidget(header)
        
        # Camera feed placeholder
        self.camera_label = QLabel("Connecting to camera...")
        self.camera_label.setFixedHeight(200)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("""
            background-color: rgba(0,0,0,0.3);
            border-radius: 8px;
            color: rgba(255,255,255,0.4);
            font-size: 12px;
        """)
        panel_layout.addWidget(self.camera_label)
        
        # Vision stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: transparent; border: none;")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(10)
        
        stats = [
            ("Face", "faceLabel", "--"),
            ("Emotion", "emotionLabel", "--"),
            ("Attention", "attentionLabel", "--"),
        ]
        
        for i, (label, attr, default) in enumerate(stats):
            lbl = QLabel(label)
            lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 10px;")
            stats_layout.addWidget(lbl, 0, i)
            
            val = QLabel(default)
            val.setStyleSheet("color: #06b6d4; font-size: 12px; font-weight: 600;")
            setattr(self, attr, val)
            stats_layout.addWidget(val, 1, i)
        
        panel_layout.addWidget(stats_frame)
        panel_layout.addStretch()
        
        parent_layout.addWidget(panel)
    
    def _create_globe_panel(self, parent_layout):
        """Create center globe panel."""
        panel = QFrame()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("🌐 AI CORE SYSTEM")
        header.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px; font-weight: 600; letter-spacing: 1.5px;")
        panel_layout.addWidget(header)
        
        # Globe
        self.globe = ParticleGlobeWidget()
        panel_layout.addWidget(self.globe, 1)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        # Mood
        mood_layout = QHBoxLayout()
        mood_label = QLabel("MOOD:")
        mood_label.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px;")
        mood_layout.addWidget(mood_label)
        
        self.mood_value = QLabel("NEUTRAL")
        self.mood_value.setStyleSheet("color: #6366f1; font-size: 13px; font-weight: 600;")
        mood_layout.addWidget(self.mood_value)
        
        bottom_layout.addLayout(mood_layout)
        bottom_layout.addStretch()
        
        # End button
        end_btn = QPushButton("⏹ END")
        end_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.05);
                border: 1px solid rgba(100,100,150,0.3);
                color: rgba(255,255,255,0.6);
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: rgba(239,68,68,0.2);
                border-color: #ef4444;
                color: #ef4444;
            }
        """)
        bottom_layout.addWidget(end_btn)
        
        panel_layout.addLayout(bottom_layout)
        
        parent_layout.addWidget(panel, 1)
    
    def _create_transcript_panel(self, parent_layout):
        """Create transcript/chat panel."""
        panel = QFrame()
        panel.setFixedWidth(320)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("💬 TRANSCRIPT")
        header.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px; font-weight: 600; letter-spacing: 1.5px;")
        panel_layout.addWidget(header)
        
        # Transcript area
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 15, 25, 150);
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self.transcript.setHtml("<p style='color: rgba(255,255,255,0.5);'>Initializing systems...</p>")
        panel_layout.addWidget(self.transcript, 1)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.text_input)
        
        send_btn = QPushButton("➤")
        send_btn.setFixedWidth(44)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #06b6d4);
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }
        """)
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        panel_layout.addLayout(input_layout)
        
        parent_layout.addWidget(panel)
    
    def _create_metrics_bar(self, parent_layout):
        """Create bottom metrics bar."""
        bar = QFrame()
        bar.setFixedHeight(80)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(20, 10, 20, 10)
        bar_layout.setSpacing(40)
        
        # GPU
        self.gpu_metric = MetricBar("GPU TEMP")
        bar_layout.addWidget(self.gpu_metric)
        
        # VRAM
        self.vram_metric = MetricBar("VRAM")
        bar_layout.addWidget(self.vram_metric)
        
        # CPU
        self.cpu_metric = MetricBar("CPU")
        bar_layout.addWidget(self.cpu_metric)
        
        # RAM
        self.ram_metric = MetricBar("RAM")
        bar_layout.addWidget(self.ram_metric)
        
        bar_layout.addStretch()
        
        # Status
        status_layout = QVBoxLayout()
        status_lbl = QLabel("STATUS")
        status_lbl.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px;")
        status_layout.addWidget(status_lbl)
        
        self.status_value = QLabel("AWAKE")
        self.status_value.setStyleSheet("""
            background-color: rgba(99,102,241,0.2);
            color: #6366f1;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        """)
        status_layout.addWidget(self.status_value)
        
        bar_layout.addLayout(status_layout)
        
        parent_layout.addWidget(bar)
    
    def _send_message(self):
        """Handle sending a message."""
        text = self.text_input.text().strip()
        if not text:
            return
        
        # Add to transcript
        self.add_transcript("You", text)
        self.text_input.clear()
        
        # Send to ZARA if connected
        if self.zara and hasattr(self.zara, 'process_input'):
            threading.Thread(target=lambda: self.zara.process_input(text)).start()
    
    def add_transcript(self, speaker: str, text: str):
        """Add message to transcript."""
        color = "#06b6d4" if speaker == "You" else "#6366f1"
        html = f"""
            <p style='margin: 10px 0;'>
                <span style='color: {color}; font-weight: 600; font-size: 11px;'>{speaker}</span><br>
                <span style='color: white;'>{text}</span>
            </p>
        """
        current = self.transcript.toHtml()
        self.transcript.setHtml(current + html)
        self.transcript.verticalScrollBar().setValue(self.transcript.verticalScrollBar().maximum())
    
    def update_voice(self, amplitude: float, is_speaking: bool):
        """Update voice state for globe animation."""
        if hasattr(self, 'globe'):
            self.globe.update_voice(amplitude, is_speaking)
    
    def update_mood(self, mood: str):
        """Update mood display."""
        self.mood_value.setText(mood.upper())
        if hasattr(self, 'globe'):
            self.globe.set_mood(mood)
    
    def update_status(self, status: str):
        """Update ZARA status."""
        self.status_value.setText(status.upper())
    
    def update_metrics(self, gpu_temp=None, vram_used=None, vram_total=5.5, 
                       cpu_percent=None, ram_percent=None):
        """Update system metrics."""
        if gpu_temp is not None:
            self.gpu_metric.set_value(gpu_temp, f"{gpu_temp:.0f}°C")
        if vram_used is not None:
            pct = (vram_used / vram_total) * 100
            self.vram_metric.set_value(pct, f"{vram_used:.1f}GB")
        if cpu_percent is not None:
            self.cpu_metric.set_value(cpu_percent, f"{cpu_percent:.0f}%")
        if ram_percent is not None:
            self.ram_metric.set_value(ram_percent, f"{ram_percent:.0f}%")
    
    def update_camera(self, frame):
        """Update camera feed with frame."""
        if frame is not None:
            try:
                import cv2
                import numpy as np
                
                # Convert to RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                
                # Create QImage
                bytes_per_line = ch * w
                qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Scale to fit
                pixmap = QPixmap.fromImage(qimg).scaled(
                    self.camera_label.width(), 
                    self.camera_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
                self.camera_label.setPixmap(pixmap)
            except Exception as e:
                logger.debug(f"Camera update error: {e}")
    
    def _update_state(self):
        """Periodic state update."""
        import time
        
        # Update time
        self.time_label.setText(time.strftime("%H:%M"))
        
        # Update from ZARA if connected
        if self.zara:
            # Get metrics
            if hasattr(self.zara, 'optimizer') and self.zara.optimizer:
                stats = self.zara.optimizer.get_stats()
                if stats:
                    self.update_metrics(
                        gpu_temp=stats.get('gpu_temp', 0),
                        vram_used=stats.get('vram_used', 0),
                        cpu_percent=stats.get('cpu_percent', 0),
                        ram_percent=stats.get('ram_percent', 0)
                    )
            
            # Get camera frame
            if hasattr(self.zara, 'eyes') and self.zara.eyes:
                try:
                    frame = self.zara.eyes.get_frame()
                    self.update_camera(frame)
                except:
                    pass
    
    def closeEvent(self, event):
        """Handle window close."""
        self.is_running = False
        if self.zara:
            # Signal ZARA to start shutdown
            pass
        event.accept()


class NativeDashboardManager:
    """
    Manages the native PyQt6 dashboard.
    Runs in separate thread to not block ZARA.
    """
    
    def __init__(self):
        self.app = None
        self.window = None
        self.thread = None
        self.zara = None
        self.is_running = False
    
    def start(self, zara=None):
        """Start dashboard in separate thread."""
        self.zara = zara
        self.is_running = True
        
        self.thread = threading.Thread(target=self._run_app, daemon=True)
        self.thread.start()
        
        logger.info("🖥️ Native Dashboard started")
    
    def _run_app(self):
        """Run the PyQt application."""
        try:
            _lazy_load()
            
            self.app = QApplication(sys.argv)
            self.window = ZaraNativeWindow(self.zara)
            self.window.show()
            
            self.app.exec()
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
    
    def stop(self):
        """Stop dashboard."""
        self.is_running = False
        if self.window:
            self.window.close()
    
    # Forwarding methods
    def update_voice(self, amplitude: float, is_speaking: bool):
        if self.window:
            self.window.update_voice(amplitude, is_speaking)
    
    def update_mood(self, mood: str):
        if self.window:
            self.window.update_mood(mood)
    
    def update_status(self, status: str):
        if self.window:
            self.window.update_status(status)
    
    def add_transcript(self, speaker: str, text: str):
        if self.window:
            self.window.add_transcript(speaker, text)


# Singleton
_native_dashboard: Optional[NativeDashboardManager] = None

def get_native_dashboard() -> NativeDashboardManager:
    """Get or create native dashboard manager."""
    global _native_dashboard
    if _native_dashboard is None:
        _native_dashboard = NativeDashboardManager()
    return _native_dashboard


if __name__ == "__main__":
    # Test standalone
    logging.basicConfig(level=logging.INFO)
    
    _lazy_load()
    app = QApplication(sys.argv)
    window = ZaraNativeWindow()
    window.show()
    
    # Test voice animation
    def test_voice():
        import random
        window.globe.update_voice(random.random() * 0.8, True)
        QTimer.singleShot(100, test_voice)
    
    QTimer.singleShot(1000, test_voice)
    
    sys.exit(app.exec())
