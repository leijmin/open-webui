import { describe, expect, test } from 'vitest';

import { getLoaderVisibilityState } from './loaderVisibility';

describe('loader visibility dispatch', () => {
	test('dispatches only when entering the viewport', () => {
		expect(getLoaderVisibilityState(false, true)).toEqual({
			isVisible: true,
			shouldDispatch: true
		});

		expect(getLoaderVisibilityState(true, true)).toEqual({
			isVisible: true,
			shouldDispatch: false
		});
	});

	test('resets after leaving the viewport', () => {
		expect(getLoaderVisibilityState(true, false)).toEqual({
			isVisible: false,
			shouldDispatch: false
		});
	});
});
