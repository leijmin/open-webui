import { describe, expect, test } from 'vitest';

import { isImageGenerationOnlyModel } from './modelCapabilities';

describe('model capability helpers', () => {
	test('detects image-only models from supported endpoint metadata', () => {
		expect(
			isImageGenerationOnlyModel({
				model_type: '图像',
				supported_endpoint_types: ['openai编辑图片', 'image-generation']
			})
		).toBe(true);
	});

	test('does not auto-treat chat models as image-only', () => {
		expect(
			isImageGenerationOnlyModel({
				model_type: 'chat',
				supported_endpoint_types: ['chat-completions']
			})
		).toBe(false);
	});

	test('does not auto-enable mixed-capability multimodal models', () => {
		expect(
			isImageGenerationOnlyModel({
				model_type: 'multimodal',
				supported_endpoint_types: ['image-generation', 'responses']
			})
		).toBe(false);
	});
});
