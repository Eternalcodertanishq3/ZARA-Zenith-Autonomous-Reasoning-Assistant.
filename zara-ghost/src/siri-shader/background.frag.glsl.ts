export const BACKGROUND_FRAGMENT_SHADER = `#version 300 es
precision highp float;

uniform vec2 uResolution;
uniform sampler2D uBackground;
uniform vec2 uTextureSize;
uniform vec2 uCanvasSize;
uniform float uBackgroundReady;

out vec4 outColor;

vec2 coverUv(vec2 screenUv, vec2 screenSize, vec2 texSize) {
    float screenAspect = screenSize.x / screenSize.y;
    float texAspect = texSize.x / texSize.y;
    vec2 scale = screenAspect > texAspect
        ? vec2(1.0, texAspect / screenAspect)
        : vec2(screenAspect / texAspect, 1.0);
    return (screenUv - 0.5) * scale + 0.5;
}

vec4 fallbackBackground(vec2 uv) {
    // Completely transparent fallback background — lets desktop background show through
    return vec4(0.0);
}

void main() {
    vec2 pixel = vec2(gl_FragCoord.x, uResolution.y - gl_FragCoord.y);
    vec2 uv = pixel / uCanvasSize;
    vec4 image = texture(uBackground, coverUv(uv, uCanvasSize, uTextureSize));
    vec4 background = mix(fallbackBackground(uv), image, clamp(uBackgroundReady, 0.0, 1.0));
    outColor = background;
}
`;
