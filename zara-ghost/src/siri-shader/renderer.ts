import { VERTEX_SHADER } from './vertex.glsl';
import { WAVE_FRAGMENT_SHADER } from './wave.frag.glsl';
import { DOTS_FRAGMENT_SHADER } from './dots.frag.glsl';
import { BACKGROUND_FRAGMENT_SHADER } from './background.frag.glsl';
import { EFFECT_COMPOSITE_FRAGMENT_SHADER } from './effect-composite.frag.glsl';
import { GLASS_COMPOSITE_FRAGMENT_SHADER } from './glass-composite.frag.glsl';
import { WAVE_PRESETS, waveUniforms, dotsUniforms } from './uniforms';
import type { WavePreset, UniformEntry } from './uniforms';
import type { SiriSurface, SiriProgress, AudioBands, SiriSizes } from './state';

const MAX_DPR = 2;
const PANEL_MARGIN_PX = 20;
const EFFECT_OVERDRAW = 1.18;
const CORNER_RADIUS_MAX_PX = 44;

interface ProgramEntry {
  label: string;
  program: WebGLProgram;
  uniforms: Map<string, WebGLUniformLocation | null>;
  types: Map<string, string>;
  values: Map<string, number[]>;
}

interface RenderTarget {
  framebuffer: WebGLFramebuffer;
  texture: WebGLTexture;
  width: number;
  height: number;
}

interface RenderLayout {
  effectWidth: number;
  effectHeight: number;
  effectOrigin: number[];
  effectSize: number[];
  panelOrigin: number[];
  panelSize: number[];
  margin: number;
  cornerRadius: number;
  containerStrength: number;
}

interface TextureBinding {
  name: string;
  texture: WebGLTexture;
  unit: number;
}

interface RenderParams {
  surface: SiriSurface;
  progress: SiriProgress[];
  bands: AudioBands;
  sizes: SiriSizes;
  dt?: number;
}

function cornerRadiusFor(coreWidth: number, coreHeight: number, answer: number, dpr: number): number {
  const half = Math.min(coreWidth, coreHeight) * 0.5;
  const t = Math.max(0, Math.min(1, answer));
  const ceiling = half + (CORNER_RADIUS_MAX_PX * dpr - half) * t;
  return Math.min(half, ceiling);
}

function toNumberArray(value: number | boolean | number[] | Float32Array): number[] {
  if (typeof value === 'number' || typeof value === 'boolean') return [Number(value)];
  if (Array.isArray(value)) return value.flat(Infinity).map(Number);
  if (ArrayBuffer.isView(value)) return Array.from(value as Float32Array, Number);
  return [];
}

function inferUniformType(declared: string | undefined, value: number | number[]): string {
  if (declared) return declared;
  if (typeof value === 'boolean') return 'bool';
  if (typeof value === 'number') return 'float';
  const list = toNumberArray(value);
  if (list.length === 2) return 'vec2';
  if (list.length === 3) return 'vec3';
  if (list.length === 4) return 'vec4';
  if (list.length === 9) return 'mat3';
  if (list.length === 16) return 'mat4';
  return 'float';
}

function arraysEqual(a: number[], b: number[]): boolean {
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

function compileShader(gl: WebGL2RenderingContext, type: number, source: string, label: string): WebGLShader {
  const shader = gl.createShader(type)!;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader) || `Unknown ${label} shader compile error.`;
    gl.deleteShader(shader);
    throw new Error(message);
  }
  return shader;
}

function createProgram(gl: WebGL2RenderingContext, fragmentSource: string, label: string): ProgramEntry {
  const vertex = compileShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER, `${label} vertex`);
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, fragmentSource, `${label} fragment`);
  const program = gl.createProgram()!;
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  gl.deleteShader(vertex);
  gl.deleteShader(fragment);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const message = gl.getProgramInfoLog(program) || `Unknown ${label} program link error.`;
    gl.deleteProgram(program);
    throw new Error(message);
  }
  return { label, program, uniforms: new Map(), types: new Map(), values: new Map() };
}

