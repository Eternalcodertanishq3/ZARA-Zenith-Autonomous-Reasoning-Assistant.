import { VERTEX_SHADER } from './vertex.glsl';
import { WAVE_FRAGMENT_SHADER } from './wave.frag.glsl';
import { WAVE_PRESETS } from './uniforms';

export class SiriRenderer {
  private gl: WebGL2RenderingContext;
  private program: WebGLProgram;
  private vao: WebGLVertexArrayObject;
  private uniforms: Record<string, WebGLUniformLocation> = {};
  private time = 0;

  constructor(canvas: HTMLCanvasElement) {
    const gl = canvas.getContext('webgl2', {
      alpha: true,
      antialias: true,
      premultipliedAlpha: true,
    });
    if (!gl) throw new Error('WebGL2 not supported');
    this.gl = gl;

    const vs = this.compileShader(gl.VERTEX_SHADER, VERTEX_SHADER);
    const fs = this.compileShader(gl.FRAGMENT_SHADER, WAVE_FRAGMENT_SHADER);
    const program = gl.createProgram()!;
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error('Shader link failed: ' + gl.getProgramInfoLog(program));
    }
    this.program = program;

    this.vao = gl.createVertexArray()!;
    this.initUniforms();
  }

  private compileShader(type: number, source: string): WebGLShader {
    const shader = this.gl.createShader(type)!;
    this.gl.shaderSource(shader, source);
    this.gl.compileShader(shader);
    if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
      const info = this.gl.getShaderInfoLog(shader);
      this.gl.deleteShader(shader);
      throw new Error('Shader compile failed: ' + info);
    }
    return shader;
  }

  private initUniforms() {
    const names = [
      'uResolution', 'uTime', 'uMouse', 'uResolved', 'uLayerOpacity',
      'uUnresolvedScale', 'uEffectScale', 'uAnchor', 'uAmplitude', 'uFreq',
      'uAberrationFreq', 'uWavePhase', 'uWaveSpeed', 'uWaveScale', 'uAberration',
      'uThickness', 'uIntensity', 'uFalloff', 'uEdgeMask', 'uEdgeMaskInset',
      'uBandFill', 'uBandFillThickness', 'uSoftness', 'uLow', 'uMid', 'uHigh',
      'uLowAmplitude', 'uLowIntensity', 'uMidAberration', 'uMidAberrationAmplitude',
      'uMidBandFill', 'uMidSoftness', 'uHighAberration', 'uHighAberrationAmplitude',
      'uWhiteClip'
    ];
    for (const name of names) {
      const loc = this.gl.getUniformLocation(this.program, name);
      if (loc) this.uniforms[name] = loc;
    }
  }

  public render() {
    const gl = this.gl;
    this.time += 0.016;

    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    gl.useProgram(this.program);
    gl.bindVertexArray(this.vao);

    // Set resolution & time
    if (this.uniforms.uResolution) gl.uniform2f(this.uniforms.uResolution, gl.canvas.width, gl.canvas.height);
    if (this.uniforms.uTime) gl.uniform1f(this.uniforms.uTime, this.time);
    if (this.uniforms.uMouse) gl.uniform4f(this.uniforms.uMouse, 0, 0, 0, 0);

    // Siri presets
    const p = WAVE_PRESETS.bloom;
    const wavePhase = this.time * 2.0;

    if (this.uniforms.uResolved) gl.uniform1f(this.uniforms.uResolved, 1.0);
    if (this.uniforms.uLayerOpacity) gl.uniform1f(this.uniforms.uLayerOpacity, 1.0);
    if (this.uniforms.uUnresolvedScale) gl.uniform1f(this.uniforms.uUnresolvedScale, p.uUnresolvedScale);
    if (this.uniforms.uEffectScale) gl.uniform1f(this.uniforms.uEffectScale, 1.0);
    if (this.uniforms.uAnchor) gl.uniform2f(this.uniforms.uAnchor, 0.5, 0.5);

    if (this.uniforms.uAmplitude) gl.uniform1f(this.uniforms.uAmplitude, p.uAmplitude);
    if (this.uniforms.uFreq) gl.uniform1f(this.uniforms.uFreq, p.uFreq);
    if (this.uniforms.uAberrationFreq) gl.uniform1f(this.uniforms.uAberrationFreq, p.uAberrationFreq);
    if (this.uniforms.uWavePhase) gl.uniform1f(this.uniforms.uWavePhase, wavePhase);
    if (this.uniforms.uWaveSpeed) gl.uniform1f(this.uniforms.uWaveSpeed, p.uWaveSpeed);
    if (this.uniforms.uWaveScale) gl.uniform1f(this.uniforms.uWaveScale, p.uWaveScale);
    if (this.uniforms.uAberration) gl.uniform1f(this.uniforms.uAberration, p.uAberration);
    if (this.uniforms.uThickness) gl.uniform1f(this.uniforms.uThickness, p.uThickness);
    if (this.uniforms.uIntensity) gl.uniform1f(this.uniforms.uIntensity, p.uIntensity);
    if (this.uniforms.uFalloff) gl.uniform1f(this.uniforms.uFalloff, p.uFalloff);
    if (this.uniforms.uEdgeMask) gl.uniform1f(this.uniforms.uEdgeMask, p.uEdgeMask);
    if (this.uniforms.uEdgeMaskInset) gl.uniform1f(this.uniforms.uEdgeMaskInset, p.uEdgeMaskInset);
    if (this.uniforms.uBandFill) gl.uniform1f(this.uniforms.uBandFill, p.uBandFill);
    if (this.uniforms.uBandFillThickness) gl.uniform1f(this.uniforms.uBandFillThickness, p.uBandFillThickness);
    if (this.uniforms.uSoftness) gl.uniform1f(this.uniforms.uSoftness, p.uSoftness);

    // Audio reactivity bands
    const audioLow = 0.2 + Math.sin(this.time * 3) * 0.1;
    const audioMid = 0.3 + Math.cos(this.time * 2.5) * 0.15;
    const audioHigh = 0.2 + Math.sin(this.time * 4) * 0.1;

    if (this.uniforms.uLow) gl.uniform1f(this.uniforms.uLow, audioLow);
    if (this.uniforms.uMid) gl.uniform1f(this.uniforms.uMid, audioMid);
    if (this.uniforms.uHigh) gl.uniform1f(this.uniforms.uHigh, audioHigh);

    if (this.uniforms.uLowAmplitude) gl.uniform1f(this.uniforms.uLowAmplitude, p.uLowAmplitude);
    if (this.uniforms.uLowIntensity) gl.uniform1f(this.uniforms.uLowIntensity, p.uLowIntensity);
    if (this.uniforms.uMidAberration) gl.uniform1f(this.uniforms.uMidAberration, p.uMidAberration);
    if (this.uniforms.uMidAberrationAmplitude) gl.uniform1f(this.uniforms.uMidAberrationAmplitude, p.uMidAberrationAmplitude);
    if (this.uniforms.uMidBandFill) gl.uniform1f(this.uniforms.uMidBandFill, p.uMidBandFill);
    if (this.uniforms.uMidSoftness) gl.uniform1f(this.uniforms.uMidSoftness, p.uMidSoftness);
    if (this.uniforms.uHighAberration) gl.uniform1f(this.uniforms.uHighAberration, p.uHighAberration);
    if (this.uniforms.uHighAberrationAmplitude) gl.uniform1f(this.uniforms.uHighAberrationAmplitude, p.uHighAberrationAmplitude);
    if (this.uniforms.uWhiteClip) gl.uniform1f(this.uniforms.uWhiteClip, p.uWhiteClip);

    // Draw full-screen triangle
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
}
