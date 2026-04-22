import { describe, expect, test } from 'vitest';

import {
	formatCodeExecutionResult,
	shouldAutoExpandCodeInterpreterDetails,
	shouldCollapseCodeBlockByDefault,
	shouldShowCodeExecutionOutput
} from './codeExecutionDisplay';

describe('code execution display rules', () => {
	test('code interpreter details are expanded by default', () => {
		expect(shouldAutoExpandCodeInterpreterDetails(false, { type: 'code_interpreter' })).toBe(
			true
		);
		expect(shouldAutoExpandCodeInterpreterDetails(false, { type: 'reasoning' })).toBe(false);
	});

	test('code interpreter code blocks ignore always-collapse defaults', () => {
		expect(shouldCollapseCodeBlockByDefault(true, { type: 'code_interpreter' })).toBe(false);
		expect(shouldCollapseCodeBlockByDefault(true, { type: 'reasoning' })).toBe(true);
	});

	test('collapsed code interpreter blocks still show execution output', () => {
		expect(
			shouldShowCodeExecutionOutput({
				collapsed: true,
				attributes: { type: 'code_interpreter' },
				result: '营销方案正文'
			})
		).toBe(true);

		expect(
			shouldShowCodeExecutionOutput({
				collapsed: true,
				attributes: { type: 'reasoning' },
				result: '不应该展示'
			})
		).toBe(false);
	});

	test('string results keep original text instead of JSON quoted text', () => {
		expect(formatCodeExecutionResult('第一行\n第二行')).toBe('第一行\n第二行');
		expect(formatCodeExecutionResult({ title: '胡椒文旅' })).toBe(
			'{\n  "title": "胡椒文旅"\n}'
		);
	});
});
