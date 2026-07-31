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

vec3 fallbackBackground(vec2 uv) {
    float vignette = smoothstep(0.95, 0.12, distance(uv, vec2(0.5)));
    // Richer gradient with subtle color shifts for better refraction visibility
    vec3 top = vec3(0.06, 0.07, 0.10);
    vec3 bottom = vec3(0.02, 0.015, 0.03);
    vec3 tint = mix(bottom, top, 1.0 - uv.y);
    // Subtle warm/cool color bands
    float band = sin(uv.y * 6.28318) * 0.02;
    tint += vec3(band * 0.5, band * 0.3, band * 0.8);
    return tint + vec3(0.04, 0.06, 0.09) * vignette;
}

void main() {
    vec2 pixel = vec2(gl_FragCoord.x, uResolution.y - gl_FragCoord.y);
    vec2 uv = pixel / uCanvasSize;
    vec3 image = texture(uBackground, coverUv(uv, uCanvasSize, uTextureSize)).rgb;
    vec3 background = mix(fallbackBackground(uv), image, clamp(uBackgroundReady, 0.0, 1.0));
    outColor = vec4(background, 1.0);
}
`;