function createLinearClampTexture(gl: WebGL2RenderingContext): WebGLTexture {
  const texture = gl.createTexture()!;
  gl.bindTexture(gl.TEXTURE_2D, texture);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  return texture;
}

function createRenderTarget(gl: WebGL2RenderingContext, width: number, height: number): RenderTarget {
  const texture = createLinearClampTexture(gl);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, width, height, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
  const framebuffer = gl.createFramebuffer()!;
  gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
  if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) {
    gl.deleteFramebuffer(framebuffer);
    gl.deleteTexture(texture);
    throw new Error('Framebuffer is incomplete.');
  }
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  return { framebuffer, texture, width, height };
}

function destroyRenderTarget(gl: WebGL2RenderingContext, target: RenderTarget | null): void {
  if (!target) return;
  gl.deleteFramebuffer(target.framebuffer);
  gl.deleteTexture(target.texture);
}

export class SiriRenderer {
  private canvas: HTMLCanvasElement;
  private gl: WebGL2RenderingContext;
  private wavePreset: WavePreset;
  private dpr = 1;
  private width = 1;
  private height = 1;
  private time = 0;
  public panelOffset: number[] = [0, 0];
  private backgroundSize: number[] = [1, 1];
  private backgroundReady = 0;
  private backgroundTexture: WebGLTexture | null = null;
  private effectTarget: RenderTarget | null = null;
  private sceneTarget: RenderTarget | null = null;
  private disposed = false;
  public error: Error | null = null;
  private vertexArray: WebGLVertexArrayObject | null = null;
  private programs!: {
    wave: ProgramEntry;
    dots: ProgramEntry;
    background: ProgramEntry;
    effectComposite: ProgramEntry;
    glassComposite: ProgramEntry;
  };
  public container = { black: 0.28, fade: 0.55, gauss: 12.0, strength: 0.95 };
  public chipLenses = {
    rects: [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]] as number[][],
    states: [0, 0, 0],
    hovers: [0, 0, 0],
  };

  constructor(canvas: HTMLCanvasElement, wavePreset: string = 'bloom') {
    this.canvas = canvas;
    this.wavePreset = (WAVE_PRESETS as Record<string, WavePreset>)[wavePreset] || WAVE_PRESETS.bloom;
    const gl = canvas.getContext('webgl2', {
      alpha: true,
      antialias: false,
      depth: false,
      stencil: false,
      premultipliedAlpha: true,
      preserveDrawingBuffer: false,
    });
    if (!gl) {
      this.error = new Error('WebGL2 is not available.');
      throw this.error;
    }
    this.gl = gl;
    this._initGL();
  }

  private _initGL(): void {
    const gl = this.gl;
    this.vertexArray = gl.createVertexArray();
    this.programs = {
      wave: createProgram(gl, WAVE_FRAGMENT_SHADER, 'wave'),
      dots: createProgram(gl, DOTS_FRAGMENT_SHADER, 'dots'),
      background: createProgram(gl, BACKGROUND_FRAGMENT_SHADER, 'background'),
      effectComposite: createProgram(gl, EFFECT_COMPOSITE_FRAGMENT_SHADER, 'effect composite'),
      glassComposite: createProgram(gl, GLASS_COMPOSITE_FRAGMENT_SHADER, 'glass composite'),
    };
    this.backgroundTexture = createLinearClampTexture(gl);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));
    gl.bindVertexArray(this.vertexArray);
    gl.disable(gl.DEPTH_TEST);
    gl.disable(gl.STENCIL_TEST);
    this.backgroundReady = 0;
    this.backgroundSize = [1, 1];
    this.effectTarget = null;
    this.sceneTarget = null;
  }

  public setBackground(image: HTMLImageElement | HTMLCanvasElement): void {
    const gl = this.gl;
    if (!gl || !this.backgroundTexture) return;
    gl.bindTexture(gl.TEXTURE_2D, this.backgroundTexture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    this.backgroundSize = [
      (image as HTMLImageElement).naturalWidth || image.width,
      (image as HTMLImageElement).naturalHeight || image.height,
    ];
    this.backgroundReady = 1;
  }

  public setBackgroundData(imageData: ImageData): void {
    const gl = this.gl;
    if (!gl || !this.backgroundTexture) return;
    gl.bindTexture(gl.TEXTURE_2D, this.backgroundTexture);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, imageData.width, imageData.height, 0, gl.RGBA, gl.UNSIGNED_BYTE, imageData.data);
    this.backgroundSize = [imageData.width, imageData.height];
    this.backgroundReady = 1;
  }

  public render(params: RenderParams): void {
    if (!this.gl || this.disposed || this.error) return;
    const { surface, progress, bands, sizes, dt = 0 } = params;
    this.time = (this.time + Math.max(0, Math.min(dt, 0.1))) % 1e5;
    this._resize();
    const layout = this._layout(surface, sizes);
    this._ensureTargets(layout);
    this._renderEffectPass(surface, progress, bands, layout);
    this._renderScenePass(layout);
    this._renderGlassPass(layout);
  }

  public dispose(): void {
    const gl = this.gl;
    if (!gl || this.disposed) return;
    destroyRenderTarget(gl, this.effectTarget);
    destroyRenderTarget(gl, this.sceneTarget);
    if (this.backgroundTexture) gl.deleteTexture(this.backgroundTexture);
    for (const entry of Object.values(this.programs || {})) {
      gl.deleteProgram((entry as ProgramEntry).program);
    }
    if (this.vertexArray) gl.deleteVertexArray(this.vertexArray);
    this.effectTarget = null;
    this.sceneTarget = null;
    this.backgroundTexture = null;
    this.disposed = true;
  }

  private _resize(): void {
    const cssWidth = Math.max(1, this.canvas.clientWidth || window.innerWidth || 1);
    const cssHeight = Math.max(1, this.canvas.clientHeight || window.innerHeight || 1);
    const dpr = Math.min(MAX_DPR, Math.max(1, window.devicePixelRatio || 1));
    const width = Math.max(1, Math.round(cssWidth * dpr));
    const height = Math.max(1, Math.round(cssHeight * dpr));
    if (width === this.width && height === this.height && dpr === this.dpr) return;
    this.dpr = dpr;
    this.width = width;
    this.height = height;
    this.canvas.width = width;
    this.canvas.height = height;
  }

  private _layout(surface: SiriSurface, sizes: SiriSizes): RenderLayout {
    const pressScale = 1 + surface.press * 0.018;
    const margin = PANEL_MARGIN_PX * this.dpr;
    const answer = surface.answer || 0;
    const baseSize = sizes.expanded.width * this.dpr;
    const answerWidth = Math.min(sizes.answer.width * this.dpr, this.width - 48 * this.dpr);
    const answerHeight = sizes.answer.height * this.dpr;
    const coreWidth = (baseSize + (answerWidth - baseSize) * answer) * pressScale;
    const coreHeight = (baseSize + (answerHeight - baseSize) * answer) * pressScale;
    const panelWidth = coreWidth + margin * 2;
    const panelHeight = coreHeight + margin * 2;
    const effectWidth = Math.max(1, Math.round(coreWidth * EFFECT_OVERDRAW));
    const effectHeight = Math.max(1, Math.round(coreHeight * EFFECT_OVERDRAW));
    const panelX = (this.width - panelWidth) * 0.5 + this.panelOffset[0];
    const panelY = (this.height - panelHeight) * 0.5 + this.panelOffset[1];
    const panelCenterY = panelY + panelHeight * 0.5;
    return {
      effectWidth,
      effectHeight,
      effectOrigin: [(this.width - effectWidth) * 0.5 + this.panelOffset[0], panelCenterY - effectHeight * 0.5],
      effectSize: [effectWidth, effectHeight],
      panelOrigin: [panelX, panelY],
      panelSize: [panelWidth, panelHeight],
      margin,
      cornerRadius: cornerRadiusFor(coreWidth, coreHeight, answer, this.dpr),
      containerStrength: this.container.strength * Math.min(1, Math.max(0, Math.max(surface.sharedResolved || 0, answer * 0.85))),
    };
  }

  private _ensureTargets(layout: RenderLayout): void {
    const gl = this.gl;
    if (!this.effectTarget || this.effectTarget.width !== layout.effectWidth || this.effectTarget.height !== layout.effectHeight) {
      destroyRenderTarget(gl, this.effectTarget);
      this.effectTarget = createRenderTarget(gl, layout.effectWidth, layout.effectHeight);
    }
    if (!this.sceneTarget || this.sceneTarget.width !== this.width || this.sceneTarget.height !== this.height) {
      destroyRenderTarget(gl, this.sceneTarget);
      this.sceneTarget = createRenderTarget(gl, this.width, this.height);
    }
  }

  private _renderEffectPass(surface: SiriSurface, progress: SiriProgress[], bands: AudioBands, layout: RenderLayout): void {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.effectTarget!.framebuffer);
    gl.viewport(0, 0, layout.effectWidth, layout.effectHeight);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.enable(gl.BLEND);
    gl.blendEquation(gl.FUNC_ADD);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    const shared: UniformEntry[] = [
      { name: 'uResolution', type: 'vec2', value: [layout.effectWidth, layout.effectHeight] },
      { name: 'uTime', value: this.time },
      { name: 'uMouse', type: 'vec4', value: [layout.effectWidth * 0.5, layout.effectHeight * 0.5, surface.press, 0] },
    ];
    this._draw(this.programs.wave, [...shared, ...waveUniforms(surface, bands, this.wavePreset)]);
    this._draw(this.programs.dots, [...shared, ...dotsUniforms(surface, progress)]);
    gl.disable(gl.BLEND);
  }

  private _renderScenePass(layout: RenderLayout): void {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.sceneTarget!.framebuffer);
    gl.viewport(0, 0, this.width, this.height);
    gl.clearColor(0, 0, 0, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    this._draw(
      this.programs.background,
      [
        { name: 'uResolution', type: 'vec2', value: [this.width, this.height] },
        { name: 'uTextureSize', type: 'vec2', value: this.backgroundSize },
        { name: 'uCanvasSize', type: 'vec2', value: [this.width, this.height] },
        { name: 'uBackgroundReady', value: this.backgroundReady },
      ],
      [{ name: 'uBackground', texture: this.backgroundTexture!, unit: 0 }],
    );
    gl.enable(gl.BLEND);
    gl.blendEquation(gl.FUNC_ADD);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    this._draw(
      this.programs.effectComposite,
      [
        { name: 'uResolution', type: 'vec2', value: [this.width, this.height] },
        { name: 'uCanvasSize', type: 'vec2', value: [this.width, this.height] },
        { name: 'uEffectOrigin', type: 'vec2', value: layout.effectOrigin },
        { name: 'uEffectSize', type: 'vec2', value: layout.effectSize },
        { name: 'uContainer', value: layout.containerStrength },
        { name: 'uContainerBlack', value: this.container.black },
        { name: 'uContainerFade', value: this.container.fade },
        { name: 'uContainerGauss', value: this.container.gauss },
        { name: 'uContainerTint', type: 'vec3', value: [0.36, 0.04, 0.05] },
        { name: 'uAnger', value: 0 },
      ],
      [{ name: 'uEffectTexture', texture: this.effectTarget!.texture, unit: 0 }],
    );
    gl.disable(gl.BLEND);
  }

  private _renderGlassPass(layout: RenderLayout): void {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, this.width, this.height);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    this._draw(
      this.programs.glassComposite,
      [
        { name: 'uResolution', type: 'vec2', value: [this.width, this.height] },
        { name: 'uTextureSize', type: 'vec2', value: this.backgroundSize },
        { name: 'uPanelSize', type: 'vec2', value: layout.panelSize },
        { name: 'uCanvasSize', type: 'vec2', value: [this.width, this.height] },
        { name: 'uPanelOrigin', type: 'vec2', value: layout.panelOrigin },
        { name: 'uMarginPx', value: layout.margin },
        { name: 'uCornerRadius', value: layout.cornerRadius },
        { name: 'uHeight', value: 24 * this.dpr },
        { name: 'uCurvature', value: 1 },
        { name: 'uRefractAmount', value: -80 * this.dpr },
        { name: 'uAngle', value: 0 },
        { name: 'uGradRadialMix', value: 0.15 },
        { name: 'uKeyAngle', value: Math.PI * 0.25 },
        { name: 'uFillAngle', value: Math.PI * 1.25 },
        { name: 'uHlHeight', value: 3.5 * this.dpr },
        { name: 'uHlCut', value: 0.52 },
        { name: 'uHlNorm', value: 8 },
        { name: 'uHlAmount', value: 1.3 },
        { name: 'uHlCurv', value: 0.85 },
        { name: 'uBackgroundReady', value: this.backgroundReady },
        { name: 'uTransparentOutside', value: 1 },
        { name: 'uChip0', type: 'vec4', value: this.chipLenses.rects[0] },
        { name: 'uChip1', type: 'vec4', value: this.chipLenses.rects[1] },
        { name: 'uChip2', type: 'vec4', value: this.chipLenses.rects[2] },
        { name: 'uChipState', type: 'vec3', value: this.chipLenses.states },
        { name: 'uChipHover', type: 'vec3', value: this.chipLenses.hovers },
        { name: 'uChipRefract', value: -22 * this.dpr },
        { name: 'uChipHeight', value: 7 * this.dpr },
        { name: 'uChipHlAmount', value: 0.6 },
        { name: 'uChipFace', value: 0.1 },
      ],
      [
        { name: 'uSceneTexture', texture: this.sceneTarget!.texture, unit: 0 },
        { name: 'uBackground', texture: this.backgroundTexture!, unit: 1 },
      ],
    );
  }

  private _draw(programEntry: ProgramEntry, uniforms: UniformEntry[] = [], textures: TextureBinding[] = []): void {
    const gl = this.gl;
    gl.useProgram(programEntry.program);
    gl.bindVertexArray(this.vertexArray);
    for (const binding of textures) {
      this._setTexture(programEntry, binding.name, binding.texture, binding.unit);
    }
    for (const uniform of uniforms) {
      this._setUniform(programEntry, uniform.name, uniform.value, uniform.type);
    }
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  private _setTexture(programEntry: ProgramEntry, name: string, texture: WebGLTexture, unit: number): void {
    const gl = this.gl;
    const location = this._getUniformLocation(programEntry, name);
    if (location === null) return;
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.uniform1i(location, unit);
  }

  private _setUniform(programEntry: ProgramEntry, name: string, value: number | number[], declaredType?: string): void {
    if (!name) return;
    const gl = this.gl;
    const location = this._getUniformLocation(programEntry, name);
    if (location === null) return;
    let type = programEntry.types.get(name);
    if (type === undefined) {
      type = inferUniformType(declaredType, value);
      programEntry.types.set(name, type);
    }
    const list = toNumberArray(value);
    const previous = programEntry.values.get(name);
    if (previous !== undefined && previous.length === list.length && arraysEqual(previous, list)) return;
    programEntry.values.set(name, list);
    if (type === 'int' || type === 'sampler2D' || type === 'bool') gl.uniform1i(location, list[0] || 0);
    else if (type === 'vec2') gl.uniform2fv(location, list.slice(0, 2));
    else if (type === 'vec3') gl.uniform3fv(location, list.slice(0, 3));
    else if (type === 'vec4') gl.uniform4fv(location, list.slice(0, 4));
    else if (type === 'mat3') gl.uniformMatrix3fv(location, false, list.slice(0, 9));
    else if (type === 'mat4') gl.uniformMatrix4fv(location, false, list.slice(0, 16));
    else gl.uniform1f(location, list[0] || 0);
  }

  private _getUniformLocation(programEntry: ProgramEntry, name: string): WebGLUniformLocation | null {
    if (programEntry.uniforms.has(name)) return programEntry.uniforms.get(name)!;
    const location = this.gl.getUniformLocation(programEntry.program, name);
    programEntry.uniforms.set(name, location);
    return location;
  }
}
