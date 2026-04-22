type ProviderModelShape = {
	supported_endpoint_types?: string[];
	model_type?: string | null;
};

type ModelCapabilityShape = ProviderModelShape & {
	openai?: ProviderModelShape;
};

const normalizeValue = (value: string | null | undefined) => (value ?? '').trim().toLowerCase();

const getSupportedEndpointTypes = (model?: ModelCapabilityShape | null) =>
	[
		...(model?.supported_endpoint_types ?? []),
		...(model?.openai?.supported_endpoint_types ?? [])
	].map(normalizeValue);

const getModelType = (model?: ModelCapabilityShape | null) =>
	normalizeValue(model?.model_type ?? model?.openai?.model_type);

const isImageEndpointType = (endpointType: string) =>
	endpointType.includes('image') || endpointType.includes('图像');

const isVideoEndpointType = (endpointType: string) =>
	endpointType.includes('video') || endpointType.includes('视频');

const isTextGenerationEndpointType = (endpointType: string) =>
	['chat', 'response', 'completion', 'text-generation', 'text'].some((marker) =>
		endpointType.includes(marker)
	);

export const isImageGenerationOnlyModel = (model?: ModelCapabilityShape | null) => {
	const supportedEndpointTypes = getSupportedEndpointTypes(model);
	const modelType = getModelType(model);

	const supportsImageGeneration =
		supportedEndpointTypes.some(isImageEndpointType) ||
		modelType.includes('image') ||
		modelType.includes('图像');
	const supportsTextGeneration = supportedEndpointTypes.some(isTextGenerationEndpointType);

	return supportsImageGeneration && !supportsTextGeneration;
};

export const isVideoGenerationOnlyModel = (model?: ModelCapabilityShape | null) => {
	const supportedEndpointTypes = getSupportedEndpointTypes(model);
	const modelType = getModelType(model);

	const supportsVideoGeneration =
		supportedEndpointTypes.some(isVideoEndpointType) ||
		modelType.includes('video') ||
		modelType.includes('视频') ||
		modelType.includes('音视频');
	const supportsTextGeneration = supportedEndpointTypes.some(isTextGenerationEndpointType);

	return supportsVideoGeneration && !supportsTextGeneration;
};
