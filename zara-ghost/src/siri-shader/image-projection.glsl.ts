export const COVER_UV_GLSL = `
vec2 coverUv(vec2 canvasUv, vec2 canvasSize, vec2 textureSize) {
	vec2 pixel = canvasUv * canvasSize;
	float scale = max(canvasSize.x / textureSize.x, canvasSize.y / textureSize.y);
	vec2 fitted = textureSize * scale;
	vec2 offset = (fitted - canvasSize) * 0.5;
	return (pixel + offset) / fitted;
}
`;
