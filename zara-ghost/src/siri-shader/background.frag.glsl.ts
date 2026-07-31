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
    // Atmospheric sky & horizon gradient
    vec3 skyTop = vec3(0.08, 0.28, 0.55);      // Deep azure blue
    vec3 skyMid = vec3(0.42, 0.65, 0.88);      // Soft sky blue
    vec3 horizonGlow = vec3(0.95, 0.82, 0.62); // Golden sun horizon
    vec3 groundVal = vec3(0.12, 0.42, 0.25);   // Lush green hills

    // Smooth sky gradient
    vec3 sky = mix(horizonGlow, skyMid, smoothstep(0.35, 0.65, uv.y));
    sky = mix(sky, skyTop, smoothstep(0.65, 1.0, uv.y));

    // Landscape hill horizon below y = 0.38
    float hillShape = 0.32 + 0.05 * sin(uv.x * 12.0) + 0.03 * cos(uv.x * 24.0);
    float hillMask = smoothstep(hillShape + 0.02, hillShape - 0.01, uv.y);
    vec3 landscape = mix(sky, groundVal, hillMask);

    // Soft volumetric cloud bands
    float cloud1 = smoothstep(0.4, 0.6, sin(uv.x * 8.0 + uv.y * 14.0) * 0.5 + 0.5);
    float cloud2 = smoothstep(0.3, 0.7, cos(uv.x * 15.0 - uv.y * 6.0) * 0.5 + 0.5);
    float cloudMask = cloud1 * cloud2 * (1.0 - hillMask) * smoothstep(0.35, 0.8, uv.y);
    vec3 withClouds = mix(landscape, vec3(0.96, 0.98, 1.0), cloudMask * 0.55);

    // Subtle sun flare in upper-left / horizon
    float sun = smoothstep(0.45, 0.0, distance(uv, vec2(0.3, 0.55)));
    withClouds += vec3(0.35, 0.25, 0.12) * sun;

    return withClouds;
}

void main() {
    vec2 pixel = vec2(gl_FragCoord.x, uResolution.y - gl_FragCoord.y);
    vec2 uv = pixel / uCanvasSize;
    vec3 image = texture(uBackground, coverUv(uv, uCanvasSize, uTextureSize)).rgb;
    vec3 background = mix(fallbackBackground(uv), image, clamp(uBackgroundReady, 0.0, 1.0));
    outColor = vec4(background, 1.0);
}
`;
