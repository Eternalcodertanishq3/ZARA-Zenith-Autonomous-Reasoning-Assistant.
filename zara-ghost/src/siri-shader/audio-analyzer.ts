import { Spring } from './spring';

const FFT_SIZE = 1024;
const FFT_HALF = FFT_SIZE / 2;
const SCRIPT_PROCESSOR_SIZE = 512;
const SPECTRUM_HOP_SIZE = 512;
const SPECTRUM_COOLDOWN_S = 1 / 60;
const BAND_SPRING = { response: 0.2, dampingRatio: 1 };
const LOW_MID_SPLIT_HZ = 500;
const MID_HIGH_SPLIT_HZ = 3000;
const PEAK_FLOOR = 8e-4;
const PEAK_DECAY = 0.9975;

function clamp01(value: number): number {
	return Math.max(0, Math.min(1, value));
}

function makeHanningWindow(): Float32Array {
	const values = new Float32Array(FFT_SIZE);
	for (let i = 0; i < FFT_SIZE; i += 1) {
		values[i] = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (FFT_SIZE - 1));
	}
	return values;
}

function makeBitReverseTable(): Uint16Array {
	const table = new Uint16Array(FFT_SIZE);
	const bits = Math.log2(FFT_SIZE);
	for (let i = 0; i < FFT_SIZE; i += 1) {
		let value = i;
		let reversed = 0;
		for (let bit = 0; bit < bits; bit += 1) {
			reversed = (reversed << 1) | (value & 1);
			value >>= 1;
		}
		table[i] = reversed;
	}
	return table;
}

export class AudioAnalyzer {
	public low = 0;
	public mid = 0;
	public high = 0;
	public running = false;

	private _rawLow = 0;
	private _rawMid = 0;
	private _rawHigh = 0;
	private _lowSpring = new Spring(0, BAND_SPRING);
	private _midSpring = new Spring(0, BAND_SPRING);
	private _highSpring = new Spring(0, BAND_SPRING);
	private _peakLow = 0.001;
	private _peakMid = 0.001;
	private _peakHigh = 0.001;
	private _context: AudioContext | null = null;
	private _source: MediaStreamAudioSourceNode | null = null;
	private _processor: ScriptProcessorNode | null = null;
	private _silentGain: GainNode | null = null;
	private _stream: MediaStream | null = null;
	private _sampleRate = 48000;
	private _ring = new Float32Array(FFT_SIZE);
	private _real = new Float32Array(FFT_SIZE);
	private _imag = new Float32Array(FFT_SIZE);
	private _mags = new Float32Array(FFT_HALF);
	private _window = makeHanningWindow();
	private _bitReverse = makeBitReverseTable();
	private _ringWrite = 0;
	private _pendingSamples = 0;
	private _spectrumCooldown = 0;

	public async start(): Promise<void> {
		if (this.running) return;
		if (!navigator.mediaDevices?.getUserMedia) {
			throw new Error('Microphone is not available in this browser.');
		}
		this._stream = await navigator.mediaDevices.getUserMedia({
			audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
		});

		const ContextClass = window.AudioContext || (window as any).webkitAudioContext;
		this._context = new ContextClass({ latencyHint: 'interactive' });
		this._sampleRate = this._context.sampleRate;
		this._silentGain = this._context.createGain();
		this._silentGain.gain.value = 0;

		this._source = this._context.createMediaStreamSource(this._stream);
		this._processor = this._context.createScriptProcessor(SCRIPT_PROCESSOR_SIZE, 1, 1);
		this._processor.onaudioprocess = (e) => this._process(e);

		this._source.connect(this._processor);
		this._processor.connect(this._silentGain);
		this._silentGain.connect(this._context.destination);

		if (this._context.state === 'suspended') {
			await this._context.resume();
		}
		this.running = true;
	}

	public stop(): void {
		if (this._processor) this._processor.onaudioprocess = null;
		if (this._source) this._source.disconnect();
		if (this._processor) this._processor.disconnect();
		if (this._silentGain) this._silentGain.disconnect();
		if (this._stream) {
			for (const track of this._stream.getTracks()) track.stop();
		}
		if (this._context && this._context.state !== 'closed') {
			this._context.close();
		}
		this._context = null;
		this._silentGain = null;
		this._source = null;
		this._processor = null;
		this._stream = null;
		this.running = false;

		this.low = 0;
		this.mid = 0;
		this.high = 0;
		this._rawLow = 0;
		this._rawMid = 0;
		this._rawHigh = 0;
		this._lowSpring.jump(0);
		this._midSpring.jump(0);
		this._highSpring.jump(0);
	}

