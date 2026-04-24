import { describe, expect, test } from 'vitest';

import { getWebSearchMode } from './webSearchPreference';

describe('web search preference', () => {
	test('defaults to always when preference is missing', () => {
		expect(getWebSearchMode({})).toBe('always');
	});

	test('respects explicit default mode', () => {
		expect(getWebSearchMode({ webSearch: null })).toBe(null);
	});

	test('respects explicit always mode', () => {
		expect(getWebSearchMode({ webSearch: 'always' })).toBe('always');
	});
});