	public update(dt: number): { low: number; mid: number; high: number } {
		if (this.running && this._processor) {
			this._maybeComputeSpectrum(dt);
		}
		this._lowSpring.setTarget(this._rawLow);
		this._midSpring.setTarget(this._rawMid);
		this._highSpring.setTarget(this._rawHigh);
		this.low = this._lowSpring.step(dt);
		this.mid = this._midSpring.step(dt);
		this.high = this._highSpring.step(dt);
		return { low: this.low, mid: this.mid, high: this.high };
	}

	private _process(event: AudioProcessingEvent): void {
		const input = event.inputBuffer.getChannelData(0);
		event.outputBuffer.getChannelData(0).fill(0);
		for (let i = 0; i < input.length; i += 1) {
			this._ring[this._ringWrite] = input[i];
			this._ringWrite = (this._ringWrite + 1) & (FFT_SIZE - 1);
		}
		this._pendingSamples += input.length;
	}

	private _maybeComputeSpectrum(dt: number): void {
		this._spectrumCooldown = Math.max(0, this._spectrumCooldown - dt);
		if (this._pendingSamples < SPECTRUM_HOP_SIZE || this._spectrumCooldown > 0) return;
		this._pendingSamples = 0;
		this._spectrumCooldown = SPECTRUM_COOLDOWN_S;
		this._computeSpectrum();
	}

	private _computeSpectrum(): void {
		const headLength = FFT_SIZE - this._ringWrite;
		for (let i = 0; i < headLength; i += 1) {
			this._real[i] = this._ring[this._ringWrite + i] * this._window[i];
			this._imag[i] = 0;
		}
		for (let i = 0; i < this._ringWrite; i += 1) {
			const j = headLength + i;
			this._real[j] = this._ring[i] * this._window[j];
			this._imag[j] = 0;
		}
		this._fft(this._real, this._imag);
		const norm = 1 / FFT_SIZE;
		for (let i = 0; i < FFT_HALF; i += 1) {
			this._mags[i] = Math.hypot(this._real[i], this._imag[i]) * norm;
		}
		this._rawLow = this._agc(this._bandRms(20, LOW_MID_SPLIT_HZ), 'Low');
		this._rawMid = this._agc(this._bandRms(LOW_MID_SPLIT_HZ, MID_HIGH_SPLIT_HZ), 'Mid');
		this._rawHigh = this._agc(this._bandRms(MID_HIGH_SPLIT_HZ, this._sampleRate * 0.5), 'High');
	}

	private _fft(real: Float32Array, imag: Float32Array): void {
		for (let i = 0; i < FFT_SIZE; i += 1) {
			const j = this._bitReverse[i];
			if (j <= i) continue;
			const tr = real[i];
			const ti = imag[i];
			real[i] = real[j];
			imag[i] = imag[j];
			real[j] = tr;
			imag[j] = ti;
		}
		for (let size = 2; size <= FFT_SIZE; size <<= 1) {
			const half = size >> 1;
			const angle = (-2 * Math.PI) / size;
			const stepR = Math.cos(angle);
			const stepI = Math.sin(angle);
			for (let start = 0; start < FFT_SIZE; start += size) {
				let wr = 1;
				let wi = 0;
				for (let offset = 0; offset < half; offset += 1) {
					const even = start + offset;
					const odd = even + half;
					const tr = wr * real[odd] - wi * imag[odd];
					const ti = wr * imag[odd] + wi * real[odd];
					real[odd] = real[even] - tr;
					imag[odd] = imag[even] - ti;
					real[even] += tr;
					imag[even] += ti;
					const nextWr = wr * stepR - wi * stepI;
					wi = wr * stepI + wi * stepR;
					wr = nextWr;
				}
			}
		}
	}

	private _bandRms(lowHz: number, highHz: number): number {
		const binHz = this._sampleRate / FFT_SIZE;
		const start = Math.max(1, Math.floor(lowHz / binHz));
		const end = Math.min(this._mags.length - 1, Math.ceil(highHz / binHz));
		if (end <= start) return 0;
		let sum = 0;
		for (let i = start; i <= end; i += 1) {
			sum += this._mags[i] * this._mags[i];
		}
		return Math.sqrt(sum / (end - start + 1));
	}

	private _agc(raw: number, band: 'Low' | 'Mid' | 'High'): number {
		const key = `_peak${band}` as '_peakLow' | '_peakMid' | '_peakHigh';
		this[key] = Math.max(raw, Math.max(PEAK_FLOOR, this[key] * PEAK_DECAY));
		return clamp01(Math.pow(raw / this[key], 0.7));
	}
}
